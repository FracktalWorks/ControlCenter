#TBD: incase a gcode is yet to be executed, block the thread from executing another gcode in moonraker api

from PyQt5 import uic
from PyQt5.QtWidgets import (QWidget, QPushButton, QSpinBox, QProgressBar, QSizePolicy, QVBoxLayout, QMessageBox, QLabel)
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QTimer
from PyQt5.QtGui import QImage
import numpy as np
from ui.custom_widgets import ImageWidget
from utils.helpers import run_async
import time
from processAutomationController.processAutomationController import ProcessAutomationController

class ControlScreen(QWidget):
    progress_update_signal = pyqtSignal(int)

    def __init__(self, main_window):
        super(ControlScreen, self).__init__(main_window)
        self.main_window = main_window

        # Load the control screen UI
        self.load_ui()

        # Initialize UI elements
        self.initialize_ui_elements()

        # Initialize ProcessAutomationController
        self.process_automation_controller = ProcessAutomationController(main_window)

        # # Setup signal-slot connections
        # self.setup_connections()

        # # Replace QWidget with custom ImageWidget
        # self.setup_custom_widgets()

        # # Connect signals to slots
        # self.connect_signals()

        self.motion_control_buttons = [
            self.homeBuildModuleButton, self.undockButton, self.dockButton,
            self.homeFeedButton, self.homeZButton, self.step01Button,
            self.step1Button, self.step10Button, self.step100Button,
            self.moveZMButton, self.moveZPButton, self.moveFeedMButton,
            self.moveFeedPButton, self.setBedTempButton, self.setVolumeTempButton,
            self.homeRecoaterButton, self.recoatButton, self.moveToStartingPositionButton,
            self.prepareForPartRemovalButton, self.initialLevellingRecoatButton,
            self.heatedBufferRecoatButton, self.doseRecoatLayerButton, self.preparePowderLoadingButton,
            self.homeXYButton, self.moveXMButton, self.moveXPButton, self.moveYMButton, self.moveYPButton,
        ]

        # Connect the scancard status update signal to the label update slot
        self.main_window.printer_status.scancard_status_updated.connect(self.update_laser_status)

    def load_ui(self):
        try:
            uic.loadUi('src/ui/control_screen/control_screen.ui', self)
            print("ControlScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ControlScreen UI: {e}")

    def initialize_ui_elements(self):
        self.chamberTempSpinBox = self.findChild(QSpinBox, "chamberTempSpinBox")
        self.setChamberTempButton = self.findChild(QPushButton, "setChamberTempButton")
        self.cooldownButton = self.findChild(QPushButton, "cooldownButton")
        self.homeBuildModuleButton = self.findChild(QPushButton, "homeBuildModuleButton")
        self.undockButton = self.findChild(QPushButton, "undockButton")
        self.dockButton = self.findChild(QPushButton, "dockButton")
        self.homeFeedButton = self.findChild(QPushButton, "homeFeedButton")
        self.step01Button = self.findChild(QPushButton, "step01Button")
        self.step1Button = self.findChild(QPushButton, "step1Button")
        self.step10Button = self.findChild(QPushButton, "step10Button")
        self.step100Button = self.findChild(QPushButton, "step100Button")

        # Z movements
        self.homeZButton = self.findChild(QPushButton, "homeZButton")
        self.moveZMButton = self.findChild(QPushButton, "moveZMButton")
        self.moveZPButton = self.findChild(QPushButton, "moveZPButton")

        # XY movements
        self.homeXYButton = self.findChild(QPushButton, "homeXYButton")
        self.moveXMButton = self.findChild(QPushButton, "moveXMButton")
        self.moveXPButton = self.findChild(QPushButton, "moveXPButton")
        self.moveYMButton = self.findChild(QPushButton, "moveYMButton")
        self.moveYPButton = self.findChild(QPushButton, "moveYPButton")

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
        self.preparePowderLoadingButton = self.findChild(QPushButton, "preparePowderLoadingButton")

        self.stopProcessButton = self.findChild(QPushButton, "stopProcessButton")
        self.recoaterProgressBar = self.findChild(QProgressBar, "recoaterProgressBar")

        self.moveToStartingPositionButton = self.findChild(QPushButton, "moveToStartingPositionButton") 
        self.prepareForPartRemovalButton = self.findChild(QPushButton, "prepareForPartRemovalButton")  

        self.maxTempLabel = self.findChild(QLabel, "maxTempLabel")  # Find the maxTempLabel

        # Initialize scanCardStatusLabel
        self.scanCardStatusLabel = self.findChild(QLabel, "scanCardStatusLabel")

        # Initialize start and stop marking buttons
        self.startMarkingButton = self.findChild(QPushButton, "startMarkingButton")
        self.stopMarkingButton = self.findChild(QPushButton, "stopMarkingButton")

    # def setup_connections(self):
    #     self.step = 10
    #     self.setStep(10)
    #     self.homeBuildModuleButton.clicked.connect(lambda: self.run_async_send_gcode("G28 Z Y\nM400"))
    #     self.undockButton.clicked.connect(lambda: self.run_async_send_gcode("goDown\nM400"))
    #     self.dockButton.clicked.connect(lambda: self.run_async_send_gcode("liftUp\nM400"))
    #     self.setChamberTempButton.clicked.connect(lambda: self.update_setpoint(self.chamberTempSpinBox.value()))
    #     self.cooldownButton.clicked.connect(self.cooldown)
    #     self.homeFeedButton.clicked.connect(lambda: self.run_async_send_gcode("G28 Y\nM400"))

    #     # Z movements
    #     self.homeZButton.clicked.connect(lambda: self.run_async_send_gcode("N50 G01 Z0 F500"))
    #     self.moveZMButton.clicked.connect(lambda: self.run_async_send_gcode("N60 G01 Z-10 F200"))
    #     self.moveZPButton.clicked.connect(lambda: self.run_async_send_gcode("N70 G01 Z10 F200"))
       
    #     # XY movements
        
    #     self.homeXYButton.clicked.connect(lambda: self.run_async_send_gcode("N70 G01 X0 Y0 F200"))
    #     self.moveXMButton.clicked.connect(lambda: self.run_async_send_gcode("N20 G01 X-10 F500"))
    #     self.moveXPButton.clicked.connect(lambda: self.run_async_send_gcode("N30 G01 X10 F500"))
    #     self.moveYMButton.clicked.connect(lambda: self.run_async_send_gcode("N40 G01 Y-10 F500"))
    #     self.moveYPButton.clicked.connect(lambda: self.run_async_send_gcode("N10 G01 Y10 F500"))

    #     self.step01Button.clicked.connect(lambda: self.setStep(0.1))
    #     self.step1Button.clicked.connect(lambda: self.setStep(1))
    #     self.step10Button.clicked.connect(lambda: self.setStep(10))
    #     self.step100Button.clicked.connect(lambda: self.setStep(100))
      
    #     self.moveFeedMButton.clicked.connect(lambda: self.run_async_send_gcode(f"G91\nG0 Y-{self.step}\nG90\nM400"))
    #     self.moveFeedPButton.clicked.connect(lambda: self.run_async_send_gcode(f"G91\nG0 Y{self.step}\nG90\nM400"))
    #     self.setBedTempButton.clicked.connect(lambda: self.run_async_send_gcode(f"SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET={self.bedTempSpinBox.value()}"))
    #     self.setVolumeTempButton.clicked.connect(self.setVolumeHeaterTemp)
    #     self.initialLevellingRecoatButton.clicked.connect(self.confirm_initial_levelling_recoat)
    #     self.heatedBufferRecoatButton.clicked.connect(self.confirm_heated_buffer_recoat)
    #     self.doseRecoatLayerButton.clicked.connect(lambda: self.run_async_process(self.process_automation_controller.dose_recoat_layer))
    #     self.preparePowderLoadingButton.clicked.connect(lambda: self.run_async_process(self.process_automation_controller.prepare_powder_loading))
    #     self.stopProcessButton.clicked.connect(self.process_automation_controller.stop_process)
    #     self.homeRecoaterButton.clicked.connect(lambda: self.run_async_send_gcode("homeRecoater"))
    #     self.recoatButton.clicked.connect(lambda: self.run_async_send_gcode("recoat"))
    #     self.moveToStartingPositionButton.clicked.connect(lambda: self.run_async_process(self.process_automation_controller.move_to_starting_sequence))
    #     self.prepareForPartRemovalButton.clicked.connect(lambda: self.run_async_process(self.process_automation_controller.prepare_for_part_removal_sequence))

        # # Connect start and stop marking buttons to Scancard functions
        # self.startMarkingButton.clicked.connect(self.main_window.scancard.start_mark)
        # self.stopMarkingButton.clicked.connect(self.main_window.scancard.stop_mark)

    @run_async
    def run_async_send_gcode(self, gcode):
        self.main_window.moonraker_api.send_gcode(gcode)

    @run_async
    def run_async_process(self, process_method):
        process_method()

    def setup_custom_widgets(self):
        thermal_camera_container = self.findChild(QWidget, "thermalCameraWidget")
        self.thermalCameraWidget = ImageWidget(thermal_camera_container)
        layout = QVBoxLayout(thermal_camera_container)
        layout.addWidget(self.thermalCameraWidget)
        self.thermalCameraWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        rgb_camera_container = self.findChild(QWidget, "rgbCameraWidget")
        self.rgbCameraWidget = ImageWidget(rgb_camera_container)
        layout = QVBoxLayout(rgb_camera_container)
        layout.addWidget(self.rgbCameraWidget)
        self.rgbCameraWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def connect_signals(self):
        self.main_window.printer_status.temperatures_updated.connect(self.update_thermal_camera_widget)
        self.main_window.printer_status.rgb_frame_updated.connect(self.update_rgb_camera_widget)
        self.main_window.printer_status.maxtemp_updated.connect(self.update_max_temp_label)  # Connect the maxtemp_updated signal

    @pyqtSlot(float)
    def update_max_temp_label(self, max_temp):
        """Slot to update the text of maxTempLabel with the maximum temperature."""
        self.maxTempLabel.setText(f"Max Temp: {max_temp:.2f}°C")

    def set_motion_control_buttons_enabled(self, enabled):
        """Enable or disable motion control buttons."""
        for button in self.motion_control_buttons:
            button.setEnabled(enabled)

    def confirm_initial_levelling_recoat(self):
        """Show a confirmation dialog before starting the initial levelling recoat."""
        reply = QMessageBox.question(self, 'Confirmation',
                                     'Ensure that the build module is moved to the starting position and recoater is homed before starting the initial levelling recoat. Do you want to proceed?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.process_automation_controller.process_running = True
            self.set_motion_control_buttons_enabled(False)
            self.run_async_process(self.process_automation_controller.initialLevellingRecoat)

    def confirm_heated_buffer_recoat(self):
        """Show a confirmation dialog before starting the heated buffer recoat."""
        reply = QMessageBox.question(self, 'Confirmation',
                                     'Ensure that the build module is moved to the starting position and recoater is homed  before starting the heated buffer recoat. Do you want to proceed?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.process_automation_controller.process_running = True
            self.set_motion_control_buttons_enabled(False)
            self.run_async_process(self.process_automation_controller.heatedBufferRecoat)

    def setVolumeHeaterTemp(self):
        """Set the volume heater temperature."""
        target_temp = self.volumeTempSpinBox.value()
        self.main_window.moonraker_api.send_gcode(f"SET_HEATER_TEMPERATURE HEATER=bed_heater_front TARGET={target_temp}")
        self.main_window.moonraker_api.send_gcode(f"SET_HEATER_TEMPERATURE HEATER=bed_heater_left TARGET={target_temp}")
        self.main_window.moonraker_api.send_gcode(f"SET_HEATER_TEMPERATURE HEATER=bed_heater_right TARGET={target_temp}")

    def update_setpoint(self, value):
        """Update the chamber temperature setpoint in the PrinterStatus model."""
        self.main_window.printer_status.chamberTemperatureSetpoint = value
        print(f"Chamber temperature setpoint updated to {value}")

    @pyqtSlot(np.ndarray, dict)
    def update_thermal_camera_widget(self, frame, temps):
        """Update the thermal camera widget."""
        if frame is not None:
            image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_BGR888)
            self.thermalCameraWidget.setImage(image)

    @pyqtSlot(np.ndarray)
    def update_rgb_camera_widget(self, frame):
        """Update the RGB camera widget."""
        if frame is not None:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.rgbCameraWidget.setImage(image)

    def cooldown(self):
        """Cooldown the chamber."""
        self.main_window.printer_status.chamberTemperatureSetpoint = 0
        self.chamberTempSpinBox.setValue(0)

    def setStep(self, stepRate):
        """Set the step rate for movement."""
        try:
            self.step100Button.setFlat(stepRate == 100)
            self.step1Button.setFlat(stepRate == 1)
            self.step10Button.setFlat(stepRate == 10)
            self.step01Button.setFlat(stepRate == 0.1)
            self.step = stepRate
        except Exception as e:
            print(f"Error in setting step: {e}")

    def start_marking(self):
        """Start the marking process."""
        self.main_window.start_scancard_mark()

    def stop_marking(self):
        """Stop the marking process."""
        self.main_window.stop_scancard_mark()

    def update_laser_status(self, status):
        """Update the laser status label."""
        self.scanCardStatusLabel.setText(f"Laser Status: {status}")


def replace_placeholders(sequence: str, printer_status) -> str:
    """Replace placeholders in the sequence with actual values from the printer_status model."""
    placeholders = {
        "{layerHeight}": printer_status.layerHeight,
        "{initialLevellingHeight}": printer_status.initialLevellingHeight,
        "{heatedBufferHeight}": printer_status.heatedBufferHeight,
        "{powderLoadingExtraHeightGap}": printer_status.powderLoadingExtraHeightGap,
        "{bedTemperature}": printer_status.bedTemperature,
        "{volumeTemperature}": printer_status.volumeTemperature,
        "{chamberTemperature}": printer_status.chamberTemperature,
        "{p}": printer_status.p,
        "{i}": printer_status.i,
        "{d}": printer_status.d,
        "{powderLoadingHeight}": printer_status.initialLevellingHeight + 2 * printer_status.heatedBufferHeight + printer_status.partHeight,
        "{dosingHeight}": printer_status.dosingHeight  # Add dosingHeight
    }
    for placeholder, value in placeholders.items():
        sequence = sequence.replace(placeholder, str(value))
    return sequence