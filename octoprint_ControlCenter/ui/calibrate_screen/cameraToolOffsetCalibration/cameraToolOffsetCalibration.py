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

from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel, QMessageBox
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt

from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils import dialog


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
        """Try to connect to USB camera on Linux with enhanced error reporting."""
        if not OPENCV_AVAILABLE:
            self.connectionError.emit("OpenCV not available")
            return False
            
        try:
            # Try to release any existing capture first
            if self.cap:
                self.cap.release()
                self.cap = None
                time.sleep(0.5)  # Give time for camera to be released
            
            # Try V4L2 for Linux USB cameras first, fallback to default
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                self.connectionError.emit(f"USB camera {self.camera_index} not found or in use by another application")
                return False
            
            # Test reading a frame
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.cap.release()
                self.cap = None
                self.connectionError.emit(f"USB camera {self.camera_index} cannot capture frames")
                return False
                
            # Set camera properties for USB cameras on Linux
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # For USB cameras, try to set manual focus if available
            try:
                self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable autofocus for calibration
            except:
                pass  # Some cameras don't support this
            
            # Additional Linux-specific USB camera optimizations
            try:
                # Set buffer size to reduce latency
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                # Set exposure manually if possible for consistent calibration
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual exposure
            except:
                pass  # Some cameras don't support these properties
            
            # Verify properties were set
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            print(f"USB camera {self.camera_index} initialized with V4L2: {actual_width}x{actual_height}")
            
            return True
        except Exception as e:
            if self.cap:
                self.cap.release()
                self.cap = None
            self.connectionError.emit(f"USB camera connection error: {str(e)}")
            return False

    def run(self):
        """Main camera capture loop."""
        if not self.try_connect():
            return
            
        self.running = True
        
        try:
            while self.running:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret and self.running:
                        with QtCore.QMutexLocker(self._frame_lock):
                            self.current_frame = frame.copy()
                            
                            # Apply zoom if needed
                            if self.zoom_factor > 1.0:
                                h, w = frame.shape[:2]
                                center_x, center_y = w // 2, h // 2
                                new_w, new_h = int(w / self.zoom_factor), int(h / self.zoom_factor)
                                x1 = max(0, center_x - new_w // 2)
                                y1 = max(0, center_y - new_h // 2)
                                x2 = min(w, x1 + new_w)
                                y2 = min(h, y1 + new_h)
                                frame = frame[y1:y2, x1:x2]
                                frame = cv2.resize(frame, (w, h))
                            
                            self.display_frame = frame.copy()
                        
                        # Convert to QImage and emit
                        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb_image.shape
                        bytes_per_line = ch * w
                        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                        self.changePixmap.emit(qt_image)
                        
                    time.sleep(0.033)  # ~30 FPS
                else:
                    time.sleep(0.1)
                    
        except Exception as e:
            self.connectionError.emit(f"Camera error: {e}")

    def stop(self):
        """Stop the camera thread."""
        self.running = False
        if self.cap:
            self.cap.release()
        self.wait()  # Wait for thread to finish


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
        self.moveZPButton: QPushButton = self.findChild(QPushButton, "moveZPButton")  # UI has moveZP05Button
        self.moveZMButton: QPushButton = self.findChild(QPushButton, "moveZMButton")
        
        # Navigation buttons
        self.nextButton: QPushButton = self.findChild(QPushButton, "stepNextButton")
        self.cancelButton: QPushButton = self.findChild(QPushButton, "stepCancelButton")

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

        # Connect to position updates for tracking
        if self.model:
            self.model.current_position_updated.connect(self.on_position_updated)


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
            if not self.camera_thread or not self.camera_thread.isRunning():
                # Check for USB camera availability first
                if not self.check_usb_camera_available():
                    dialog.WarningOk(self, "Please connect a USB calibration camera to a USB port and try again", overlay=True)
                    return
                # Start camera with the working method
                self.start_camera()
            
            # Set zoom level
            if self.camera_thread:
                zoom = 2.0 if is_fine else 1.0
                self.camera_thread.set_zoom(zoom)
            
            # Update UI for current step
            step_type = "Fine" if is_fine else "Course"
            self.nextButton.setText("Record Position" if is_fine else "Fine Positioning")
            
            self.logger.info(f"Setup {step_type} positioning for {tool_name}")
            
        except Exception as e:
            self.logger.error(f"Error setting up positioning step: {e}")
            dialog.WarningOk(self, f"Error setting up positioning: {e}")

    def start_camera(self):
        """Initialize and start the camera feed."""
        if not OPENCV_AVAILABLE:
            self.show_camera_error("OpenCV not available - install opencv-python")
            return
            
        try:
            self.logger.info("Starting camera feed...")
            
            # Try to find an available camera
            camera_index = self.find_available_camera()
            
            if camera_index is not None:
                self.camera_thread = CameraThread(camera_index)
                self.camera_thread.changePixmap.connect(self._update_camera_feed)
                self.camera_thread.connectionError.connect(self._on_camera_error)
                self.camera_thread.start()
                self.logger.info(f"Camera started successfully on index {camera_index}")
                
                # Give camera time to initialize
                QTimer.singleShot(1000, self._check_camera_status)
            else:
                self.show_camera_error("No USB camera detected")
                
        except Exception as e:
            self.logger.error(f"Error starting camera: {e}")
            self.show_camera_error(f"Camera error: {str(e)}")

    def show_camera_error(self, message):
        """Show camera error message."""
        try:
            if hasattr(self, 'webCamFeed') and self.webCamFeed:
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
        except Exception as e:
            self.logger.error(f"Error showing camera error: {e}")
    
    def check_usb_camera_available(self):
        """Check if a USB camera is available before starting the camera screen."""
        if not OPENCV_AVAILABLE:
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

    def find_available_camera(self):
        """Find the first available USB camera index (prioritizing USB over CSI)."""
        if not OPENCV_AVAILABLE:
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
        """Test if a camera at the given index is accessible - EXACT ORIGINAL METHOD."""
        try:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, _ = cap.read()
                cap.release()
                return ret
            return False
        except Exception:
            return False

    def _find_usb_cameras(self):
        """Find USB cameras on Linux, excluding CSI cameras."""
        usb_cameras = []
        
        if not OPENCV_AVAILABLE:
            return usb_cameras
        
        # Check /dev/video* devices and filter for USB cameras
        import subprocess
        import os
        
        try:
            # List video devices
            video_devices = []
            for i in range(10):
                device_path = f"/dev/video{i}"
                if os.path.exists(device_path):
                    video_devices.append((i, device_path))
            
            self.logger.info(f"Found video devices: {[d[1] for d in video_devices]}")
            
            # For each video device, check if it's USB
            for index, device_path in video_devices:
                try:
                    # Get device info using v4l2-ctl if available
                    result = subprocess.run(['v4l2-ctl', '--device', device_path, '--info'], 
                                          capture_output=True, text=True, timeout=3)
                    
                    if result.returncode == 0:
                        info = result.stdout.lower()
                        self.logger.debug(f"Device {device_path} info: {info}")
                        
                        # Check if it's a USB device (look for usb in the info)
                        # Exclude CSI cameras explicitly
                        if 'usb' in info and 'csi' not in info and 'bcm2835' not in info:
                            # Double-check by testing OpenCV connection
                            cap = cv2.VideoCapture(index)
                            if cap.isOpened():
                                ret, frame = cap.read()
                                if ret and frame is not None:
                                    usb_cameras.append(index)
                                    self.logger.info(f"Found USB camera at index {index}: {device_path}")
                            cap.release()
                        else:
                            self.logger.debug(f"Skipping {device_path}: not USB or is CSI camera")
                            
                except subprocess.TimeoutExpired:
                    self.logger.debug(f"v4l2-ctl timeout for {device_path}")
                except FileNotFoundError:
                    self.logger.debug("v4l2-ctl not available, using fallback detection")
                    # Fallback: test OpenCV connection and assume USB if working
                    cap = cv2.VideoCapture(index)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            usb_cameras.append(index)
                            self.logger.info(f"Found camera at index {index} (fallback detection)")
                    cap.release()
                except Exception as e:
                    self.logger.debug(f"USB detection failed for {device_path}: {e}")
                    
        except Exception as e:
            self.logger.debug(f"Linux USB camera detection failed: {e}")
            # Final fallback: try standard indices with default backend
            for i in [0, 1, 2]:
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            usb_cameras.append(i)
                            self.logger.info(f"Found camera at index {i} (final fallback)")
                    cap.release()
                except Exception:
                    pass
        
        self.logger.info(f"Detected USB cameras at indices: {usb_cameras}")
        return usb_cameras
    
    def _test_camera_connection(self, camera_index):
        """Test if a USB camera is available at the given index on Linux."""
        if not OPENCV_AVAILABLE:
            return False
            
        try:
            # Use default backend like original working code
            cap = cv2.VideoCapture(camera_index)
            
            if cap.isOpened():
                # Test reading multiple frames to ensure stable connection
                for _ in range(3):
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        cap.release()
                        return False
                    time.sleep(0.1)  # Small delay between test frames
                
                cap.release()
                return True
        except Exception as e:
            self.logger.debug(f"USB camera test failed for index {camera_index}: {e}")
        
        return False
    
    def _check_camera_status(self):
        """Check if camera thread is running properly."""
        if not hasattr(self, 'camera_thread') or not self.camera_thread:
            self.logger.error("Camera thread not created")
            return
            
        if not self.camera_thread.isRunning():
            self.logger.error("Camera thread failed to start")
            self._on_camera_error("Camera thread failed to start")
        else:
            self.logger.info("Camera thread started successfully")

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
        """Handle camera connection errors with improved options."""
        self.logger.error(f"Camera error: {error_msg}")
        
        # Create custom dialog with multiple options
        msg = QMessageBox(self)
        msg.setWindowTitle("Camera Connection Error")
        msg.setText(f"Camera connection failed:\n{error_msg}")
        msg.setInformativeText("What would you like to do?")
        
        retry_button = msg.addButton("Retry Connection", QMessageBox.ActionRole)
        skip_button = msg.addButton("Continue Without Camera", QMessageBox.ActionRole)
        cancel_button = msg.addButton("Cancel Calibration", QMessageBox.RejectRole)
        
        msg.exec_()
        
        if msg.clickedButton() == retry_button:
            # Try to reconnect using working camera detection
            if self.check_usb_camera_available():
                QTimer.singleShot(500, self.start_camera)
            else:
                dialog.WarningOk(self, "Please connect a USB calibration camera and try again", overlay=True)
        elif msg.clickedButton() == skip_button:
            # Continue without camera - show placeholder
            self._show_camera_placeholder()
        else:
            # Cancel calibration
            self.on_cancel_clicked()
    
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
        """Handle next button clicks."""
        try:
            current_step = self._current_step
            
            if current_step == self.STEP_CLEAN_NOZZLES:
                # Move to camera connection step
                self.goto_step(self.STEP_CONNECT_CAMERA)
                
            elif current_step == self.STEP_CONNECT_CAMERA:
                # Move to T0 course positioning
                self.goto_step(self.STEP_POSITION_T0_COURSE)
                
            elif current_step == self.STEP_POSITION_T0_COURSE:
                # Move to T0 fine positioning
                self.goto_step(self.STEP_POSITION_T0_FINE)
                
            elif current_step == self.STEP_POSITION_T0_FINE:
                # Record T0 position and move to T1 setup
                self._record_tool_position(0)
                self._switch_to_tool(1)
                self.goto_step(self.STEP_POSITION_T1_COURSE)
                
            elif current_step == self.STEP_POSITION_T1_COURSE:
                # Move to T1 fine positioning
                self.goto_step(self.STEP_POSITION_T1_FINE)
                
            elif current_step == self.STEP_POSITION_T1_FINE:
                # Record T1 position and show results
                self._record_tool_position(1)
                self.goto_step(self.STEP_RESULTS)
                
            elif current_step == self.STEP_RESULTS:
                # Apply tool offsets and finish
                self._apply_tool_offsets()
                
        except Exception as e:
            self.logger.error(f"Error in next button handler: {e}")
            dialog.WarningOk(self, f"Error proceeding to next step: {e}")

    def _record_tool_position(self, tool):
        """Record the current position for the specified tool."""
        if not self.octoprint_client:
            return
            
        try:
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
            # Stop camera thread
            if self.camera_thread and self.camera_thread.isRunning():
                self.camera_thread.stop()
            
            # Return to main calibrate screen (similar to NozzleChangeWizard pattern)
            self.main_window.calibrate_screen.show_calibrate_screen()
                        
        except Exception as e:
            self.logger.error(f"Error in cancel handler: {e}")
            # Even if there's an error, try to return to calibrate screen
            self.main_window.calibrate_screen.show_calibrate_screen()


    def cleanup(self):
        """Cleanup resources when widget is destroyed."""
        try:
            if self.camera_thread and self.camera_thread.isRunning():
                self.camera_thread.stop()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def closeEvent(self, event):
        """Handle widget close event."""
        self.cleanup()
        super().closeEvent(event)
