from PyQt5 import uic
from PyQt5.QtWidgets import (QWidget, QToolButton, QPushButton, QLineEdit, QLabel,
                             QSpinBox, QFrame, QProgressBar, QSizePolicy, QVBoxLayout)
from PyQt5.QtCore import pyqtSlot
import numpy as np
from ui.custom_widgets import ImageWidget
from PyQt5.QtGui import QImage, QPixmap
from temperatureController.heaterBoard import HeaterBoard
from temperatureController.chamberTemperatureController import ChamberTemperatureController

class ControlScreen(QWidget):
    def __init__(self, main_window, moonraker_api=None):
        super(ControlScreen, self).__init__(main_window)
        self.main_window = main_window
        self.moonraker_api = moonraker_api

        # Load the control screen UI
        try:
            uic.loadUi('src/ui/control_screen/control_screen.ui', self)
            print("ControlScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ControlScreen UI: {e}")

        self.chamberTempSpinBox = self.findChild(QSpinBox, "chamberTempSpinBox")
        self.setChamberTempButton = self.findChild(QPushButton, "setChamberTempButton")
        self.cooldownButton = self.findChild(QPushButton, "cooldownButton")

        # Setup any signal-slot connections and additional initialization here
        self.setChamberTempButton.clicked.connect(lambda: self.update_setpoint(self.chamberTempSpinBox.value()))

        # Replace the QWidget with the custom ImageWidget
        thermal_camera_container = self.findChild(QWidget, "thermalCameraWidget")
        self.thermalCameraWidget = ImageWidget(thermal_camera_container)
        layout = QVBoxLayout(thermal_camera_container)
        layout.addWidget(self.thermalCameraWidget)
        self.thermalCameraWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        # Replace the QWidget with the custom ImageWidget
        rgb_camera_container = self.findChild(QWidget, "rgbCameraWidget")
        self.rgbCameraWidget = ImageWidget(rgb_camera_container)
        layout = QVBoxLayout(rgb_camera_container)
        layout.addWidget(self.rgbCameraWidget)
        self.rgbCameraWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Connect the temperatures_updated signal to the update_thermal_camera_widget slot
        self.main_window.printer_status.temperatures_updated.connect(self.update_thermal_camera_widget)
        self.main_window.printer_status.rgb_frame_updated.connect(self.update_rgb_camera_widget)

        self.cooldownButton.clicked.connect(self.cooldown)

    def update_setpoint(self, value):
        """Update the chamber temperature setpoint in the PrinterStatus model."""
        self.main_window.printer_status.chamberTemperatureSetpoint = value


    @pyqtSlot(np.ndarray, dict)
    def update_thermal_camera_widget(self, frame, temps):
        if frame is not None:
            image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_BGR888)
            self.thermalCameraWidget.setImage(image)

    @pyqtSlot(np.ndarray)
    def update_rgb_camera_widget(self, frame):
        if frame is not None:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.rgbCameraWidget.setImage(image)

    def cooldown(self):
        self.main_window.printer_status.chamberTemperatureSetpoint = 0