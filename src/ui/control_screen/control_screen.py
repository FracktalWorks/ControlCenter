from PyQt5 import uic
from PyQt5.QtWidgets import (QWidget, QToolButton, QPushButton, QLineEdit, QLabel,
                             QSpinBox, QFrame, QProgressBar, QSizePolicy, QVBoxLayout, QMessageBox)
from PyQt5.QtCore import pyqtSlot
import numpy as np
from ui.custom_widgets import ImageWidget
from PyQt5.QtGui import QImage, QPixmap
from temperatureController.heaterBoard import HeaterBoard
from temperatureController.chamberTemperatureController import ChamberTemperatureController
from utils.helpers import run_async

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

        self.homeBuildModuleButton = self.findChild(QPushButton, "homeBuildModuleButton")
        self.undockButton = self.findChild(QPushButton, "undockButton")
        self.dockButton = self.findChild(QPushButton, "dockButton")
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
        self.setBedTempButton = self.findChild(QPushButton, "setBedTempButton")
        self.bedTempSpinBox = self.findChild(QSpinBox, "bedTempSpinBox")
        self.setVolumeTempButton = self.findChild(QPushButton, "setVolumeTempButton")
        self.volumeTempSpinBox = self.findChild(QSpinBox, "volumeTempSpinBox")

        self.homeRecoaterButton = self.findChild(QPushButton, "homeRecoaterButton")
        self.recoatButton = self.findChild(QPushButton, "recoatButton")
        self.initialLevellingRecoatButton = self.findChild(QPushButton, "initialLevellingRecoatButton")
        self.heatedBufferRecoatButton = self.findChild(QPushButton, "heatedBufferRecoatButton")
        self.doseRecoatLayerButton = self.findChild(QPushButton, "doseRecoatLayerButton")

        self.stopProcessButton = self.findChild(QPushButton, "stopProcessButton")
        self.recoaterProgressBar = self.findChild(QProgressBar, "recoaterProgressBar")

        # Setup any signal-slot connections and additional initialization here
        self.step = 10
        self.setStep(10)
        self.homeBuildModuleButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode("G28 Z Y\nM400"))
        self.undockButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode("goDown\nM400"))
        self.dockButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode("liftUp\nM400"))
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
        self.setBedTempButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode(f"SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET={self.bedTempSpinBox.value()}"))
        self.setVolumeTempButton.clicked.connect(self.setVolumeHeaterTemp)
        self.initialLevellingRecoatButton.clicked.connect(self.confirm_initial_levelling_recoat)
        self.heatedBufferRecoatButton.clicked.connect(self.confirm_heated_buffer_recoat)
        self.doseRecoatLayerButton.clicked.connect(self.dose_recoat_layer)
        self.stopProcessButton.clicked.connect(self.stop_process)

        self.homeRecoaterButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode("homeRecoater"))
        self.recoatButton.clicked.connect(lambda: self.main_window.moonraker_api.send_gcode("recoat"))

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

        # Flag to control the recoat process
        self.recoat_running = False

    def confirm_initial_levelling_recoat(self):
        """Show a confirmation dialog before starting the initial levelling recoat."""
        reply = QMessageBox.question(self, 'Confirmation',
                                     'Ensure that the build module is moved to the starting position before starting the initial levelling recoat. Do you want to proceed?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.recoat_running = True
            self.initialLevellingRecoat()

    @run_async
    def initialLevellingRecoat(self):
        '''
        This function is used to perform the initial levelling recoat
        takes input from the layer height and the initial levelling height from the paramerters screen and calculates how many
        time to run the recoater and move the Z and Y axis.
        Sequence: we start by asuming that the Z axis is at zero position, and the feedAxis/Y axis is at its starting positon filled with powder.
        after evey recoat the z axis goes up by the layer height and the feed axis goes down by the layer height, this is repeated until the
        initial levelling height is reached.
        '''
        layerHeight = self.main_window.parameters_screen.layerHeightLineEdit.value()
        initialLevellingHeight = self.main_window.parameters_screen.initialLevellingHeightLineEdit.value()
        recoatCount = int(initialLevellingHeight / layerHeight)
        for i in range(recoatCount):
            if not self.recoat_running:
                break
            self.main_window.moonraker_api.send_gcode("homeRecoater")
            self.main_window.moonraker_api.send_gcode(f"G91\nG0 Z{layerHeight}\nG90\nM400")
            self.main_window.moonraker_api.send_gcode(f"G91\nG0 Y-{layerHeight}\nG90\nM400")
            self.main_window.moonraker_api.send_gcode("recoat\nM400")
            self.main_window.moonraker_api.send_gcode("homeRecoater\nM400")
            # Update progress bar
            progress = int((i + 1) / recoatCount * 100)
            self.recoaterProgressBar.setValue(progress)

    def confirm_heated_buffer_recoat(self):
        """Show a confirmation dialog before starting the heated buffer recoat."""
        reply = QMessageBox.question(self, 'Confirmation',
                                     'Ensure that the build module is moved to the starting position before starting the heated buffer recoat. Do you want to proceed?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.recoat_running = True
            self.heatedBufferRecoat()

    @run_async
    def heatedBufferRecoat(self):
        '''
        This function is used to perform the heated buffer recoat
        takes input from the layer height and the heated buffer height from the paramerters screen and calculates how many
        time to run the recoater and move the Z and Y axis.
        Sequence: we start by asuming that the Z axis is at zero position, and the feedAxis/Y axis is at its starting positon filled with powder.
        after evey recoat the z axis goes up by the layer height and the feed axis goes down by the layer height, this is repeated until the
        heated buffer height is reached.
        '''
        layerHeight = self.main_window.parameters_screen.layerHeightLineEdit.value()
        heatedBufferHeight = self.main_window.parameters_screen.heatedBufferHeightLineEdit.value()
        recoatCount = int(heatedBufferHeight / layerHeight)
        for i in range(recoatCount):
            if not self.recoat_running:
                break
            self.main_window.moonraker_api.send_gcode("homeRecoater")
            self.main_window.moonraker_api.send_gcode(f"G91\nG0 Z{layerHeight}\nG90\nM400")
            self.main_window.moonraker_api.send_gcode(f"G91\nG0 Y-{layerHeight}\nG90\nM400")
            self.main_window.moonraker_api.send_gcode("recoat\nM400")
            self.main_window.moonraker_api.send_gcode("homeRecoater\nM400")
            # Update progress bar
            progress = int((i + 1) / recoatCount * 100)
            self.recoaterProgressBar.setValue(progress)

    @run_async
    def dose_recoat_layer(self):
        '''
        This function is used to perform a single recoat using the layer height from the parameters screen.
        '''
        layerHeight = self.main_window.parameters_screen.layerHeightLineEdit.value()
        self.main_window.moonraker_api.send_gcode("homeRecoater")
        self.recoaterProgressBar.setValue(0)
        self.main_window.moonraker_api.send_gcode(f"G91\nG0 Z{layerHeight}\nG90\nM400")
        self.recoaterProgressBar.setValue(25)
        self.main_window.moonraker_api.send_gcode(f"G91\nG0 Y-{layerHeight}\nG90\nM400")
        self.recoaterProgressBar.setValue(50)
        self.main_window.moonraker_api.send_gcode("recoat\nM400")
        self.recoaterProgressBar.setValue(75)
        self.main_window.moonraker_api.send_gcode("homeRecoater\nM400")
        self.recoaterProgressBar.setValue(100)

    def stop_process(self):
        """Stop the recoat process."""
        self.recoat_running = False

    def setVolumeHeaterTemp(self):
        self.main_window.moonraker_api.send_gcode(f"SET_HEATER_TEMPERATURE HEATER=bed_heater_front TARGET={self.volumeTempSpinBox.value()}")
        self.main_window.moonraker_api.send_gcode(f"SET_HEATER_TEMPERATURE HEATER=bed_heater_left TARGET={self.volumeTempSpinBox.value()}")
        self.main_window.moonraker_api.send_gcode(f"SET_HEATER_TEMPERATURE HEATER=bed_heater_right TARGET={self.volumeTempSpinBox.value()}")

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