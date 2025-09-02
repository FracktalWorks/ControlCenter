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
from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils.dependency_manager import SimplifiedDependencyChecker
from utils import dialog

# Try to import OpenCV, using the dependency checker
cv2 = SimplifiedDependencyChecker.import_with_install(
    'cv2', 
    'opencv-python', 
    'Computer vision library for camera functionality'
)


class CameraThread(QThread):
    """Thread for handling camera capture to avoid blocking the UI."""
    changePixmap = pyqtSignal(QImage)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = False

    def run(self):
        """Main camera capture loop."""
        if cv2 is None:
            return  # Cannot run without OpenCV
            
        cap = cv2.VideoCapture(self.camera_index)
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.running = True
        
        while self.running:
            ret, frame = cap.read()
            if ret:
                # Convert the image to RGB format
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                
                # Create QImage
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                
                # Emit the image
                self.changePixmap.emit(qt_image)
            
            # Control frame rate
            self.msleep(33)  # ~30 FPS
        
        cap.release()

    def stop(self):
        """Stop the camera thread."""
        self.running = False
        self.quit()
        self.wait()


class CameraToolOffsetCalibration(QWidget):
    """Camera Tool Offset Calibration widget.

    Responsibilities:
    - Load and bind UI elements
    - Handle USB camera feed display
    - Provide 1mm movement controls
    - Basic navigation between calibration screen
    """

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.octoprint_client = getattr(main_window, "octoprint_client", None)
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing CameraToolOffsetCalibration")

        # Camera related attributes
        self.camera_thread = None
        self.camera_available = False
        self.opencv_available = cv2 is not None
        
        # Check if OpenCV is available
        if not self.opencv_available:
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
        
        # Camera display
        self.webCamFeed: QLabel = self.findChild(QLabel, "webCamFeed")
        
        # Movement buttons
        self.moveXPButton: QPushButton = self.findChild(QPushButton, "moveXPButton")
        self.moveXMButton: QPushButton = self.findChild(QPushButton, "moveXMButton")
        self.moveYPButton: QPushButton = self.findChild(QPushButton, "moveYPButton")
        self.moveYMButton: QPushButton = self.findChild(QPushButton, "moveYMButton")
        
        # Navigation buttons
        self.nextButton: QPushButton = self.findChild(QPushButton, "step1NextButton")
        self.cancelButton: QPushButton = self.findChild(QPushButton, "step1CancelButton")

        # Validate required elements
        required = [
            self.stackedWidget, self.stepLabel, self.webCamFeed,
            self.moveXPButton, self.moveXMButton, self.moveYPButton, self.moveYMButton,
            self.nextButton, self.cancelButton
        ]
        check_ui_elements(self, required, "CameraToolOffsetCalibration")

        # Set up movement step (1mm)
        self.movement_step = 1.0

        # Wire signals
        self.nextButton.clicked.connect(self.on_next_clicked)
        self.cancelButton.clicked.connect(self.on_cancel_clicked)
        
        # Movement button connections (1mm steps)
        self.moveXPButton.clicked.connect(lambda: self.move_axis('x', self.movement_step))
        self.moveXMButton.clicked.connect(lambda: self.move_axis('x', -self.movement_step))
        self.moveYPButton.clicked.connect(lambda: self.move_axis('y', self.movement_step))
        self.moveYMButton.clicked.connect(lambda: self.move_axis('y', -self.movement_step))

        # Initialize camera feed placeholder
        self.setup_camera_placeholder()

        self.logger.info("CameraToolOffsetCalibration initialized successfully")

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
        """Start camera when widget is shown."""
        super().showEvent(event)
        self.start_camera()

    def hideEvent(self, event):
        """Stop camera when widget is hidden."""
        super().hideEvent(event)
        self.stop_camera()

    def start_camera(self):
        """Initialize and start the camera feed."""
        if not self.opencv_available:
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
            else:
                self.show_camera_error("No USB camera detected")
                
        except Exception as e:
            self.logger.error(f"Error starting camera: {e}")
            self.show_camera_error(f"Camera error: {str(e)}")

    def stop_camera(self):
        """Stop the camera feed."""
        try:
            if self.camera_thread and self.camera_thread.isRunning():
                self.camera_thread.stop()
                self.camera_thread = None
                self.camera_available = False
                self.logger.info("Camera stopped")
        except Exception as e:
            self.logger.error(f"Error stopping camera: {e}")

    def find_available_camera(self):
        """Find the first available camera index."""
        if not self.opencv_available or cv2 is None:
            return None
            
        for i in range(5):  # Check first 5 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                cap.release()
                if ret:
                    return i
        return None

    def set_camera_image(self, image):
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

    def on_next_clicked(self):
        """Handle Next button click - currently does nothing as requested."""
        self.logger.info("Next button clicked (no action configured)")
        # Future: Implement calibration logic here

    def on_cancel_clicked(self):
        """Handle Cancel button click - return to calibrate screen."""
        self.logger.info("Cancel button clicked - returning to calibrate screen")
        try:
            # Stop camera before returning
            self.stop_camera()
            # Return to main calibrate screen
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
