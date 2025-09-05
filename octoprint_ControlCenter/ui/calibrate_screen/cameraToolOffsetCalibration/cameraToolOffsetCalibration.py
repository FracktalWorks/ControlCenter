"""
Camera Tool Offset Calibration
==============================

Simplified user-guided tool offset calibration using manual positioning.

Workflow:
1. Clean Nozzles - Heat and present both nozzles for cleaning
2. Connect Camera - Position for camera and request connection 
3. Position T0 - Course and fine positioning of T0 nozzle center
4. Position T1 - Course and fine positioning of T1 nozzle center  
5. Results - Calculate and apply tool offsets

No automatic detection - relies on user manual positioning.
"""

import os
import sys
import time
import subprocess

# Dynamic OpenCV import with automatic installation
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("OpenCV not found. Attempting to install...")
    
    try:
        # For Raspberry Pi - use prebuilt package to avoid long compilation
        print("Installing OpenCV using apt (prebuilt package)...")
        subprocess.check_call(['sudo', 'apt', 'update'])
        subprocess.check_call(['sudo', 'apt', 'install', '-y', 'python3-opencv'])
        import cv2
        OPENCV_AVAILABLE = True
        print("✓ OpenCV installed successfully from apt!")
    except subprocess.CalledProcessError:
        # Fallback to pip if apt fails
        try:
            print("Apt installation failed, trying pip as fallback...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'opencv-python'])
            import cv2
            OPENCV_AVAILABLE = True
            print("✓ OpenCV installed successfully with pip!")
        except subprocess.CalledProcessError:
            # Final fallback with sudo pip
            try:
                subprocess.check_call(['sudo', 'pip3', 'install', 'opencv-python'])
                import cv2
                OPENCV_AVAILABLE = True
                print("✓ OpenCV installed successfully with sudo pip!")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Failed to automatically install OpenCV: {e}")
                print("Please install it manually with: sudo apt install python3-opencv or pip install opencv-python")
                OPENCV_AVAILABLE = False

from PyQt5 import uic, QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel, QMessageBox, QProgressDialog
import time
import traceback

# Additional PyQt5 imports for loading dialog
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, QMutex, QWaitCondition
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt

from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils import dialog


class CameraSystem(QThread):
    """Unified camera management system combining detection, thread management, and UI feedback."""
    
    # Signals for camera events
    camera_found = pyqtSignal(int)      # Emits camera index when found
    camera_failed = pyqtSignal()        # Emits when camera initialization fails
    frame_ready = pyqtSignal(QImage)    # Emits processed camera frames
    connection_error = pyqtSignal(str)  # Emits connection errors
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(self.__class__.__name__)
        self.camera_thread = None
        self.available_indices = []
        self.should_stop = False
        self.zoom_factor = 1.0
        self.detection_mode = False  # True when running camera detection
        
    def find_working_camera(self):
        """Find working camera using unified detection logic with enhanced V4L2 support."""
        if not OPENCV_AVAILABLE:
            print("ERROR: OpenCV not available")
            return None
            
        try:
            import cv2
            import time
            
            print("Starting camera detection...")
            
            # Test camera indices in order of preference
            test_indices = [1, 0, 2, 3]  # USB cameras typically at index 1
            
            for index in test_indices:
                print(f"Testing camera at index {index}...")
                if self._test_camera_at_index(index):
                    print(f"SUCCESS: Found working camera at index {index}")
                    return index
                else:
                    print(f"Camera at index {index} not working")
                    
            print("WARNING: No working camera found after testing all indices")
            return None
            
        except Exception as e:
            print(f"ERROR: Camera detection failed: {e}")
            return None
    
    def _test_camera_at_index(self, index):
        """Test if camera at given index is working with enhanced V4L2 support."""
        try:
            import cv2
            import time
            
            print(f"  Testing camera at index {index}...")
            
            # For V4L2 cameras, try CAP_V4L2 backend if available, otherwise use default
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
                print(f"  Using V4L2 backend for camera {index}")
            except (AttributeError, Exception):
                cap = cv2.VideoCapture(index)
                print(f"  Using default backend for camera {index}")
            
            # Give V4L2 cameras more time to initialize
            time.sleep(0.3)
            
            # Don't rely on cap.isOpened() for V4L2 cameras - it's unreliable
            success_count = 0
            valid_frames = 0
            
            # Try multiple frame reads for stability with longer timeouts
            for attempt in range(5):  # Increased attempts for V4L2
                try:
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Check if frame has valid data
                        if hasattr(frame, 'shape') and len(frame.shape) >= 2:
                            height, width = frame.shape[:2]
                            if height > 0 and width > 0 and frame.size > 0:
                                valid_frames += 1
                                print(f"  Camera {index} valid frame {valid_frames}: {width}x{height}")
                                
                                # If we get even 1 valid frame, camera is working
                                if valid_frames >= 1:
                                    success_count = valid_frames
                                    break
                except Exception as e:
                    print(f"  Camera {index} read attempt {attempt + 1} failed: {e}")
                
                time.sleep(0.2)  # Longer delay for V4L2 cameras
            
            # Cleanup
            try:
                cap.release()
            except Exception as e:
                print(f"  Warning: Error releasing camera {index}: {e}")
            
            time.sleep(0.3)  # Allow camera to be released properly
            
            if success_count > 0:
                print(f"  SUCCESS: Camera {index} is working ({success_count} valid frames)")
                return True
            else:
                print(f"  FAILED: Camera {index} - no valid frames captured")
                return False
                
        except Exception as e:
            print(f"  ERROR: Camera {index} test exception: {e}")
            try:
                if 'cap' in locals():
                    cap.release()
            except:
                pass
            return False
    
    def start_camera_detection(self):
        """Start background camera detection."""
        if self.isRunning():
            return
        
        self.detection_mode = True
        self.should_stop = False
        self.start()
    
    def start_camera_feed(self, camera_index):
        """Start camera feed with given index."""
        try:
            # Stop any existing camera
            self.stop_camera()
            
            # Create new camera thread
            self.camera_thread = CameraThread(camera_index)
            self.camera_thread.changePixmap.connect(self.frame_ready.emit)
            self.camera_thread.connectionError.connect(self.connection_error.emit)
            self.camera_thread.start()
            
            self.logger.info(f"Camera feed started on index {camera_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start camera feed: {e}")
            self.connection_error.emit(f"Failed to start camera feed: {e}")
            return False
    
    def set_zoom(self, factor):
        """Set zoom factor for camera feed."""
        self.zoom_factor = factor
        if self.camera_thread:
            self.camera_thread.set_zoom(factor)
    
    def stop_camera(self):
        """Stop camera thread safely."""
        try:
            if self.camera_thread and self.camera_thread.isRunning():
                # Disconnect signals first to prevent crashes during shutdown
                try:
                    self.camera_thread.changePixmap.disconnect()
                    self.camera_thread.connectionError.disconnect()
                except TypeError:
                    # Signals already disconnected
                    pass
                
                # Stop the thread
                self.camera_thread.stop()
                
                # Wait for thread to finish, then delete
                if not self.camera_thread.wait(3000):  # 3 second timeout
                    self.logger.warning("Camera thread did not stop cleanly, terminating")
                    self.camera_thread.terminate()
                    self.camera_thread.wait(1000)
                
                # Clean up thread reference
                self.camera_thread = None
                self.logger.info("Camera stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping camera: {e}")
            # Force cleanup even if there was an error
            self.camera_thread = None
    
    def stop_detection(self):
        """Stop camera detection."""
        self.should_stop = True
        if self.detection_mode and self.isRunning():
            self.wait(1000)
    
    def run(self):
        """Background camera detection thread."""
        if not self.detection_mode:
            return
            
        try:
            if not OPENCV_AVAILABLE:
                self.camera_failed.emit()
                return
            
            import time
            
            # Find working camera
            camera_index = self.find_working_camera()
            
            if camera_index is not None and not self.should_stop:
                print(f"CameraSystem: Found working camera at index {camera_index}")
                self.camera_found.emit(camera_index)
            else:
                # Try fallback with longer delay for V4L2 cameras
                if not self.should_stop:
                    print("CameraSystem: Trying V4L2 fallback with longer delay...")
                    time.sleep(0.5)  # Give V4L2 cameras more time
                    
                    camera_index = self.find_working_camera()
                    if camera_index is not None:
                        print(f"CameraSystem: V4L2 fallback found camera at index {camera_index}")
                        self.camera_found.emit(camera_index)
                    else:
                        print("CameraSystem: No working camera found after fallback")
                        self.camera_failed.emit()
                else:
                    self.camera_failed.emit()
            
        except Exception as e:
            print(f"CameraSystem: Critical error: {e}")
            self.camera_failed.emit()
        finally:
            self.detection_mode = False
    
    def is_camera_running(self):
        """Check if camera is currently running."""
        return (self.camera_thread and 
                self.camera_thread.isRunning() and 
                hasattr(self.camera_thread, 'cap') and 
                self.camera_thread.cap and 
                self.camera_thread.cap.isOpened())
    
    def cleanup(self):
        """Cleanup all camera resources."""
        self.stop_detection()
        self.stop_camera()


class CameraThread(QThread):
    """Thread for handling camera capture to avoid blocking the UI."""
    changePixmap = pyqtSignal(QImage)
    connectionError = pyqtSignal(str)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = False
        self.cap = None
        self.current_frame = None
        self.display_frame = None
        self._frame_lock = QtCore.QMutex()
        self.zoom_factor = 1.0

    def set_zoom(self, factor):
        """Set zoom factor for display."""
        self.zoom_factor = factor

    def try_connect(self):
        """Try to connect to USB camera with segfault protection."""
        if not OPENCV_AVAILABLE:
            print(f"=== CAMERA_THREAD: OpenCV not available")
            self.connectionError.emit("OpenCV not available")
            return False
            
        try:
            print(f"=== CAMERA_THREAD: Starting connection to camera {self.camera_index}")
            # Clean up any existing connection first
            if self.cap:
                try:
                    self.cap.release()
                except:
                    pass
                self.cap = None
                time.sleep(0.3)  # Give time for cleanup
            
            # Try to connect with safety measures for older OpenCV
            print(f"=== CAMERA_THREAD: Creating VideoCapture for index {self.camera_index}")
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                print(f"=== CAMERA_THREAD: Camera {self.camera_index} failed to open")
                self.connectionError.emit(f"USB camera {self.camera_index} not found or in use")
                return False
            
            print(f"=== CAMERA_THREAD: Camera {self.camera_index} opened, testing frame capture...")
            
            # Test reading a frame with safety checks
            for attempt in range(3):  # Try multiple times
                ret, frame = self.cap.read()
                print(f"=== CAMERA_THREAD: Frame read attempt {attempt + 1}: ret={ret}, frame_valid={ret and frame is not None and frame.size > 0}")
                if ret and frame is not None and frame.size > 0:
                    break
                time.sleep(0.1)
            else:
                print(f"=== CAMERA_THREAD: Camera {self.camera_index} failed all frame capture attempts")
                self.cap.release()
                self.cap = None
                self.connectionError.emit(f"USB camera {self.camera_index} cannot capture frames")
                return False
                
            print(f"=== CAMERA_THREAD: Camera {self.camera_index} frame capture successful, setting properties...")
            
            # Set basic camera properties safely - square aspect ratio and 10 FPS
            try:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 10)
                
                # Disable autofocus if supported (helps prevent crashes)
                try:
                    self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                except:
                    pass  # Ignore if autofocus control not supported
                
                # Set buffer size to 1 to reduce memory usage
                try:
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except:
                    pass  # Ignore if buffer size control not supported
                    
            except Exception as e:
                print(f"Warning: Could not set camera properties: {e}")
                # Continue anyway - properties are optional
            
            # Final test - try to read one more frame to ensure camera is stable
            try:
                ret, test_frame = self.cap.read()
                if ret and test_frame is not None and test_frame.size > 0:
                    height, width = test_frame.shape[:2]
                    print(f"=== CAMERA_THREAD: Camera {self.camera_index} initialized successfully: {width}x{height}")
                    return True
                else:
                    print(f"=== CAMERA_THREAD: Camera {self.camera_index} final stability test failed")
                    self.cap.release()
                    self.cap = None
                    self.connectionError.emit(f"Camera {self.camera_index} cannot provide stable frames")
                    return False
            except Exception as e:
                print(f"=== CAMERA_THREAD: Camera {self.camera_index} final test exception: {e}")
                self.cap.release()
                self.cap = None
                self.connectionError.emit(f"Camera {self.camera_index} final test failed: {e}")
                return False
                
        except Exception as e:
            print(f"=== CAMERA_THREAD: Camera {self.camera_index} connection exception: {e}")
            if self.cap:
                try:
                    self.cap.release()
                except:
                    pass
                self.cap = None
            self.connectionError.emit(f"Camera connection error: {str(e)}")
            return False

    def run(self):
        """Main camera capture loop - segfault-safe for Raspberry Pi."""
        if not self.try_connect():
            return
            
        self.running = True
        frame_count = 0
        
        try:
            while self.running:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret and self.running and frame is not None:
                        try:
                            # Basic safety checks for OpenCV 3.2.0 on Pi
                            if frame.size == 0:
                                continue
                                
                            with QtCore.QMutexLocker(self._frame_lock):
                                self.current_frame = frame.copy()
                                
                                # Simple zoom (avoid complex operations that can segfault)
                                if self.zoom_factor > 1.0:
                                    h, w = frame.shape[:2]
                                    if h > 0 and w > 0:  # Safety check
                                        center_x, center_y = w // 2, h // 2
                                        new_w, new_h = max(1, int(w / self.zoom_factor)), max(1, int(h / self.zoom_factor))
                                        x1 = max(0, center_x - new_w // 2)
                                        y1 = max(0, center_y - new_h // 2)
                                        x2 = min(w, x1 + new_w)
                                        y2 = min(h, y1 + new_h)
                                        
                                        if x2 > x1 and y2 > y1:  # Ensure valid crop
                                            cropped = frame[y1:y2, x1:x2]
                                            if cropped.size > 0:  # Safety check
                                                frame = cv2.resize(cropped, (w, h))
                                
                                self.display_frame = frame.copy()
                            
                            # Convert to QImage safely
                            if frame.size > 0 and len(frame.shape) == 3:
                                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                h, w, ch = rgb_image.shape
                                
                                if h > 0 and w > 0 and ch > 0:  # Safety checks
                                    bytes_per_line = ch * w
                                    # Make a copy to avoid memory issues
                                    rgb_copy = rgb_image.copy()
                                    qt_image = QImage(rgb_copy.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                                    
                                    if self.running:  # Check again before emit
                                        self.changePixmap.emit(qt_image)
                        
                        except Exception as e:
                            # Don't emit errors for every frame to avoid spam
                            frame_count += 1
                            if frame_count % 30 == 0:  # Log every 30 frames only
                                print(f"Frame processing error: {e}")
                        
                    # Controlled frame rate with safety
                    self.msleep(100)  # 10 FPS
                else:
                    self.msleep(100)  # Longer wait if camera not available
                    
        except Exception as e:
            self.connectionError.emit(f"Camera thread error: {e}")
        finally:
            # Ensure cleanup
            self.running = False
            if self.cap:
                try:
                    self.cap.release()
                except:
                    pass  # Ignore cleanup errors
                self.cap = None

    def stop(self):
        """Stop the camera thread safely - prevent segfaults."""
        self.running = False
        
        # Immediately stop any ongoing frame capture
        if self.cap:
            try:
                # Try to read one more frame to clear buffer (helps with some cameras)
                self.cap.read()
            except:
                pass
        
        # Give thread time to finish current operation
        if self.isRunning():
            if not self.wait(2000):  # Wait up to 2 seconds
                print("Warning: Camera thread did not stop cleanly, terminating...")
                self.terminate()
                self.wait(1000)  # Wait for termination
        
        # Clean up camera resource safely with multiple attempts
        if self.cap:
            for attempt in range(3):  # Try multiple times
                try:
                    self.cap.release()
                    self.cap = None
                    break
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        print(f"Warning: Camera cleanup error after {attempt + 1} attempts: {e}")
                    else:
                        time.sleep(0.1)  # Brief pause before retry
            
            # Force cleanup even if release failed
            self.cap = None


class CameraToolOffsetCalibration(QWidget):
    """Simplified Camera Tool Offset Calibration widget.
    
    Manual positioning workflow:
    1. Clean Nozzles - Heat both nozzles and position for cleaning
    2. Connect Camera - Regular mode, position camera under T0  
    3. Position T0 Course - Manual positioning with coarse adjustment
    4. Position T0 Fine - Manual positioning with fine adjustment
    5. Position T1 Course - Manual positioning with coarse adjustment  
    6. Position T1 Fine - Manual positioning with fine adjustment
    7. Results - Calculate and apply tool offsets
    """
    
    # Step indices
    STEP_CLEAN_NOZZLES = 0
    STEP_CONNECT_CAMERA = 1  
    STEP_POSITION_T0_COURSE = 2
    STEP_POSITION_T0_FINE = 3
    STEP_POSITION_T1_COURSE = 4
    STEP_POSITION_T1_FINE = 5
    STEP_RESULTS = 6
    TOTAL_STEPS = 7

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.model = getattr(main_window, "printer_model", None)
        self.octoprint_client = getattr(main_window, "octoprint_client", None)
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing CameraToolOffsetCalibration")

        # Camera related attributes  
        self.camera_thread = None
        self.camera_available = False
        self.camera_setup_in_progress = False
        
        # Positioning state
        self.tool0_position = None
        self.tool1_position = None
        self.current_tool = 0
        self.movement_step = 0.5  # Start with course movement
        
        # Wizard state
        self._current_step = 0
        
        # Load UI
        try:
            ui_file_path = os.path.join(os.path.dirname(__file__), "cameraToolOffsetCalibration.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("CameraToolOffsetCalibration UI loaded successfully")
        except Exception as e:
            self.logger.exception(f"Failed to load CameraToolOffsetCalibration UI file: {e}")

        # Bind UI elements
        self.stackedWidget: QStackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.stepLabel: QLabel = self.findChild(QLabel, "stepLabel")
        
        # Step pages
        self.step1Page: QWidget = self.findChild(QWidget, "step1Page")
        self.step2Page: QWidget = self.findChild(QWidget, "step2Page") 
        self.step3Page: QWidget = self.findChild(QWidget, "step3Page")
        
        # Step 1 elements (Clean Nozzles)
        self.step1Label: QLabel = self.findChild(QLabel, "step1Label")
        self.step1Gif: QLabel = self.findChild(QLabel, "step1Gif")
        
        # Step 2 elements (Connect Camera)
        self.step2Label: QLabel = self.findChild(QLabel, "step2Label")
        self.step2Gif: QLabel = self.findChild(QLabel, "step2Gif")
        
        # Step 3 elements (Camera Feed)
        self.webCamFeed: QLabel = self.findChild(QLabel, "webCamFeed")
        
        # Movement buttons (matching UI names)
        self.moveXPButton: QPushButton = self.findChild(QPushButton, "moveXPButton")
        self.moveXMButton: QPushButton = self.findChild(QPushButton, "moveXMButton")
        self.moveYPButton: QPushButton = self.findChild(QPushButton, "moveYPButton")
        self.moveYMButton: QPushButton = self.findChild(QPushButton, "moveYMButton")
        self.moveZPButton: QPushButton = self.findChild(QPushButton, "moveZPButton")  
        self.moveZMButton: QPushButton = self.findChild(QPushButton, "moveZMButton")
        
        # Navigation buttons
        self.nextButton: QPushButton = self.findChild(QPushButton, "stepNextButton")
        self.cancelButton: QPushButton = self.findChild(QPushButton, "stepCancelButton")

        # Create camera retry button (will be added dynamically when needed)
        self.camera_retry_button = QPushButton("Retry Camera")
        self.camera_retry_button.clicked.connect(self.start_camera_with_loading_dialog)
        self.camera_retry_button.hide()  # Hidden by default

        # Validate required elements
        required = [
            self.stackedWidget, self.stepLabel,
            self.step1Page, self.step2Page, self.step3Page,
            self.step1Label, self.step2Label, self.webCamFeed,
            self.moveXPButton, self.moveXMButton, self.moveYPButton, self.moveYMButton,
            self.moveZPButton, self.moveZMButton,
            self.nextButton, self.cancelButton
        ]
        check_ui_elements(self, required, "CameraToolOffsetCalibration")

        # Wire signals
        self.nextButton.clicked.connect(self.on_next_clicked)
        self.cancelButton.clicked.connect(self.on_cancel_clicked)
        
        # Movement button connections - step size changes based on current step
        self.moveXPButton.clicked.connect(lambda: self.move_axis('X', self.movement_step))
        self.moveXMButton.clicked.connect(lambda: self.move_axis('X', -self.movement_step))
        self.moveYPButton.clicked.connect(lambda: self.move_axis('Y', self.movement_step))
        self.moveYMButton.clicked.connect(lambda: self.move_axis('Y', -self.movement_step))
        self.moveZPButton.clicked.connect(lambda: self.move_axis('Z', self.movement_step))
        self.moveZMButton.clicked.connect(lambda: self.move_axis('Z', -self.movement_step))

        # Position tracking will be connected only when needed
        self._position_tracking_connected = False


        self.logger.info("CameraToolOffsetCalibration initialized successfully")

    def showEvent(self, event):
        """Reset the wizard UI to Step 1 each time the widget is shown."""
        super().showEvent(event)
        try:
            self.goto_step(self.STEP_CLEAN_NOZZLES)
            self.logger.debug("Reset wizard to step 1 on show")
        except Exception as e:
            self.logger.warning(f"Error resetting wizard on show: {e}")

    def goto_step(self, index: int):
        """Switch to the given step index and run step-entry hooks."""
        index = max(0, min(index, self.TOTAL_STEPS - 1))
        prev_step = getattr(self, "_current_step", 0)

        self._current_step = index
        if self.stackedWidget:
            self.stackedWidget.setCurrentIndex(min(index, 2))  # UI only has 3 pages
        self._update_step_label()

        # Step-specific logic
        if index == self.STEP_CLEAN_NOZZLES:
            # Step 1: Clean Nozzles - Heat both nozzles in mirror mode
            self.nextButton.setText("Next")
            self.nextButton.setEnabled(True)
            self.step1Label.setText("Please clean both nozzle tips with a wire brush for best calibration results.\n\nBoth nozzles are heated to 80°C and positioned for easy cleaning.")
            self._start_nozzle_cleaning()
            
        elif index == self.STEP_CONNECT_CAMERA:
            # Step 2: Connect Camera
            self.nextButton.setText("Next") 
            self.nextButton.setEnabled(True)
            self.step2Label.setText("Connect the USB calibration camera and place it exactly below the nozzle.\n\nThe printer is positioned at the center front for easy camera placement.")
            self._position_for_camera()
            # Don't auto-start camera here - wait for user to click Next
            
        elif index in [self.STEP_POSITION_T0_COURSE, self.STEP_POSITION_T0_FINE, 
                       self.STEP_POSITION_T1_COURSE, self.STEP_POSITION_T1_FINE]:
            # Steps 3-6: Positioning steps
            self._setup_positioning_step(index)
            
        elif index == self.STEP_RESULTS:
            # Step 7: Results
            self._show_results()

        self.logger.info(f"Switched to step {index + 1}/{self.TOTAL_STEPS}")

    def _update_step_label(self):
        """Update the step label."""
        try:
            if self.stepLabel:
                self.stepLabel.setText(f"Step {self._current_step + 1}/{self.TOTAL_STEPS}")
        except Exception:
            pass

    def _start_nozzle_cleaning(self):
        """Step 1: Heat both nozzles and position for cleaning."""
        if not self.octoprint_client:
            return
            
        try:
            # Home the printer
            self.octoprint_client.gcode("G28")
            
            # Set Z to 50mm
            self.octoprint_client.gcode("G1 Z50 F3000")
            
            # Set IDEX mode to Mirror
            self.octoprint_client.gcode("M605 S3")
            
            # Position at front of bed, X at 1/3 from left
            # Get machine build size from printer model
            build_size = getattr(self.model, 'machineBuildSize', {'X': 200}) if self.model else {'X': 200}
            bed_width = build_size.get('X', 200)
            x_position = int(bed_width / 3)  # 1/3 from left
            self.logger.info(f"Using bed width: {bed_width}mm, positioning at X{x_position} (1/3 from left)")
            self.octoprint_client.gcode(f"G1 X{x_position} Y20 F3000")
            
            # Heat both nozzles to 80C
            self.octoprint_client.gcode("M104 T0 S80")
            self.octoprint_client.gcode("M104 T1 S80")
            
            # Get latest M218 tool offsets from websockets
            self.octoprint_client.gcode("M503")
            
            self.logger.info("Nozzle cleaning setup complete")
            
        except Exception as e:
            self.logger.error(f"Error in nozzle cleaning setup: {e}")
            dialog.WarningOk(self, f"Error setting up nozzle cleaning: {e}")

    def _position_for_camera(self):
        """Step 2: Position for camera connection."""
        if not self.octoprint_client:
            return
            
        try:
            # Set regular mode and activate T0
            self.octoprint_client.gcode("M605 S1")
            self.octoprint_client.gcode("T0")
            
            # Move to center X, front Y, Z at 30mm
            # Get machine build size from printer model for center positioning
            build_size = getattr(self.model, 'machineBuildSize', {'X': 200}) if self.model else {'X': 200}
            bed_width = build_size.get('X', 200)
            x_center = int(bed_width / 2)  # Center of bed
            self.logger.info(f"Using bed width: {bed_width}mm, positioning camera at center X{x_center}")
            self.octoprint_client.gcode(f"G1 X{x_center} Y20 Z30 F3000")
            
            self.logger.info("Camera positioning setup complete")
            
        except Exception as e:
            self.logger.error(f"Error in camera positioning: {e}")
            dialog.WarningOk(self, f"Error positioning for camera: {e}")

    def _setup_positioning_step(self, step_index):
        """Setup positioning steps (3-6)."""
        try:
            # Determine current tool and step type
            if step_index in [self.STEP_POSITION_T0_COURSE, self.STEP_POSITION_T0_FINE]:
                tool = 0
                tool_name = "T0"
            else:
                tool = 1 
                tool_name = "T1"
                
            is_fine = step_index in [self.STEP_POSITION_T0_FINE, self.STEP_POSITION_T1_FINE]
            
            # Set movement step resolution
            self.movement_step = 0.01 if is_fine else 0.5
            
            # Setup camera if not already running
            if not (hasattr(self, 'camera_thread') and self.camera_thread and self.camera_thread.isRunning()):
                # Start camera with loading dialog
                self.start_camera_with_loading_dialog()
            else:
                # Camera already running, just update configuration if needed
                self._configure_camera_for_step(is_fine)
            
            # Update UI for current step
            step_type = "Fine" if is_fine else "Course"
            self.nextButton.setText("Record Position" if is_fine else "Fine Positioning")
            
            self.logger.info(f"Setup {step_type} positioning for {tool_name}")
            
        except Exception as e:
            self.logger.error(f"Error setting up positioning step: {e}")
            dialog.WarningOk(self, f"Error setting up positioning: {e}")

    def _configure_camera_for_step(self, is_fine):
        """Configure camera zoom for the current step."""
        try:
            # Simple implementation - zoom is handled by CameraThread if needed
            zoom = 2.0 if is_fine else 1.0
            # Note: zoom functionality can be added to CameraThread later if needed
        except Exception as e:
            self.logger.error(f"Error configuring camera: {e}")

    def _find_working_camera_direct(self):
        """Find working camera using simple detection."""
        return self.find_available_camera()

    def _attempt_camera_connection_with_loading(self):
        """Legacy method - redirect to new implementation with loading dialog."""
        print("Using legacy camera connection method - redirecting to new implementation")
        self.start_camera_with_loading_dialog()

    def _on_camera_connection_success(self, camera_index):
        """Handle successful camera connection with segfault protection."""
        try:
            # Close any existing connecting dialog
            if hasattr(self, 'connecting_dialog') and self.connecting_dialog:
                self.connecting_dialog.close()
                self.connecting_dialog = None
            
            # Camera feed is already started by _perform_camera_detection, so just configure
            self.camera_available = True
            self.camera_setup_in_progress = False
            self.logger.info(f"Camera connected successfully on index {camera_index}")
            
            # Clear any placeholder content
            self._clear_no_camera_layout()
            
            # Safely connect camera feed signals (prevent duplicates and segfaults)
            self._safe_connect_camera_feed_signals()
            
            # Proceed to next step
            self.goto_step(self.STEP_POSITION_T0_COURSE)
                
        except Exception as e:
            self.logger.error(f"Error in camera connection success: {e}")
            # Close dialog if it exists
            if hasattr(self, 'connecting_dialog') and self.connecting_dialog:
                self.connecting_dialog.close()
                self.connecting_dialog = None
            self._on_camera_connection_failed()
    
    def _safe_connect_camera_feed_signals(self):
        """This method is no longer needed with simple camera thread approach."""
        pass

    def _on_camera_connection_failed(self):
        """Handle failed camera connection with retry dialog."""
        try:
            self.camera_setup_in_progress = False
            
            # Hide loading dialog if it exists
            self.hide_loading_dialog()
            
            # Show retry dialog using RetrySkipCancel
            result = dialog.RetrySkipCancel(
                parent=self,
                text="Camera Connection Failed\n\nNo camera was detected. Please check your camera connection.\n\nWould you like to retry, skip camera setup, or cancel?",
                overlay=True,
                icon="warning"
            )
            
            if result == "retry":
                # User wants to retry - attempt connection again with small delay
                print("User chose to retry camera connection")
                QTimer.singleShot(500, self.start_camera_with_loading_dialog)
            elif result == "skip":
                # Continue without camera
                print("User chose to skip camera setup")
                self.camera_available = False
                self._camera_skipped = True
                self._show_camera_placeholder()
                self.goto_step(self.STEP_POSITION_T0_COURSE)
            else:
                # User cancelled - stay on current step
                print("User cancelled camera setup")
                pass
                
        except Exception as e:
            self.logger.error(f"Error handling camera connection failure: {e}")
            # Fallback - continue without camera
            self.camera_available = False
            self._camera_skipped = True
            self._show_camera_placeholder()

    def start_camera_with_loading_dialog(self):
        """Show loading dialog and start camera initialization."""
        if self.camera_setup_in_progress:
            return  # Prevent multiple simultaneous attempts
        
        self.camera_setup_in_progress = True
        
        try:
            # Show loading dialog
            self.show_loading_dialog()
            
            # Use a timer to start camera after dialog is shown
            QTimer.singleShot(100, self.start_camera)
            
        except Exception as e:
            self.logger.error(f"Error starting camera with loading: {e}")
            self.hide_loading_dialog()
            self.show_camera_error(f"Initialization error: {str(e)}")

    def show_loading_dialog(self):
        """Show 'Please wait, loading...' dialog."""
        try:
            self.loading_dialog = dialog.dialog(
                self, 
                "Please wait, loading camera...", 
                buttons=QMessageBox.NoButton,  # No buttons
                overlay=True,
                icon=":/Icons/img/icons/information.png"
            )
            self.loading_dialog.show()
            self.logger.info("Loading dialog shown")
        except Exception as e:
            self.logger.error(f"Error showing loading dialog: {e}")

    def hide_loading_dialog(self):
        """Hide the loading dialog."""
        try:
            if self.loading_dialog:
                self.loading_dialog.hide()
                self.loading_dialog = None
                self.logger.info("Loading dialog hidden")
        except Exception as e:
            self.logger.error(f"Error hiding loading dialog: {e}")

    def start_camera(self):
        """Initialize and start the camera feed."""
        if not OPENCV_AVAILABLE:
            self.hide_loading_dialog()
            self.show_camera_error("OpenCV not available - install opencv-python")
            return
            
        try:
            print("=== START_CAMERA: Starting camera feed...")
            self.logger.info("Starting camera feed...")
            
            # Try to find an available camera
            print("=== START_CAMERA: Calling find_available_camera()...")
            camera_index = self.find_available_camera()
            print(f"=== START_CAMERA: find_available_camera() returned: {camera_index}")
            
            if camera_index is not None:
                print(f"=== START_CAMERA: Creating CameraThread with index {camera_index}")
                self.camera_thread = CameraThread(camera_index)
                self.camera_thread.changePixmap.connect(self._update_camera_feed)
                self.camera_thread.connectionError.connect(self._on_camera_error)
                print("=== START_CAMERA: Starting camera thread...")
                self.camera_thread.start()
                self.camera_available = True
                self.camera_setup_in_progress = False
                self.logger.info(f"Camera started successfully on index {camera_index}")
                print(f"=== START_CAMERA: Camera thread started successfully")
                
                # Hide loading dialog on success
                self.hide_loading_dialog()
                
                # Clear any placeholder content
                self._clear_no_camera_layout()
                
                # Proceed to next step
                print("=== START_CAMERA: Going to next step")
                self.goto_step(self.STEP_POSITION_T0_COURSE)
            else:
                print("=== START_CAMERA: No camera found, calling _on_camera_connection_failed")
                self.hide_loading_dialog()
                self.camera_setup_in_progress = False
                self._on_camera_connection_failed()
                
        except Exception as e:
            print(f"=== START_CAMERA: Exception occurred: {e}")
            self.logger.error(f"Error starting camera: {e}")
            self.hide_loading_dialog()
            self.camera_setup_in_progress = False
            self._on_camera_connection_failed()

    def find_available_camera(self):
        """Find the first available USB camera index (prioritizing USB over CSI)."""
        if not OPENCV_AVAILABLE:
            return None
        
        import cv2
        import time
        
        # Check indices 1-5 first (USB cameras typically start at 1 if CSI is at 0)
        for i in range(1, 6):
            if self._test_camera_index(i):
                return i
        
        # If no cameras found at 1+, check index 0 but assume it might be CSI
        if self._test_camera_index(0):
            return 0
            
        return None

    def _test_camera_index(self, index):
        """Test if a camera at the given index is accessible with better V4L2 handling."""
        try:
            import cv2
            import time
            
            # For V4L2 cameras, try to open with CAP_V4L2 backend if available
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            except (AttributeError, Exception):
                cap = cv2.VideoCapture(index)
            
            # Give camera time to initialize (important for V4L2)
            time.sleep(0.3)
            
            success_count = 0
            
            # Try multiple reads to test stability
            for attempt in range(3):
                try:
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Check if frame has valid dimensions
                        if hasattr(frame, 'shape') and len(frame.shape) >= 2:
                            height, width = frame.shape[:2]
                            if height > 0 and width > 0:
                                success_count += 1
                                break  # One successful read is enough
                except Exception:
                    pass
                
                time.sleep(0.1)
            
            # Cleanup
            try:
                cap.release()
            except Exception:
                pass
            
            time.sleep(0.2)  # Allow camera to be released
            
            # Camera is working if we got at least one successful read
            return success_count > 0
                
        except Exception:
            try:
                if 'cap' in locals():
                    cap.release()
            except:
                pass
            return False

    def _update_camera_feed(self, image):
        """Update the camera feed label with new image."""
        try:
            # Scale image to fit the label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(image)
            scaled_pixmap = pixmap.scaled(
                self.webCamFeed.size(), 
                QtCore.Qt.KeepAspectRatio, 
                QtCore.Qt.SmoothTransformation
            )
            self.webCamFeed.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.logger.error(f"Error updating camera image: {e}")

    def show_camera_error(self, message):
        """Show camera error message and provide retry option."""
        self.webCamFeed.setText(f"Camera Error:\n{message}")
        self.webCamFeed.setStyleSheet("""
            QLabel {
                color: rgb(255, 100, 100);
                background-color: rgb(60, 60, 60);
                border: 2px solid rgb(150, 100, 100);
                border-radius: 5px;
                font-size: 12px;
                text-align: center;
            }
        """)
        self.camera_available = False
        
        # Show retry dialog
        result = dialog.RetrySkipCancel(
            parent=self,
            text=f"Camera Error\n\n{message}\n\nWould you like to retry, skip camera setup, or cancel?",
            overlay=True,
            icon="warning"
        )
        
        if result == "retry":
            # User wants to retry
            QTimer.singleShot(500, self.start_camera_with_loading_dialog)
        elif result == "skip":
            # Continue without camera
            self.camera_available = False
            self._camera_skipped = True
            self._show_camera_placeholder()
            self.goto_step(self.STEP_POSITION_T0_COURSE)
        else:
            # User cancelled - stay on current step
            pass

    def _show_camera_placeholder(self):
        """Show a placeholder when camera is not available."""
        if not self.webCamFeed:
            return
        
        # Create a placeholder image
        placeholder = QPixmap(640, 480)
        placeholder.fill(Qt.lightGray)
        
        # Draw text on placeholder
        painter = QPainter(placeholder)
        painter.setPen(Qt.black)
        painter.drawText(placeholder.rect(), Qt.AlignCenter, 
                        "Camera Not Available\nPosition nozzle manually\nusing movement controls")
        painter.end()
        
        self.webCamFeed.setPixmap(placeholder)
        self.logger.info("Showing camera placeholder - manual positioning mode")

    def _on_camera_found(self, camera_index):
        """Legacy method - redirect to new success handler."""
        self._on_camera_connection_success(camera_index)
    
    def _clear_no_camera_layout(self):
        """Clear the no-camera layout if it exists."""
        try:
            if hasattr(self, 'webCamFeed') and self.webCamFeed and self.webCamFeed.layout():
                # Clear the layout
                while self.webCamFeed.layout().count():
                    item = self.webCamFeed.layout().takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                self.webCamFeed.layout().deleteLater()
                self.webCamFeed.setLayout(None)
                
                # Reset camera feed to normal style
                self.webCamFeed.setStyleSheet("")
                self.webCamFeed.setText("")
        except Exception as e:
            self.logger.error(f"Error clearing no-camera layout: {e}")

    def _find_working_camera_direct(self):
        """Direct camera detection fallback using simple detection."""
        return self.find_available_camera()

    def _on_camera_failed(self):
        """Legacy method - redirect to new failure handler."""
        self._on_camera_connection_failed()
    
    def _show_camera_placeholder(self):
        """Show placeholder when camera is not available."""
        if hasattr(self, 'webCamFeed') and self.webCamFeed:
            # Create a layout for the camera feed area
            layout = QVBoxLayout(self.webCamFeed)
            
            # Message label
            message_label = QLabel("Camera not available")
            message_label.setStyleSheet("""
                QLabel {
                    color: rgb(200, 200, 200);
                    background-color: transparent;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px;
                    qproperty-alignment: AlignCenter;
                }
            """)
            
            # Instruction label
            instruction_label = QLabel("You can continue with manual positioning\nor retry camera connection")
            instruction_label.setStyleSheet("""
                QLabel {
                    color: rgb(150, 150, 150);
                    background-color: transparent;
                    font-size: 11px;
                    padding: 5px;
                    qproperty-alignment: AlignCenter;
                }
            """)
            
            # Retry button
            retry_button = QPushButton("Retry Camera")
            retry_button.clicked.connect(self.start_camera_with_loading_dialog)
            retry_button.setStyleSheet("""
                QPushButton {
                    border: 1px solid rgb(87, 87, 87);
                    background-color: qlineargradient(spread: pad, x1: 0, y1: 1, x2: 0, y2: 0.188, stop: 0 rgba(180, 180, 180, 255), stop: 1 rgba(255, 255, 255, 255));
                    height: 50px;
                    width: 120px;
                    border-radius: 5px;
                    font: 12pt "Gotham";
                    color: rgb(50, 50, 50);
                }
                QPushButton:pressed {
                    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #dadbde, stop: 1 #f6f7fa);
                }
                QPushButton:focus {
                    outline: none;
                }
            """)
            
            layout.addStretch()
            layout.addWidget(message_label)
            layout.addWidget(instruction_label)
            layout.addWidget(retry_button)
            layout.addStretch()
            
        # Set camera feed area style
        self.webCamFeed.setStyleSheet("""
            QLabel {
                background-color: rgb(60, 60, 60);
                border: 2px solid rgb(100, 100, 100);
                border-radius: 5px;
            }
        """)

    def _handle_camera_setup_cancelled(self):
        """Handle when user cancels camera setup."""
        self.logger.info("Camera setup cancelled by user")
        # Allow user to continue without camera
        self.camera_available = False
        self._camera_skipped = True  # Mark that user chose to skip camera
        
        # Update next button state to allow proceeding
        self._update_next_button_state()
        
        # Show no-camera message in camera feed area with retry option
        if hasattr(self, 'webCamFeed') and self.webCamFeed:
            # Create a layout for the camera feed area if it doesn't have one
            if not self.webCamFeed.layout():
                layout = QVBoxLayout(self.webCamFeed)
                
                # Message label
                message_label = QLabel("Camera not available")
                message_label.setStyleSheet("""
                    QLabel {
                        color: rgb(200, 200, 200);
                        background-color: transparent;
                        font-size: 14px;
                        font-weight: bold;
                        padding: 10px;
                        qproperty-alignment: AlignCenter;
                    }
                """)
                
                # Instruction label
                instruction_label = QLabel("You can continue with manual positioning\nor retry camera connection")
                instruction_label.setStyleSheet("""
                    QLabel {
                        color: rgb(150, 150, 150);
                        background-color: transparent;
                        font-size: 11px;
                        padding: 5px;
                        qproperty-alignment: AlignCenter;
                    }
                """)
                
                # Retry button
                retry_button = QPushButton("Retry Camera")
                retry_button.clicked.connect(self.start_camera_with_loading_dialog)
                retry_button.setStyleSheet("""
                    QPushButton {
                        border: 1px solid rgb(87, 87, 87);
                        background-color: qlineargradient(spread: pad, x1: 0, y1: 1, x2: 0, y2: 0.188, stop: 0 rgba(180, 180, 180, 255), stop: 1 rgba(255, 255, 255, 255));
                        height: 50px;
                        width: 120px;
                        border-radius: 5px;
                        font: 12pt "Gotham";
                        color: rgb(50, 50, 50);
                    }
                    QPushButton:pressed {
                        background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #dadbde, stop: 1 #f6f7fa);
                    }
                    QPushButton:focus {
                        outline: none;
                    }
                """)
                
                layout.addStretch()
                layout.addWidget(message_label)
                layout.addWidget(instruction_label)
                layout.addWidget(retry_button)
                layout.addStretch()
                
            # Set camera feed area style
            self.webCamFeed.setStyleSheet("""
                QLabel {
                    background-color: rgb(60, 60, 60);
                    border: 2px solid rgb(100, 100, 100);
                    border-radius: 5px;
                }
            """)

    # Legacy methods removed - now using unified CameraSystem
    # start_camera(), show_camera_error(), check_usb_camera_available(),
    # find_available_camera(), _test_camera_index(), _find_usb_cameras(),
    # _test_camera_connection(), _check_camera_status() have been replaced

    def _update_camera_feed(self, qt_image):
        """Update the camera feed with crosshair overlay."""
        if not self.webCamFeed:
            return
            
        # Create pixmap from image
        pixmap = QPixmap.fromImage(qt_image)
        
        # Draw crosshair overlay
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.red, 2))
        
        # Draw circle and crosshair in center
        center_x = pixmap.width() // 2
        center_y = pixmap.height() // 2
        radius = 15 if self.movement_step == 0.01 else 10
        
        # Draw circle
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Draw crosshair
        painter.drawLine(center_x - radius - 5, center_y, center_x + radius + 5, center_y)
        painter.drawLine(center_x, center_y - radius - 5, center_x, center_y + radius + 5)
        
        painter.end()
        
        # Update the label
        self.webCamFeed.setPixmap(pixmap)

    def _on_camera_error(self, error_msg):
        """Handle camera connection errors with simple camera thread approach."""
        try:
            self.logger.error(f"Camera error: {error_msg}")
            
            # Stop camera thread safely
            if hasattr(self, 'camera_thread') and self.camera_thread:
                try:
                    self.camera_thread.stop()
                    self.camera_thread.wait(1000)  # Wait up to 1 second
                except:
                    pass
                self.camera_thread = None
            
            # Close any loading dialog
            self.hide_loading_dialog()
            
            # Reset setup flag
            self.camera_setup_in_progress = False
            
            # Show retry dialog
            self._on_camera_connection_failed()
            
        except Exception as e:
            self.logger.error(f"Error in camera error handler: {e}")
            # Fallback - reset state
            self.camera_setup_in_progress = False
            self.camera_available = False
            # Fallback - show placeholder and continue
            self._show_camera_placeholder()
    
    def _show_camera_error_dialog(self, error_msg):
        """Show camera error dialog with retry/skip/cancel options using utils.dialog."""
        try:
            # Format the error message for better display
            formatted_msg = f"Camera Error\n\n{error_msg}\n\nWhat would you like to do?"
            
            # Use RetrySkipCancel from utils.dialog for consistent styling
            result = dialog.RetrySkipCancel(
                parent=self,
                text=formatted_msg,
                overlay=True,
                icon="warning"
            )
            
            if result == "retry":
                print("User chose to retry after camera error")
                QTimer.singleShot(500, self.start_camera_with_loading_dialog)
            elif result == "skip":
                print("User chose to continue without camera after error")
                self.camera_available = False
                self._camera_skipped = True
                self._show_camera_placeholder()
                # Continue to positioning steps
                self.goto_step(self.STEP_POSITION_T0_COURSE)
            else:
                print("User cancelled after camera error")
                # Stay on current step - user can try again or cancel wizard
                pass
                
        except Exception as e:
            self.logger.error(f"Error showing camera error dialog: {e}")
            # Fallback - show placeholder and continue
            self._show_camera_placeholder()
    
    def _show_camera_placeholder(self):
        """Show a placeholder when camera is not available."""
        if not self.webCamFeed:
            return
        
        # Create a placeholder image
        placeholder = QPixmap(640, 480)
        placeholder.fill(Qt.lightGray)
        
        # Draw text on placeholder
        painter = QPainter(placeholder)
        painter.setPen(Qt.black)
        painter.drawText(placeholder.rect(), Qt.AlignCenter, 
                        "Camera Not Available\nPosition nozzle manually\nusing movement controls")
        painter.end()
        
        self.webCamFeed.setPixmap(placeholder)
        self.logger.info("Showing camera placeholder - manual positioning mode")

    def _connect_position_tracking(self):
        """Connect position tracking when needed for recording tool positions."""
        if not self._position_tracking_connected and self.model:
            self.model.current_position_updated.connect(self.on_position_updated)
            self._position_tracking_connected = True
            self.logger.debug("Position tracking connected")
    
    def _disconnect_position_tracking(self):
        """Disconnect position tracking when no longer needed."""
        if self._position_tracking_connected and self.model:
            try:
                self.model.current_position_updated.disconnect(self.on_position_updated)
                self._position_tracking_connected = False
                self.logger.debug("Position tracking disconnected")
            except TypeError:
                # Signal was already disconnected
                self._position_tracking_connected = False

    def move_axis(self, axis, distance):
        """Move the specified axis by the given distance."""
        if not self.octoprint_client:
            return
            
        try:
            command = f"G91\nG1 {axis}{distance} F3000\nG90"
            self.octoprint_client.gcode(command)
            self.logger.debug(f"Moving {axis} by {distance}mm")
        except Exception as e:
            self.logger.error(f"Error moving {axis} axis: {e}")

    def on_next_clicked(self):
        """Handle next button clicks with segfault protection."""
        try:
            current_step = self._current_step
            
            if current_step == self.STEP_CLEAN_NOZZLES:
                # Move to camera connection step
                self.goto_step(self.STEP_CONNECT_CAMERA)
                
            elif current_step == self.STEP_CONNECT_CAMERA:
                # Show loading dialog and try to connect camera
                try:
                    self.start_camera_with_loading_dialog()
                except Exception as e:
                    self.logger.error(f"Error starting camera connection: {e}")
                    # Show camera error with retry option
                    self.show_camera_error(f"Connection error: {str(e)}")
                return  # Don't proceed to next step until camera is handled
                
            elif current_step == self.STEP_POSITION_T0_COURSE:
                # Move to T0 fine positioning
                self.goto_step(self.STEP_POSITION_T0_FINE)
                
            elif current_step == self.STEP_POSITION_T0_FINE:
                # Record T0 position and move to T1 setup
                try:
                    self._record_tool_position(0)
                    self._switch_to_tool(1)
                    self.goto_step(self.STEP_POSITION_T1_COURSE)
                except Exception as e:
                    self.logger.error(f"Error recording T0 position: {e}")
                    dialog.WarningOk(self, f"Error recording T0 position: {e}")
                
            elif current_step == self.STEP_POSITION_T1_COURSE:
                # Move to T1 fine positioning
                self.goto_step(self.STEP_POSITION_T1_FINE)
                
            elif current_step == self.STEP_POSITION_T1_FINE:
                # Record T1 position and show results
                try:
                    self._record_tool_position(1)
                    self.goto_step(self.STEP_RESULTS)
                except Exception as e:
                    self.logger.error(f"Error recording T1 position: {e}")
                    dialog.WarningOk(self, f"Error recording T1 position: {e}")
                
            elif current_step == self.STEP_RESULTS:
                # Apply tool offsets and finish
                try:
                    self._apply_tool_offsets()
                except Exception as e:
                    self.logger.error(f"Error applying tool offsets: {e}")
                    dialog.WarningOk(self, f"Error applying tool offsets: {e}")
                
        except Exception as e:
            self.logger.error(f"Error in next button handler: {e}")
            dialog.WarningOk(self, f"An error occurred: {e}")

    def _record_tool_position(self, tool):
        """Record the current position for the specified tool."""
        if not self.octoprint_client:
            return
            
        try:
            # Connect position tracking for this recording
            self._connect_position_tracking()
            
            # Send M114 to get current position
            self.current_tool = tool
            self.octoprint_client.gcode("M114")
            self.logger.info(f"Requesting position for tool {tool}")
            
        except Exception as e:
            self.logger.error(f"Error recording tool {tool} position: {e}")

    def _switch_to_tool(self, tool):
        """Switch to the specified tool."""
        if not self.octoprint_client:
            return
            
        try:
            # Move Z down 5mm, switch tool, move Z back up
            self.octoprint_client.gcode("G91")  # Relative mode
            self.octoprint_client.gcode("G1 Z-5 F3000")  # Move down
            self.octoprint_client.gcode(f"T{tool}")  # Switch tool
            self.octoprint_client.gcode("G1 Z5 F3000")  # Move back up
            self.octoprint_client.gcode("G90")  # Absolute mode
            
            self.logger.info(f"Switched to tool {tool}")
            
        except Exception as e:
            self.logger.error(f"Error switching to tool {tool}: {e}")

    def on_position_updated(self, position):
        """Handle position updates from websocket."""
        try:
            if self.current_tool is not None and 'x' in position and 'y' in position:
                pos = {'x': position['x'], 'y': position['y']}
                
                if self.current_tool == 0:
                    self.tool0_position = pos
                    self.logger.info(f"Recorded T0 position: {pos}")
                elif self.current_tool == 1:
                    self.tool1_position = pos
                    self.logger.info(f"Recorded T1 position: {pos}")
                    
                # Reset current tool
                self.current_tool = None
                
                # Disconnect position tracking since we got what we needed
                self._disconnect_position_tracking()
                
        except Exception as e:
            self.logger.error(f"Error handling position update: {e}")

    def _show_results(self):
        """Show the results and calculated offsets."""
        try:
            self.nextButton.setText("Apply Tool Offsets")
            
            if self.tool0_position and self.tool1_position:
                # Calculate offset differences
                x_diff = self.tool1_position['x'] - self.tool0_position['x']
                y_diff = self.tool1_position['y'] - self.tool0_position['y']
                
                # Get current tool offsets from printer model
                current_x_offset = float(getattr(self.model, 'tool_offsets', {}).get('X', 0)) if self.model else 0.0
                current_y_offset = float(getattr(self.model, 'tool_offsets', {}).get('Y', 0)) if self.model else 0.0
                
                # Calculate new offsets
                new_x_offset = current_x_offset + x_diff
                new_y_offset = current_y_offset + y_diff
                
                # Store calculated offsets
                self.calculated_offsets = {
                    'x': new_x_offset,
                    'y': new_y_offset
                }
                
                self.logger.info(f"Calculated tool offsets - X: {new_x_offset}, Y: {new_y_offset}")
                
            else:
                dialog.WarningOk(self, "Missing position data for offset calculation")
                
        except Exception as e:
            self.logger.error(f"Error showing results: {e}")
            dialog.WarningOk(self, f"Error calculating results: {e}")

    def _apply_tool_offsets(self):
        """Apply the calculated tool offsets."""
        if not self.octoprint_client or not hasattr(self, 'calculated_offsets'):
            return
            
        try:
            x_offset = self.calculated_offsets['x']
            y_offset = self.calculated_offsets['y']
            
            # Apply tool offsets using M218
            self.octoprint_client.gcode(f"M218 T1 X{x_offset} Y{y_offset}")
            
            # Save configuration
            self.octoprint_client.gcode("SAVE_CONFIG")
            
            self.logger.info(f"Applied tool offsets - X: {x_offset}, Y: {y_offset}")
            
            dialog.InfoOk(self, f"Tool offsets applied successfully!\nX: {x_offset:.3f}mm\nY: {y_offset:.3f}mm")
            
            # Return to main calibrate screen
            self.on_cancel_clicked()
            
        except Exception as e:
            self.logger.error(f"Error applying tool offsets: {e}")
            dialog.WarningOk(self, f"Error applying tool offsets: {e}")

    def on_cancel_clicked(self):
        """Handle cancel button clicks and return to main calibrate screen."""
        try:
            # Stop camera
            self.stop_camera()
            
            # Return to main calibrate screen (similar to NozzleChangeWizard pattern)
            self.main_window.calibrate_screen.show_calibrate_screen()
                        
        except Exception as e:
            self.logger.error(f"Error in cancel handler: {e}")
            # Even if there's an error, try to return to calibrate screen
            self.main_window.calibrate_screen.show_calibrate_screen()

    def stop_camera(self):
        """Stop the camera feed safely using the simple CameraThread approach."""
        try:
            print("=== STOP_CAMERA: Starting camera stop process...")
            
            # Hide loading dialog if it's still showing
            self.hide_loading_dialog()
            print("=== STOP_CAMERA: Loading dialog hidden")
            
            if self.camera_thread and self.camera_thread.isRunning():
                self.logger.info("Stopping camera thread...")
                print("=== STOP_CAMERA: Camera thread is running, stopping...")
                
                # Disconnect signal to prevent any remaining frames from being processed
                try:
                    print("=== STOP_CAMERA: Disconnecting changePixmap signal...")
                    self.camera_thread.changePixmap.disconnect()
                    print("=== STOP_CAMERA: changePixmap signal disconnected")
                except Exception as e:
                    print(f"=== STOP_CAMERA: Signal disconnect warning: {e}")
                    pass  # Signal might already be disconnected
                
                # Stop the thread
                print("=== STOP_CAMERA: Calling camera_thread.stop()...")
                self.camera_thread.stop()
                print("=== STOP_CAMERA: camera_thread.stop() completed")
                
                # Clear the reference
                print("=== STOP_CAMERA: Clearing camera_thread reference...")
                self.camera_thread = None
                self.camera_available = False
                self.logger.info("Camera stopped successfully")
                print("=== STOP_CAMERA: Camera stopped successfully")
            else:
                print("=== STOP_CAMERA: No running camera thread to stop")
            
            # Reset setup flag
            self.camera_setup_in_progress = False
            print("=== STOP_CAMERA: Stop process completed")
                
        except Exception as e:
            print(f"=== STOP_CAMERA: Exception during stop: {e}")
            self.logger.error(f"Error stopping camera: {e}")
            # Even if there's an error, clear the reference to prevent further issues
            self.camera_thread = None
            self.camera_available = False
            self.camera_setup_in_progress = False


    def cleanup(self):
        """Cleanup resources when widget is destroyed."""
        try:
            print("Starting simple cleanup...")
            
            # Stop camera using simple method
            self.stop_camera()
            
            # Disconnect position tracking
            self._disconnect_position_tracking()
            
            print("Cleanup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            print(f"Cleanup error (non-critical): {e}")

    def closeEvent(self, event):
        """Handle widget close event with full cleanup."""
        try:
            self.cleanup()
            super().closeEvent(event)
        except Exception as e:
            print(f"Close event error (non-critical): {e}")
            super().closeEvent(event)
