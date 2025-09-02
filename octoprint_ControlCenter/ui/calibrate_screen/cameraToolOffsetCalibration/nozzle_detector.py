"""
Enhanced Nozzle Detection System
================================

Based on kTAMV's multi-algorithm approach for robust nozzle detection.
Uses 5 different detector/preprocessor combinations with progressive fallback.

Features:
- Multiple blob detection algorithms (standard, relaxed, super-relaxed)
- Different image preprocessing methods (YUV, grayscale, median blur)
- Consistency validation (3 consecutive matches)
- Visual feedback with detection overlays
- Closest-to-center selection when multiple blobs found
"""

import cv2
import numpy as np
import time
import copy
from typing import Tuple, Optional, List, Dict, Any
from utils.logger import get_logger


class NozzleDetector:
    """
    Multi-algorithm nozzle detection system with progressive fallback.
    """
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing NozzleDetector with kTAMV algorithms")
        
        # Frame dimensions (kTAMV standard)
        self.frame_width = 640
        self.frame_height = 480
        self.frame_center = (320, 240)
        
        # Detection algorithm tracking
        self.last_successful_algorithm = None
        
        # Create blob detectors with different sensitivity levels
        self.detectors = self._create_blob_detectors()
        
        # Only proceed if detectors were created successfully
        if not self.detectors:
            self.logger.error("Failed to create blob detectors - OpenCV compatibility issue")
            # Use simplified detection methods as fallback
            self.use_simple_detection = True
            self.algorithms = [("simple", "grayscale", (255, 0, 0))]
        else:
            self.use_simple_detection = False
            # Define algorithm combinations (detector + preprocessor)
            self.algorithms = [
                ("standard", "yuv", (0, 0, 255)),      # Red for standard + YUV
                ("standard", "grayscale", (0, 255, 0)), # Green for standard + grayscale
                ("relaxed", "yuv", (255, 0, 0)),       # Blue for relaxed + YUV
                ("relaxed", "grayscale", (39, 127, 255)), # Orange for relaxed + grayscale
                ("super_relaxed", "median", (39, 255, 127)) # Light green for super-relaxed + median
            ]
        
        self.logger.info(f"Created {len(self.algorithms)} detection algorithms")
    
    def _create_blob_detectors(self) -> Dict[str, Any]:
        """Create three blob detectors with different sensitivity levels."""
        detectors = {}
        
        # Check OpenCV version and use appropriate method
        try:
            # Try the newer method first (OpenCV 3.x+)
            params_class = cv2.SimpleBlobDetector_Params
            create_method = cv2.SimpleBlobDetector_create
        except AttributeError:
            # Fallback for older OpenCV versions (2.x)
            try:
                params_class = cv2.SimpleBlobDetector.Params
                create_method = cv2.SimpleBlobDetector
            except AttributeError:
                self.logger.error("SimpleBlobDetector not available in this OpenCV version")
                return {}
        
        # Standard Parameters (most restrictive)
        standard_params = params_class()
        standard_params.minThreshold = 1
        standard_params.maxThreshold = 50
        standard_params.thresholdStep = 1
        
        # Area filtering
        standard_params.filterByArea = True
        standard_params.minArea = 400
        standard_params.maxArea = 900
        
        # Circularity filtering (most important for nozzle detection)
        standard_params.filterByCircularity = True
        standard_params.minCircularity = 0.8
        standard_params.maxCircularity = 1.0
        
        # Convexity filtering
        standard_params.filterByConvexity = True
        standard_params.minConvexity = 0.3
        standard_params.maxConvexity = 1.0
        
        # Inertia filtering
        standard_params.filterByInertia = True
        standard_params.minInertiaRatio = 0.3
        
        detectors["standard"] = create_method(standard_params)
        
        # Relaxed Parameters (medium sensitivity)
        relaxed_params = params_class()
        relaxed_params.minThreshold = 1
        relaxed_params.maxThreshold = 50
        relaxed_params.thresholdStep = 1
        
        # Area filtering (larger range)
        relaxed_params.filterByArea = True
        relaxed_params.minArea = 600
        relaxed_params.maxArea = 15000
        
        # Circularity filtering (more permissive)
        relaxed_params.filterByCircularity = True
        relaxed_params.minCircularity = 0.6
        relaxed_params.maxCircularity = 1.0
        
        # Convexity filtering (more permissive)
        relaxed_params.filterByConvexity = True
        relaxed_params.minConvexity = 0.1
        relaxed_params.maxConvexity = 1.0
        
        # Inertia filtering (more permissive)
        relaxed_params.filterByInertia = True
        relaxed_params.minInertiaRatio = 0.3
        
        detectors["relaxed"] = create_method(relaxed_params)
        
        # Super-Relaxed Parameters (most permissive)
        super_relaxed_params = params_class()
        super_relaxed_params.minThreshold = 20
        super_relaxed_params.maxThreshold = 200
        
        # Area filtering (very permissive)
        super_relaxed_params.filterByArea = True
        super_relaxed_params.minArea = 200
        
        # All other filters set to very permissive values
        super_relaxed_params.filterByCircularity = True
        super_relaxed_params.minCircularity = 0.5
        
        super_relaxed_params.filterByConvexity = True
        super_relaxed_params.minConvexity = 0.5
        
        super_relaxed_params.filterByInertia = True
        super_relaxed_params.minInertiaRatio = 0.5
        
        super_relaxed_params.filterByColor = False
        super_relaxed_params.minDistBetweenBlobs = 2
        
        detectors["super_relaxed"] = create_method(super_relaxed_params)
        
        self.logger.info("Created standard, relaxed, and super-relaxed blob detectors")
        return detectors
    
    def _preprocess_yuv(self, frame: np.ndarray) -> np.ndarray:
        """
        YUV color space preprocessing with adaptive threshold.
        Best for detecting dark circular features like nozzle openings.
        """
        try:
            # Gamma correction
            adjusted = self._adjust_gamma(frame, gamma=1.2)
            
            # Convert to YUV color space
            yuv = cv2.cvtColor(adjusted, cv2.COLOR_BGR2YUV)
            yuv_planes = cv2.split(yuv)
            
            # Process Y (luminance) channel
            y_channel = cv2.GaussianBlur(yuv_planes[0], (7, 7), 6)
            y_channel = cv2.adaptiveThreshold(
                y_channel, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 1
            )
            
            # Convert back to BGR for blob detection
            result = cv2.cvtColor(y_channel, cv2.COLOR_GRAY2BGR)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in YUV preprocessing: {e}")
            return frame
    
    def _preprocess_grayscale(self, frame: np.ndarray) -> np.ndarray:
        """
        Grayscale preprocessing with triangle threshold.
        Good for high contrast nozzle detection.
        """
        try:
            # Gamma correction
            adjusted = self._adjust_gamma(frame, gamma=1.2)
            
            # Convert to grayscale
            gray = cv2.cvtColor(adjusted, cv2.COLOR_BGR2GRAY)
            
            # Triangle threshold for automatic threshold selection
            threshold_val, binary = cv2.threshold(
                gray, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_TRIANGLE
            )
            
            # Gaussian blur to smooth edges
            blurred = cv2.GaussianBlur(binary, (7, 7), 6)
            
            # Convert back to BGR
            result = cv2.cvtColor(blurred, cv2.COLOR_GRAY2BGR)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in grayscale preprocessing: {e}")
            return frame
    
    def _preprocess_median(self, frame: np.ndarray) -> np.ndarray:
        """
        Median blur preprocessing for noise reduction.
        Good for noisy environments.
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Median blur to reduce noise
            result = cv2.medianBlur(gray, 5)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in median preprocessing: {e}")
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    def _adjust_gamma(self, image: np.ndarray, gamma: float = 1.2) -> np.ndarray:
        """Apply gamma correction to improve contrast."""
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table)
    
    def _find_closest_keypoint(self, keypoints: List, center: Tuple[int, int] = None) -> int:
        """Find the keypoint closest to the center of the frame."""
        if not keypoints:
            return -1
        
        if center is None:
            center = self.frame_center
        
        closest_index = 0
        closest_distance = float('inf')
        target_point = np.array(center)
        
        for i, keypoint in enumerate(keypoints):
            point = np.array(keypoint.pt)
            distance = np.linalg.norm(point - target_point)
            
            if distance < closest_distance:
                closest_distance = distance
                closest_index = i
        
        return closest_index
    
    def detect_nozzle(self, frame: np.ndarray) -> Tuple[Optional[Tuple[int, int]], np.ndarray, Optional[str]]:
        """
        Detect nozzle in frame using multiple algorithms with progressive fallback.
        
        Returns:
            - center: (x, y) coordinates of detected nozzle center, or None if not found
            - annotated_frame: Frame with detection overlays
            - algorithm_used: String identifier of successful algorithm, or None
        """
        if frame is None:
            self.logger.warning("Received None frame for detection")
            return None, frame, None
        
        # Resize frame to standard dimensions
        frame = cv2.resize(frame, (self.frame_width, self.frame_height))
        annotated_frame = copy.deepcopy(frame)
        
        # Draw crosshairs first (will be overlaid by detection circle if found)
        self._draw_crosshairs(annotated_frame)
        
        # Try last successful algorithm first (if any)
        if self.last_successful_algorithm is not None:
            try:
                result = self._try_algorithm(frame, self.last_successful_algorithm)
                if result[0] is not None:
                    center, algorithm_name = result
                    self._draw_detection(annotated_frame, center, self.algorithms[self.last_successful_algorithm][2])
                    self.logger.debug(f"Detection successful with last algorithm: {algorithm_name}")
                    return center, annotated_frame, algorithm_name
            except Exception as e:
                self.logger.warning(f"Last successful algorithm failed: {e}")
                self.last_successful_algorithm = None
        
        # Try all algorithms in order
        for i, (detector_name, preprocessor_name, color) in enumerate(self.algorithms):
            try:
                result = self._try_algorithm(frame, i)
                if result[0] is not None:
                    center, algorithm_name = result
                    self.last_successful_algorithm = i
                    self._draw_detection(annotated_frame, center, color)
                    self.logger.info(f"Nozzle detected with algorithm {i+1}: {algorithm_name}")
                    return center, annotated_frame, algorithm_name
                    
            except Exception as e:
                self.logger.warning(f"Algorithm {i+1} ({detector_name}+{preprocessor_name}) failed: {e}")
                continue
        
        # No detection found - draw error indicator
        self._draw_no_detection(annotated_frame)
        self.logger.debug("No nozzle detected with any algorithm")
        return None, annotated_frame, None
    
    def _try_algorithm(self, frame: np.ndarray, algorithm_index: int) -> Tuple[Optional[Tuple[int, int]], str]:
        """Try a specific detection algorithm."""
        if self.use_simple_detection:
            return self._simple_detection(frame)
        
        detector_name, preprocessor_name, _ = self.algorithms[algorithm_index]
        
        # Get detector
        detector = self.detectors[detector_name]
        
        # Preprocess frame
        if preprocessor_name == "yuv":
            processed_frame = self._preprocess_yuv(frame)
        elif preprocessor_name == "grayscale":
            processed_frame = self._preprocess_grayscale(frame)
        elif preprocessor_name == "median":
            processed_frame = self._preprocess_median(frame)
        else:
            processed_frame = frame
        
        # Detect keypoints
        keypoints = detector.detect(processed_frame)
        
        if not keypoints:
            return None, f"{detector_name}+{preprocessor_name}"
        
        # If multiple keypoints, use the one closest to center
        if len(keypoints) > 1:
            closest_index = self._find_closest_keypoint(keypoints)
            chosen_keypoint = keypoints[closest_index]
            self.logger.debug(f"Multiple keypoints found ({len(keypoints)}), using closest to center")
        else:
            chosen_keypoint = keypoints[0]
        
        # Extract center coordinates
        x, y = np.around(chosen_keypoint.pt)
        center = (int(x), int(y))
        
        algorithm_name = f"{detector_name}+{preprocessor_name}"
        self.logger.debug(f"Algorithm {algorithm_name} detected nozzle at {center}")
        
        return center, algorithm_name
    
    def _simple_detection(self, frame: np.ndarray) -> Tuple[Optional[Tuple[int, int]], str]:
        """Simple detection method for OpenCV compatibility fallback."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (9, 9), 2)
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None, "simple+grayscale"
            
            # Filter contours by area and circularity
            candidates = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if 200 < area < 2000:  # Reasonable nozzle size range
                    # Check circularity
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter * perimeter)
                        if circularity > 0.5:  # Reasonably circular
                            # Get center
                            M = cv2.moments(contour)
                            if M["m00"] != 0:
                                cx = int(M["m10"] / M["m00"])
                                cy = int(M["m01"] / M["m00"])
                                candidates.append((cx, cy, area))
            
            if not candidates:
                return None, "simple+grayscale"
            
            # Choose the candidate closest to frame center
            center_x, center_y = self.frame_center
            best_candidate = min(candidates, 
                                key=lambda c: (c[0] - center_x)**2 + (c[1] - center_y)**2)
            
            return (best_candidate[0], best_candidate[1]), "simple+grayscale"
            
        except Exception as e:
            self.logger.error(f"Simple detection failed: {e}")
            return None, "simple+grayscale"
    
    def _draw_crosshairs(self, frame: np.ndarray):
        """Draw crosshairs at the center of the frame."""
        center_x, center_y = self.frame_center
        
        # Black outline
        cv2.line(frame, (center_x, 0), (center_x, self.frame_height), (0, 0, 0), 2)
        cv2.line(frame, (0, center_y), (self.frame_width, center_y), (0, 0, 0), 2)
        
        # White center lines
        cv2.line(frame, (center_x, 0), (center_x, self.frame_height), (255, 255, 255), 1)
        cv2.line(frame, (0, center_y), (self.frame_width, center_y), (255, 255, 255), 1)
    
    def _draw_detection(self, frame: np.ndarray, center: Tuple[int, int], color: Tuple[int, int, int]):
        """Draw detection circle and crosshair at detected position."""
        x, y = center
        
        # Detection circle (filled with transparency effect)
        radius = 17
        circle_frame = cv2.circle(frame.copy(), center, radius, color, -1, cv2.LINE_AA)
        cv2.addWeighted(circle_frame, 0.4, frame, 0.6, 0, frame)
        
        # Circle outline
        cv2.circle(frame, center, radius, (0, 0, 0), 1, cv2.LINE_AA)
        
        # Crosshair at detection point
        cv2.line(frame, (x-5, y), (x+5, y), (255, 255, 255), 2)
        cv2.line(frame, (x, y-5), (x, y+5), (255, 255, 255), 2)
    
    def _draw_no_detection(self, frame: np.ndarray):
        """Draw error indicator when no nozzle is detected."""
        center_x, center_y = self.frame_center
        radius = 17
        
        # Red circle outline
        cv2.circle(frame, (center_x, center_y), radius, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.circle(frame, (center_x, center_y), radius+1, (0, 0, 255), 1, cv2.LINE_AA)
    
    def detect_with_consistency(self, camera_thread, min_matches: int = 3, timeout: float = 20.0, 
                              tolerance: int = 1) -> Tuple[Optional[Tuple[int, int]], str]:
        """
        Detect nozzle with consistency validation - requires multiple consecutive matching detections.
        
        Args:
            camera_thread: Camera thread to get frames from
            min_matches: Number of consecutive matching detections required
            timeout: Maximum time to spend detecting (seconds)
            tolerance: Pixel tolerance for position matching
            
        Returns:
            - center: Final detected center position, or None if failed
            - algorithm_used: Algorithm that succeeded, or error message
        """
        self.logger.info(f"Starting consistency detection: {min_matches} matches, {timeout}s timeout, {tolerance}px tolerance")
        
        start_time = time.time()
        last_position = (0, 0)
        position_matches = 0
        final_position = None
        successful_algorithm = None
        
        while time.time() - start_time < timeout:
            # Get current frame from camera thread
            try:
                frame = camera_thread.get_current_frame()  # This method needs to be added to camera thread
                if frame is None:
                    time.sleep(0.1)
                    continue
            except Exception as e:
                self.logger.error(f"Error getting frame from camera thread: {e}")
                time.sleep(0.1)
                continue
            
            # Detect nozzle in frame
            center, annotated_frame, algorithm = self.detect_nozzle(frame)
            
            # Update camera thread with annotated frame for display
            try:
                camera_thread.update_display_frame(annotated_frame)
            except Exception as e:
                self.logger.warning(f"Could not update display frame: {e}")
            
            if center is None:
                position_matches = 0
                time.sleep(0.3)  # Wait before next attempt
                continue
            
            # Check if position matches last detection within tolerance
            if (abs(center[0] - last_position[0]) <= tolerance and 
                abs(center[1] - last_position[1]) <= tolerance):
                position_matches += 1
                self.logger.debug(f"Position match {position_matches}/{min_matches} at {center}")
                
                if position_matches >= min_matches:
                    final_position = center
                    successful_algorithm = algorithm
                    self.logger.info(f"Consistency detection successful: {final_position} with {algorithm}")
                    break
            else:
                if position_matches > 0:
                    self.logger.debug(f"Position changed from {last_position} to {center}, resetting matches")
                position_matches = 1  # Reset but count this detection
                successful_algorithm = algorithm
            
            last_position = center
            time.sleep(0.3)  # Control detection rate (kTAMV uses 0.3s intervals)
        
        elapsed = time.time() - start_time
        if final_position is None:
            error_msg = f"Consistency detection failed after {elapsed:.1f}s"
            self.logger.warning(error_msg)
            return None, error_msg
        else:
            self.logger.info(f"Consistency detection completed in {elapsed:.1f}s")
            return final_position, successful_algorithm


class DetectionResult:
    """Container for detection results with metadata."""
    
    def __init__(self, center: Optional[Tuple[int, int]], algorithm: Optional[str], 
                 confidence: float = 0.0, timestamp: float = None):
        self.center = center
        self.algorithm = algorithm
        self.confidence = confidence
        self.timestamp = timestamp or time.time()
        self.success = center is not None
    
    def __str__(self):
        if self.success:
            return f"Detection at {self.center} using {self.algorithm} (confidence: {self.confidence:.2f})"
        else:
            return "Detection failed"
