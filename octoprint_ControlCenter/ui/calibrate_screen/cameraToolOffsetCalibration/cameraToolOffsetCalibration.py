"""
Camera Tool Offset Calibration
==============================

User-guided UI flow for calibrating tool offsets using a camera feed.

Features implemented:
- USB camera feed display
- 1mm movement controls (X+, X-, Y+, Y-)
- Basic navigation (Next/Cancel buttons)
- Integration with calibrate_screen

Future features:
- Actual calibration logic
- Crosshair overlay
- Offset calculations
"""

import os
import sys
import time
import subprocess
import time

# Dynamic OpenCV import with automatic installation
try:
    import cv2
except ImportError:
    print("OpenCV not found. Attempting to install...")
    
    try:
        # For Raspberry Pi - use prebuilt package to avoid long compilation
        print("Installing OpenCV using apt (prebuilt package)...")
        subprocess.check_call(['sudo', 'apt', 'update'])
        subprocess.check_call(['sudo', 'apt', 'install', '-y', 'python3-opencv'])
        import cv2
        print("✓ OpenCV installed successfully from apt!")
    except subprocess.CalledProcessError:
        # Fallback to pip if apt fails
        try:
            print("Apt installation failed, trying pip as fallback...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'opencv-python'])
            import cv2
            print("✓ OpenCV installed successfully with pip!")
        except subprocess.CalledProcessError:
            # Final fallback with sudo pip
            try:
                subprocess.check_call(['sudo', 'pip3', 'install', 'opencv-python'])
                import cv2
                print("✓ OpenCV installed successfully with sudo pip!")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                raise ImportError(
                    "Failed to automatically install OpenCV. "
                    "Please install it manually with: sudo apt install python3-opencv "
                    "or pip install opencv-python"
                ) from e

from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel, QMessageBox
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils import dialog
from .nozzle_detector import NozzleDetector


class CameraThread(QThread):
    """Thread for handling camera capture to avoid blocking the UI."""
    changePixmap = pyqtSignal(QImage)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = False
        self.cap = None
        self.current_frame = None
        self.display_frame = None
        self._frame_lock = QtCore.QMutex()

    def run(self):
        """Main camera capture loop."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                return
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.running = True
            
            while self.running:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret and self.running:  # Check running again after read
                        try:
                            # Store current frame for detection algorithms
                            self._frame_lock.lock()
                            self.current_frame = frame.copy()
                            
                            # Use display frame if available, otherwise use original frame
                            display_frame = self.display_frame if self.display_frame is not None else frame
                            self._frame_lock.unlock()
                            
                            # Convert the image to RGB format for display
                            rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                            h, w, ch = rgb_image.shape
                            bytes_per_line = ch * w
                            
                            # Create QImage - make a copy of the data to avoid memory issues
                            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                            
                            # Only emit if still running
                            if self.running:
                                self.changePixmap.emit(qt_image)
                        except Exception as e:
                            # Silently continue on frame processing errors
                            self._frame_lock.unlock()  # Ensure unlock on error
                            pass
                else:
                    break
                
                # Control frame rate
                self.msleep(33)  # ~30 FPS
        
        except Exception as e:
            # Handle any camera errors gracefully
            pass
        finally:
            # Always clean up camera resource
            if self.cap:
                self.cap.release()
                self.cap = None

    def stop(self):
        """Stop the camera thread safely."""
        self.running = False
        
        # Release camera resource immediately
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Wait for thread to finish with a timeout
        if self.isRunning():
            self.quit()
            if not self.wait(1000):  # Wait up to 1 second
                self.terminate()  # Force terminate if needed
                self.wait(500)  # Give it a bit more time after terminate

    def get_current_frame(self):
        """Get the current raw frame for detection algorithms."""
        self._frame_lock.lock()
        try:
            frame = self.current_frame.copy() if self.current_frame is not None else None
            return frame
        finally:
            self._frame_lock.unlock()

    def update_display_frame(self, annotated_frame):
        """Update the frame that will be displayed (with detection overlays)."""
        self._frame_lock.lock()
        try:
            self.display_frame = annotated_frame.copy() if annotated_frame is not None else None
        finally:
            self._frame_lock.unlock()

    def clear_display_frame(self):
        """Clear the display frame to show original camera feed."""
        self._frame_lock.lock()
        try:
            self.display_frame = None
        finally:
            self._frame_lock.unlock()


class CameraToolOffsetCalibration(QWidget):
    """Camera Tool Offset Calibration widget.

    Responsibilities:
    - Load and bind UI elements
    - Handle USB camera feed display
    - Provide 1mm movement controls
    - Basic navigation between calibration screen
    """
    
    # Step indices (0-based) for clarity
    STEP_CLEAN_NOZZLES = 0
    STEP_CONNECT_CAMERA = 1  
    STEP_CAMERA_FEED = 2
    TOTAL_STEPS = 3

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.octoprint_client = getattr(main_window, "octoprint_client", None)
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing CameraToolOffsetCalibration")

        # Camera related attributes
        self.camera_thread = None
        self.camera_available = False
        self.opencv_available = True
        self.loading_dialog = None
        
        # Enhanced detection system
        self.nozzle_detector = None
        self.detection_active = False
        
        # Wizard state
        self._current_step = 0
        
        # Check if OpenCV is available
        try:
            cv2.__version__
            # Initialize nozzle detector
            self.nozzle_detector = NozzleDetector()
            self.logger.info("Enhanced nozzle detection system initialized")
        except NameError:
            self.opencv_available = False
            self.logger.warning("OpenCV not available - camera functionality disabled")

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
        
        # Movement buttons (only on step 3)
        self.moveXPButton: QPushButton = self.findChild(QPushButton, "moveXPButton")
        self.moveXMButton: QPushButton = self.findChild(QPushButton, "moveXMButton")
        self.moveYPButton: QPushButton = self.findChild(QPushButton, "moveYPButton")
        self.moveYMButton: QPushButton = self.findChild(QPushButton, "moveYMButton")
        
        # Navigation buttons
        self.nextButton: QPushButton = self.findChild(QPushButton, "step1NextButton")
        self.cancelButton: QPushButton = self.findChild(QPushButton, "step1CancelButton")

        # Validate required elements
        required = [
            self.stackedWidget, self.stepLabel,
            self.step1Page, self.step2Page, self.step3Page,
            self.step1Label, self.step1Gif, self.step2Label, self.step2Gif, self.webCamFeed,
            self.moveXPButton, self.moveXMButton, self.moveYPButton, self.moveYMButton,
            self.nextButton, self.cancelButton
        ]
        check_ui_elements(self, required, "CameraToolOffsetCalibration")

        # Set up movement step (1mm)
        self.movement_step = 1.0

        # Wire signals
        self.nextButton.clicked.connect(self.on_next_clicked)
        self.cancelButton.clicked.connect(self.on_cancel_clicked)
        
        # Movement button connections (1mm steps) - only active on step 3
        self.moveXPButton.clicked.connect(lambda: self.move_axis('x', self.movement_step))
        self.moveXMButton.clicked.connect(lambda: self.move_axis('x', -self.movement_step))
        self.moveYPButton.clicked.connect(lambda: self.move_axis('y', self.movement_step))
        self.moveYMButton.clicked.connect(lambda: self.move_axis('y', -self.movement_step))

        # Start at step 1 (Clean Nozzles)
        self.goto_step(self.STEP_CLEAN_NOZZLES)

        self.logger.info("CameraToolOffsetCalibration initialized successfully")

    def goto_step(self, index: int):
        """Switch to the given step index (0-based) and run step-entry hooks."""
        index = max(0, min(index, self.TOTAL_STEPS - 1))
        prev_step = getattr(self, "_current_step", 0)

        # Update the step
        self._current_step = index
        if self.stackedWidget:
            self.stackedWidget.setCurrentIndex(index)
        self._update_step_label()

        # Step-specific logic
        if index == self.STEP_CLEAN_NOZZLES:
            # Step 1: Clean Nozzles
            self.nextButton.setText("Next")
            self.nextButton.setEnabled(True)
            
        elif index == self.STEP_CONNECT_CAMERA:
            # Step 2: Connect Camera and position printer
            self.nextButton.setText("Next")
            self.nextButton.setEnabled(True)
            # Start printer positioning when entering step 2
            if prev_step != self.STEP_CONNECT_CAMERA:
                self._perform_printer_positioning()
            
        elif index == self.STEP_CAMERA_FEED:
            # Step 3: Camera Feed - ready for kTAMV calibration
            self.nextButton.setText("Start kTAMV Calibration")
            self.nextButton.setEnabled(True)
            # Stop camera from previous steps if running
            if prev_step != self.STEP_CAMERA_FEED:
                self.stop_camera()
            # Check for USB camera and start feed
            if not self.check_usb_camera_available():
                dialog.WarningOk(self, "Please connect a USB calibration camera to a USB port and try again", overlay=True)
                # Go back to step 2
                self.goto_step(self.STEP_CONNECT_CAMERA)
                return
            # Start camera with loading dialog
            self.start_camera_with_loading()

        self.logger.info(f"Switched to step {index + 1}/{self.TOTAL_STEPS}")


    def _update_step_label(self):
        """Update the "Step X/Y" label to match the current index."""
        try:
            if self.stepLabel:
                self.stepLabel.setText(f"Step {self._current_step + 1}/{self.TOTAL_STEPS}")
        except Exception:
            pass

    def on_next_clicked(self):
        """Handle Next button click - simple step advancement."""
        try:
            if self._current_step == self.STEP_CLEAN_NOZZLES:
                # Step 1 -> Step 2
                self.goto_step(self.STEP_CONNECT_CAMERA)
                
            elif self._current_step == self.STEP_CONNECT_CAMERA:
                # Step 2 -> Step 3
                self.goto_step(self.STEP_CAMERA_FEED)
                
            elif self._current_step == self.STEP_CAMERA_FEED:
                # Step 3: Start kTAMV calibration directly
                self._start_ktamv_calibration_direct()
                
        except Exception as e:
            self.logger.error(f"Error in on_next_clicked: {e}")
            dialog.WarningOk(self, f"Navigation error: {str(e)}", overlay=True)


    def _perform_printer_positioning(self):
        """Perform printer homing and positioning for step 2."""
        self.logger.info("Starting printer positioning for camera calibration")
        
        try:
            if not self.octoprint_client:
                self.logger.error("OctoPrint client not available for positioning")
                return
            
            # Simple direct positioning sequence like nozzleChangeWizard
            self.logger.info("Homing all axes...")
            self.octoprint_client.gcode("G28")
            
            self.logger.info("Selecting T0 tool...")
            self.octoprint_client.selectTool(0)
            
            self.logger.info("Moving bed to Z25...")
            self.octoprint_client.gcode("G1 Z25 F1200")
            
            # Move to front center position (same as nozzleChangeWizard)
            self.logger.info("Moving to front center position...")
            try:
                build_size = self.main_window.printer_model.machineBuildSize
                center_x = build_size.get('X', 220) / 2  # X center with fallback
                front_y = 30  # Front position (30mm from front)
                
                self.octoprint_client.gcode(f"G1 X{center_x} Y{front_y} F6000")
                self.logger.info(f"Moved to X{center_x} Y{front_y}")
            except Exception as e:
                # Fallback to default position if build size not available
                self.logger.warning(f"Could not get build size, using default position: {e}")
                self.octoprint_client.gcode("G1 X110 Y30 F6000")  # Default 220mm bed center
            
            self.logger.info("Printer positioning complete")
            
        except Exception as e:
            self.logger.error(f"Error during printer positioning: {e}")



    def setup_camera_placeholder(self):
        """Set up placeholder text for camera feed."""
        if not self.opencv_available:
            self.webCamFeed.setText("Camera Feed\n(OpenCV not available)")
            self.webCamFeed.setStyleSheet("""
                QLabel {
                    color: rgb(255, 200, 100);
                    background-color: rgb(60, 60, 60);
                    border: 2px solid rgb(150, 150, 100);
                    border-radius: 5px;
                    font-size: 14px;
                    text-align: center;
                }
            """)
        else:
            self.webCamFeed.setText("Camera Feed\n(Initializing...)")
            self.webCamFeed.setStyleSheet("""
                QLabel {
                    color: rgb(255, 255, 255);
                    background-color: rgb(60, 60, 60);
                    border: 2px solid rgb(100, 100, 100);
                    border-radius: 5px;
                    font-size: 14px;
                    text-align: center;
                }
            """)

    def showEvent(self, event):
        """Reset to step 1 when widget is shown."""
        super().showEvent(event)
        # Reset to first step
        self.goto_step(self.STEP_CLEAN_NOZZLES)

    def hideEvent(self, event):
        """Stop camera when widget is hidden."""
        super().hideEvent(event)
        # Use a timer to delay camera stop to avoid race conditions
        QTimer.singleShot(50, self.stop_camera)

    def check_usb_camera_available(self):
        """Check if a USB camera is available before starting the camera screen."""
        if not self.opencv_available:
            self.logger.warning("OpenCV not available, cannot detect cameras")
            return False
        
        self.logger.info("Checking for USB camera before opening camera calibration")
        
        try:
            # Check indices 1-5 first (USB cameras typically start at 1 if CSI is at 0)
            for i in range(1, 6):
                if self._test_camera_index(i):
                    self.logger.info(f"USB camera found at index {i}")
                    return True
            
            # If no cameras found at 1+, check index 0 but assume it might be USB
            if self._test_camera_index(0):
                self.logger.info("Camera found at index 0 (assuming USB)")
                return True
                
            self.logger.warning("No USB camera detected")
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting USB camera: {e}")
            return False

    def start_camera_with_loading(self):
        """Show loading dialog and start camera initialization."""
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
        if not self.opencv_available:
            self.hide_loading_dialog()
            self.show_camera_error("OpenCV not available - install opencv-python")
            return
            
        try:
            self.logger.info("Starting camera feed...")
            
            # Try to find an available camera
            camera_index = self.find_available_camera()
            
            if camera_index is not None:
                self.camera_thread = CameraThread(camera_index)
                self.camera_thread.changePixmap.connect(self.set_camera_image)
                self.camera_thread.start()
                self.camera_available = True
                self.logger.info(f"Camera started successfully on index {camera_index}")
                
                # Hide loading dialog on success
                self.hide_loading_dialog()
            else:
                self.hide_loading_dialog()
                self.show_camera_error("No USB camera detected")
                
        except Exception as e:
            self.logger.error(f"Error starting camera: {e}")
            self.hide_loading_dialog()
            self.show_camera_error(f"Camera error: {str(e)}")

    def stop_camera(self):
        """Stop the camera feed safely."""
        try:
            # Hide loading dialog if it's still showing
            self.hide_loading_dialog()
            
            # Cancel any ongoing detection
            if hasattr(self, 'detection_thread') and self.detection_thread.isRunning():
                self.detection_thread.terminate()
                self.detection_thread.wait(1000)
            
            # Cancel any ongoing calibration
            if hasattr(self, 'calibration_thread') and self.calibration_thread.isRunning():
                self.calibration_thread.terminate()
                self.calibration_thread.wait(1000)
            
            if self.camera_thread and self.camera_thread.isRunning():
                self.logger.info("Stopping camera thread...")
                
                # Disconnect signal to prevent any remaining frames from being processed
                try:
                    self.camera_thread.changePixmap.disconnect()
                except:
                    pass  # Signal might already be disconnected
                
                # Stop the thread
                self.camera_thread.stop()
                
                # Clear the reference
                self.camera_thread = None
                self.camera_available = False
                self.logger.info("Camera stopped successfully")
            
            # Clear the camera display
            self.setup_camera_placeholder()
                
        except Exception as e:
            self.logger.error(f"Error stopping camera: {e}")
            # Even if there's an error, clear the reference to prevent further issues
            self.camera_thread = None
            self.camera_available = False

    def find_available_camera(self):
        """Find the first available USB camera index (prioritizing USB over CSI)."""
        if not self.opencv_available:
            return None
        
        # Check indices 1-5 first (USB cameras typically start at 1 if CSI is at 0)
        for i in range(1, 6):
            if self._test_camera_index(i):
                self.logger.info(f"Found USB camera at index {i}")
                return i
        
        # If no cameras found at 1+, check index 0 but assume it might be CSI
        if self._test_camera_index(0):
            self.logger.info("Found camera at index 0 (may be CSI or USB)")
            return 0
            
        return None

    def _test_camera_index(self, index):
        """Test if a camera at the given index is accessible."""
        try:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, _ = cap.read()
                cap.release()
                return ret
            return False
        except Exception:
            return False

    def set_camera_image(self, image):
        """Update the camera feed label with new image."""
        try:
            # Add crosshairs if we're on step 3 (camera feed step)
            if hasattr(self, '_current_step') and self._current_step == self.STEP_CAMERA_FEED:
                image = self._add_crosshairs_to_image(image)
            
            # Scale image to fit the label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(image)
            scaled_pixmap = pixmap.scaled(
                self.webCamFeed.size(), 
                QtCore.Qt.KeepAspectRatio, 
                QtCore.Qt.SmoothTransformation
            )
            self.webCamFeed.setPixmap(scaled_pixmap)
            
            # Show that enhanced detection is ready
            if not hasattr(self, '_detection_ready_shown'):
                self._detection_ready_shown = True
                self.logger.info("Enhanced detection system ready - camera feed active")
                
        except Exception as e:
            self.logger.error(f"Error updating camera image: {e}")

    def _add_crosshairs_to_image(self, qimage):
        """Add crosshairs overlay to QImage for centering guidance."""
        try:
            # Convert QImage to QPixmap for drawing
            pixmap = QPixmap.fromImage(qimage)
            
            # Create painter for drawing crosshairs
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            
            # Get image dimensions
            width = pixmap.width()
            height = pixmap.height()
            center_x = width // 2
            center_y = height // 2
            
            # Set up pen for crosshairs
            pen = QtGui.QPen(QtCore.Qt.red)
            pen.setWidth(2)
            pen.setStyle(QtCore.Qt.SolidLine)
            painter.setPen(pen)
            
            # Draw crosshairs
            crosshair_length = min(width, height) // 8  # Crosshair arm length
            
            # Horizontal line
            painter.drawLine(center_x - crosshair_length, center_y, 
                           center_x + crosshair_length, center_y)
            
            # Vertical line  
            painter.drawLine(center_x, center_y - crosshair_length,
                           center_x, center_y + crosshair_length)
            
            # Draw center circle for precise positioning
            pen.setWidth(1)
            painter.setPen(pen)
            circle_radius = 5
            painter.drawEllipse(center_x - circle_radius, center_y - circle_radius,
                              circle_radius * 2, circle_radius * 2)
            
            # Draw outer targeting circle
            pen.setStyle(QtCore.Qt.DashLine)
            painter.setPen(pen)
            outer_radius = crosshair_length // 2
            painter.drawEllipse(center_x - outer_radius, center_y - outer_radius,
                              outer_radius * 2, outer_radius * 2)
            
            painter.end()
            
            # Convert back to QImage
            return pixmap.toImage()
            
        except Exception as e:
            self.logger.error(f"Error adding crosshairs: {e}")
            return qimage  # Return original image if drawing fails

    def show_camera_error(self, message):
        """Show camera error message."""
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

    def move_axis(self, axis, distance):
        """Move the specified axis by the given distance."""
        try:
            if not self.octoprint_client:
                self.logger.error("OctoPrint client not available")
                return

            self.logger.info(f"Moving {axis.upper()} axis by {distance}mm")
            
            # Use jog command similar to control screen
            if axis.lower() == 'x':
                self.octoprint_client.jog(x=distance, speed=2000)
            elif axis.lower() == 'y':
                self.octoprint_client.jog(y=distance, speed=2000)
            else:
                self.logger.error(f"Invalid axis: {axis}")
                
        except Exception as e:
            self.logger.error(f"Error moving {axis} axis: {e}")
            dialog.WarningOk(self, f"Movement error: {str(e)}", overlay=True)

    def _start_ktamv_calibration_direct(self):
        """Start kTAMV camera calibration directly (following original kTAMV approach)."""
        try:
            self.logger.info("Starting kTAMV camera calibration directly...")
            
            # Disable controls during calibration
            self._disable_controls_for_calibration()
            
            # Start calibration in a separate thread to avoid blocking UI
            from PyQt5.QtCore import QThread, pyqtSignal
            
            class CalibrationThread(QThread):
                calibration_complete = pyqtSignal(dict)  # Results dictionary
                calibration_progress = pyqtSignal(str)   # Progress messages
                
                def __init__(self, nozzle_detector, camera_thread, octoprint_client, parent_logger):
                    super().__init__()
                    self.nozzle_detector = nozzle_detector
                    self.camera_thread = camera_thread
                    self.octoprint_client = octoprint_client
                    self.parent_logger = parent_logger
                
                def run(self):
                    try:
                        # Custom logger function for thread-safe logging
                        def thread_logger(message):
                            self.calibration_progress.emit(message)
                            self.parent_logger.info(f"[KTAMV_CALIB] {message}")
                        
                        # Perform kTAMV camera calibration (this includes detection)
                        calib_results = self.nozzle_detector.ktamv_calib_camera(
                            self.camera_thread, 
                            self.octoprint_client,
                            logger_func=thread_logger
                        )
                        
                        # If calibration successful, proceed with nozzle centering
                        if calib_results.get('success', False):
                            thread_logger("Camera calibration successful! Starting nozzle centering...")
                            
                            # Perform nozzle centering
                            center_results = self.nozzle_detector.ktamv_find_nozzle_center(
                                self.camera_thread,
                                self.octoprint_client,
                                target_center=(320, 240),
                                max_iterations=5,
                                tolerance=5,
                                logger_func=thread_logger
                            )
                            
                            # Combine results
                            combined_results = {
                                'calibration': calib_results,
                                'centering': center_results,
                                'overall_success': calib_results.get('success', False) and center_results.get('success', False)
                            }
                        else:
                            # Calibration failed
                            combined_results = {
                                'calibration': calib_results,
                                'centering': {'success': False, 'error': 'Calibration failed'},
                                'overall_success': False
                            }
                        
                        self.calibration_complete.emit(combined_results)
                        
                    except Exception as e:
                        error_results = {
                            'calibration': {'success': False, 'error': f"Thread error: {str(e)}"},
                            'centering': {'success': False, 'error': 'Not attempted'},
                            'overall_success': False
                        }
                        self.calibration_complete.emit(error_results)
            
            # Create and start calibration thread
            self.calibration_thread = CalibrationThread(
                self.nozzle_detector, 
                self.camera_thread, 
                self.octoprint_client,
                self.logger
            )
            self.calibration_thread.calibration_complete.connect(self._on_ktamv_calibration_complete)
            self.calibration_thread.calibration_progress.connect(self._on_calibration_progress)
            self.calibration_thread.start()
            
            # Show progress dialog
            self._show_calibration_progress()
            
        except Exception as e:
            self.logger.error(f"Error starting kTAMV calibration: {e}")
            self._enable_controls_after_calibration()
            dialog.ErrorOk(self, f"Calibration start error:\n{str(e)}", overlay=True)

    def restore_next_button(self):
        """Restore Next button to original state."""
        try:
            self.nextButton.setEnabled(True)
            self.nextButton.setText("Start kTAMV Calibration")
        except Exception as e:
            self.logger.error(f"Error restoring next button: {e}")

    def _disable_controls_for_calibration(self):
        """Disable movement controls and next button during calibration."""
        try:
            # Disable movement buttons
            self.moveXPButton.setEnabled(False)
            self.moveXMButton.setEnabled(False)
            self.moveYPButton.setEnabled(False)
            self.moveYMButton.setEnabled(False)
            
            # Disable next button
            self.nextButton.setEnabled(False)
            self.nextButton.setText("Calibrating...")
            
            self.logger.info("Controls disabled for calibration")
        except Exception as e:
            self.logger.error(f"Error disabling controls: {e}")

    def _enable_controls_after_calibration(self):
        """Re-enable controls after calibration is complete."""
        try:
            # Re-enable movement buttons
            self.moveXPButton.setEnabled(True)
            self.moveXMButton.setEnabled(True)
            self.moveYPButton.setEnabled(True)
            self.moveYMButton.setEnabled(True)
            
            # Re-enable next button
            self.nextButton.setEnabled(True)
            self.nextButton.setText("Next")
            
            self.logger.info("Controls re-enabled after calibration")
        except Exception as e:
            self.logger.error(f"Error enabling controls: {e}")

    def _show_calibration_progress(self):
        """Show calibration progress dialog."""
        try:
            self.calibration_progress_dialog = dialog.dialog(
                self, 
                "Performing kTAMV Camera Calibration...\n\nThis will take a few moments.\nCamera feed will remain live.", 
                buttons=QMessageBox.Cancel,
                overlay=True,
                icon=":/Icons/img/icons/information.png"
            )
            
            # Connect cancel button
            if hasattr(self.calibration_progress_dialog, 'button'):
                cancel_button = self.calibration_progress_dialog.button(QMessageBox.Cancel)
                if cancel_button:
                    cancel_button.clicked.connect(self._cancel_calibration)
            
            self.calibration_progress_dialog.show()
            self.logger.info("Calibration progress dialog shown")
        except Exception as e:
            self.logger.error(f"Error showing calibration progress dialog: {e}")

    def _on_calibration_progress(self, message):
        """Handle calibration progress updates."""
        try:
            # Update progress dialog text if it exists
            if hasattr(self, 'calibration_progress_dialog') and self.calibration_progress_dialog:
                current_text = "Performing kTAMV Camera Calibration...\n\n"
                current_text += f"Latest: {message}\n"
                current_text += "Camera feed will remain live."
                self.calibration_progress_dialog.setText(current_text)
            
            # Also log to console for debugging
            print(f"[KTAMV_CALIB] {message}")
            
        except Exception as e:
            self.logger.error(f"Error updating calibration progress: {e}")

    def _cancel_calibration(self):
        """Cancel ongoing calibration."""
        try:
            if hasattr(self, 'calibration_thread') and self.calibration_thread.isRunning():
                self.calibration_thread.terminate()
                self.calibration_thread.wait(2000)
            
            self._hide_calibration_progress()
            self._enable_controls_after_calibration()
            self.logger.info("Calibration cancelled by user")
        except Exception as e:
            self.logger.error(f"Error cancelling calibration: {e}")

    def _hide_calibration_progress(self):
        """Hide the calibration progress dialog."""
        try:
            if hasattr(self, 'calibration_progress_dialog') and self.calibration_progress_dialog:
                self.calibration_progress_dialog.hide()
                self.calibration_progress_dialog = None
                self.logger.info("Calibration progress dialog hidden")
        except Exception as e:
            self.logger.error(f"Error hiding calibration progress dialog: {e}")

    def _on_ktamv_calibration_complete(self, results):
        """Handle kTAMV calibration completion."""
        try:
            self._hide_calibration_progress()
            
            # Store calibration results
            self.calibration_results = results
            
            if results.get('overall_success', False):
                # Both calibration and centering succeeded
                calib_data = results['calibration']
                center_data = results['centering']
                
                success_msg = (f"kTAMV Calibration Complete!\n\n"
                              f"Camera Offset: ({calib_data['offset_x']:+.1f}, {calib_data['offset_y']:+.1f}) pixels\n"
                              f"Scaling Factor: {calib_data['scaling_factor']:.3f}\n"
                              f"Nozzle Centered in {center_data['iterations']} iterations\n"
                              f"Final Position: {center_data['final_position']}")
                
                dialog.SuccessOk(self, success_msg, overlay=True)
                self.logger.info("kTAMV calibration and centering completed successfully")
                
                # Enable controls with "Next" button to proceed
                self._enable_controls_after_calibration()
                
            else:
                # Calibration or centering failed
                calib_error = results['calibration'].get('error', 'Unknown calibration error')
                center_error = results['centering'].get('error', 'Unknown centering error')
                
                error_msg = f"kTAMV Calibration Failed:\n\nCalibration: {calib_error}\nCentering: {center_error}"
                dialog.ErrorOk(self, error_msg, overlay=True)
                self.logger.error(f"kTAMV calibration failed: {error_msg}")
                
                # Re-enable controls to allow retry
                self.restore_next_button()
                self._enable_controls_after_calibration()
                
        except Exception as e:
            self.logger.error(f"Error handling calibration completion: {e}")
            self.restore_next_button()
            self._enable_controls_after_calibration()

    def on_cancel_clicked(self):
        """Handle Cancel button click - return to calibrate screen."""
        self.logger.info("Cancel button clicked - returning to calibrate screen")
        try:
            # Stop camera before returning
            self.stop_camera()
            
            # Add a small delay to ensure cleanup completes
            QTimer.singleShot(100, self._return_to_calibrate_screen)
            
        except Exception as e:
            self.logger.error(f"Error during cancel: {e}")
            # Still try to return to calibrate screen
            self._return_to_calibrate_screen()

    def _return_to_calibrate_screen(self):
        """Helper method to return to calibrate screen."""
        try:
            self.main_window.calibrate_screen.show_calibrate_screen()
        except Exception as e:
            self.logger.error(f"Error returning to calibrate screen: {e}")

    def setup(self, params=None):
        """Setup method called when screen is activated."""
        self.logger.info("Setting up CameraToolOffsetCalibration")
        # Future: Add any setup logic here
        pass

    def closeEvent(self, event):
        """Clean up when widget is closed."""
        self.stop_camera()
        super().closeEvent(event)

    def __del__(self):
        """Destructor to ensure camera cleanup."""
        try:
            self.hide_loading_dialog()
            self.stop_camera()
        except:
            pass  # Ignore errors during destruction
