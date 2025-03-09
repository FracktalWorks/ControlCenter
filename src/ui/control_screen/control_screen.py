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
    def __init__(self, main_window):
        super(ControlScreen, self).__init__(main_window)
        self.main_window = main_window

        # Load the control screen UI
        try:
            uic.loadUi('src/ui/control_screen/control_screen.ui', self)
            print("ControlScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ControlScreen UI: {e}")

        self.chamberTempSpinBox = self.findChild(QSpinBox, "chamberTempSpinBox")
        self.setChamberTempButton = self.findChild(QPushButton, "setChamberTempButton")
        self.cooldownButton = self.findChild(QPushButton, "cooldownButton")
        self.homeFeedButton = self.findChild(QPushButton, "homeFeedButton")
        self.homeZButton = self.findChild(QPushButton, "homeZButton")
        self.step01Button = self.findChild(QPushButton, "step01Button")
        self.step1Button = self.findChild(QPushButton, "step1Button")
        self.step10Button = self.findChild(QPushButton, "step10Button")
        self.step100Button = self.findChild(QPushButton, "step100Button")
        self.moveZMButton = self.findChild(QPushButton, "moveZMButton")
        self.moveZPButton = self.findChild(QPushButton, "moveZPButton")
        self.moveFeedMButton = self.findChild(QPushButton, "moveFeedMButton")
        self.moveFeedPButton = self.findChild(QPushButton, "moveFeedPButton")



        # Setup any signal-slot connections and additional initialization here
        self.step=10
        self.setChamberTempButton.clicked.connect(lambda: self.update_setpoint(self.chamberTempSpinBox.value()))
        self.cooldownButton.clicked.connect(self.cooldown)
        self.homeFeedButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode("G28 Y\nM400"))
        self.homeZButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode("G28 Z\nM400"))
        self.step01Button.clicked.connect(lambda: self.setStep(0.1))
        self.step1Button.clicked.connect(lambda: self.setStep(1))
        self.step10Button.clicked.connect(lambda: self.setStep(10))
        self.step100Button.clicked.connect(lambda: self.setStep(100))
        self.moveZMButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode(f"G91\nG0 Z-{self.step}\nG90\nM400"))
        self.moveZPButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode(f"G91\nG0 Z{self.step}\nG90\nM400"))
        self.moveFeedMButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode(f"G91\nG0 Y-{self.step}\nG90\nM400"))
        self.moveFeedPButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode(f"G91\nG0 Y{self.step}\nG90\nM400"))
        



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

    def setStep(self, stepRate):
        """
        Sets the class variable "Step" which would be needed for movement and joging
        :param stepRate: step multiplier for movement in the move
        :return: nothing
        """
        try:
            if stepRate == 100:
                self.step100Button.setFlat(True)
                self.step1Button.setFlat(False)
                self.step10Button.setFlat(False)
                self.step01Button.setFlat(False)

                self.step = 100
            if stepRate == 1:
                self.step100Button.setFlat(False)
                self.step1Button.setFlat(True)
                self.step10Button.setFlat(False)
                self.step01Button.setFlat(False)

                self.step = 1
            if stepRate == 10:
                self.step100Button.setFlat(False)
                self.step1Button.setFlat(False)
                self.step10Button.setFlat(True)
                self.step01Button.setFlat(False)
                self.step = 10
            if stepRate == 0.1:
                self.step100Button.setFlat(False)
                self.step1Button.setFlat(False)
                self.step10Button.setFlat(False)
                self.step01Button.setFlat(True)
                self.step = 0.1
        except Exception as e:
            print(f"Error in setting step: {e}")
