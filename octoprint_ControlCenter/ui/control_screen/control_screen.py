import time

import os
from PyQt5 import uic
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QWidget, QPushButton, QSpinBox, QTabWidget, QToolButton
from utils.helpers import check_ui_elements
from ui.control_screen.changeFilament.changeFilament import ChangeFilament
from utils.logger import get_logger
from utils import dialog

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


logger = get_logger(__name__)

class ControlScreen(QWidget):
    def __init__(self, main_window):
        super(ControlScreen, self).__init__()
        self.main_window = main_window
        self.octoprint_client = main_window.octoprint_client

        # Use centralized logger
        self.logger = get_logger(self.__class__.__name__)

        # Load the UI
        try:
            # Use relative path from the current module's directory
            ui_file_path = os.path.join(os.path.dirname(__file__), "control_screen.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("ControlScreen UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load ControlScreen UI file: {e}", exc_info=True)

        # Initialize UI components
        self.controlTabWidget = self.findChild(QTabWidget, "controlTabWidget")
        self.controlBackButton = self.findChild(QPushButton, "controlBackButton")

        # Tab widgets
        self.feedRateTab = self.findChild(QWidget, "feedRateTab")
        self.temperatureTab = self.findChild(QWidget, "temperatureTab")
        self.motionTab = self.findChild(QWidget, "motionTab")
        self.filamentTab = self.findChild(QWidget, "filamentTab")

        # Feed rate controls
        self.feedRateSpinBox = self.findChild(QSpinBox, "feedRateSpinBox")
        self.setFeedRateButton = self.findChild(QPushButton, "setFeedRateButton")
        self.moveZPBabyStep = self.findChild(QPushButton, "moveZPBabyStep")
        self.moveZMBabyStep = self.findChild(QPushButton, "moveZMBabyStep")

        # Temperature controls
        self.fanOnButton = self.findChild(QPushButton, "fanOnButton")
        self.fanOffButton = self.findChild(QPushButton, "fanOffButton")
        self.cooldownButton = self.findChild(QPushButton, "cooldownButton")
        self.toolTempSpinBox = self.findChild(QSpinBox, "toolTempSpinBox")
        self.setToolTempButton = self.findChild(QPushButton, "setToolTempButton")
        self.bedTempSpinBox = self.findChild(QSpinBox, "bedTempSpinBox")
        self.setBedTempButton = self.findChild(QPushButton, "setBedTempButton")
        self.toolToggleTemperatureButton = self.findChild(QPushButton, "toolToggleTemperatureButton")
        self.tool180PreheatButton = self.findChild(QPushButton, "tool180PreheatButton")
        self.tool250PreheatButton = self.findChild(QPushButton, "tool250PreheatButton")
        self.bed60PreheatButton = self.findChild(QPushButton, "bed60PreheatButton")
        self.bed100PreheatButton = self.findChild(QPushButton, "bed100PreheatButton")

        # Motion controls
        self.step1mmButton = self.findChild(QPushButton, "step1mmButton")
        self.step10mmButton = self.findChild(QPushButton, "step10mmButton")
        self.step100mmButton = self.findChild(QPushButton, "step100mmButton")
        self.moveXPButton = self.findChild(QPushButton, "moveXPButton")
        self.moveXMButton = self.findChild(QPushButton, "moveXMButton")
        self.moveYPButton = self.findChild(QPushButton, "moveYPButton")
        self.moveYMButton = self.findChild(QPushButton, "moveYMButton")
        self.motorOffButton = self.findChild(QPushButton, "motorOffButton")
        self.homeXYButton = self.findChild(QPushButton, "homeXYButton")
        self.moveZMButton = self.findChild(QPushButton, "moveZMButton")
        self.moveZPButton = self.findChild(QPushButton, "moveZPButton")
        self.homeZButton = self.findChild(QPushButton, "homeZButton")
        self.toolToggleMotionButton = self.findChild(QPushButton, "toolToggleMotionButton")
        self.extruderButton = self.findChild(QPushButton, "extruderButton")
        self.retractButton = self.findChild(QPushButton, "retractButton")

        # Filament controls
        self.flowRateSpinBox = self.findChild(QSpinBox, "flowRateSpinBox")
        self.setFlowRateButton = self.findChild(QPushButton, "setFlowRateButton")

        # Change Filament and Filament Sensor controls
        self.changeFilamentButton = self.findChild(QToolButton, "changeFilamentButton")
        self.toggleFilamentSensorButton = self.findChild(QToolButton, "toggleFilamentSensorButton")

        # Validate UI components
        check_ui_elements(self, [
            self.controlTabWidget, self.controlBackButton, self.feedRateSpinBox,
            self.setFeedRateButton, self.moveZPBabyStep, self.moveZMBabyStep,
            self.fanOnButton, self.fanOffButton, self.cooldownButton,
            self.toolTempSpinBox, self.setToolTempButton, self.bedTempSpinBox,
            self.setBedTempButton, self.step1mmButton, self.step10mmButton,
            self.step100mmButton, self.moveXPButton, self.moveXMButton,
            self.moveYPButton, self.moveYMButton, self.flowRateSpinBox,
            self.setFlowRateButton, self.changeFilamentButton, self.toggleFilamentSensorButton,
            self.feedRateTab, self.temperatureTab, self.motionTab, self.filamentTab
        ], "ControlScreen")

        # Initialize sub-screens
        self.screens = {}
        self._initialize_sub_screens()

        # set the active extruder to 0 initially
        self.setActiveExtruder(0)  # Default to extruder 0

        # Feed Rate Buttons Signal Connections
        self.controlBackButton.clicked.connect(lambda: self.main_window.switch_to_home_screen())
        self.setFeedRateButton.clicked.connect(
            lambda: self.octoprint_client.feedrate(self.feedRateSpinBox.value())
        )
        self.moveZPBabyStep.clicked.connect(
            lambda: self.octoprint_client.gcode(command='M290 Z0.025')
        )
        self.moveZMBabyStep.clicked.connect(
            lambda: self.octoprint_client.gcode(command='M290 Z-0.025')
        )

        # Temperature Buttons Signal Connections
        self.fanOnButton.clicked.connect(lambda: self.octoprint_client.gcode(command='M106 S255'))
        self.fanOffButton.clicked.connect(lambda: self.octoprint_client.gcode(command='M107'))
        self.cooldownButton.clicked.connect(self.coolDownAction)
        self.setToolTempButton.clicked.connect(self.setToolTemp)
        self.setBedTempButton.clicked.connect(lambda: self.octoprint_client.setBedTemperature(self.bedTempSpinBox.value()))
        self.bed60PreheatButton.pressed.connect(lambda: self.preheatBedTemp(60))
        self.bed100PreheatButton.pressed.connect(lambda: self.preheatBedTemp(100))
        self.tool180PreheatButton.pressed.connect(lambda: self.preheatToolTemp(180))
        self.tool250PreheatButton.pressed.connect(lambda: self.preheatToolTemp(250))
        self.toolToggleTemperatureButton.pressed.connect(self.selectToolTemperature)

        # Motion Buttons Signal Connections
        self.step1mmButton.clicked.connect(lambda: self.setStep(1))
        self.step10mmButton.clicked.connect(lambda: self.setStep(10))
        self.step100mmButton.clicked.connect(lambda: self.setStep(100))
        self.moveXPButton.clicked.connect(lambda: self.octoprint_client.jog(x=self.step, speed=2000))
        self.moveXMButton.clicked.connect(lambda: self.octoprint_client.jog(x=-self.step, speed=2000))
        self.moveYPButton.clicked.connect(lambda: self.octoprint_client.jog(y=self.step, speed=2000))
        self.moveYMButton.clicked.connect(lambda: self.octoprint_client.jog(y=-self.step, speed=2000))
        self.motorOffButton.clicked.connect(lambda: self.octoprint_client.gcode(command='M18'))
        self.homeXYButton.clicked.connect(lambda: self.octoprint_client.home(['x', 'y']))
        self.moveZMButton.clicked.connect(lambda: self.octoprint_client.jog(z=-self.step, speed=2000))
        self.moveZPButton.clicked.connect(lambda: self.octoprint_client.jog(z=self.step, speed=2000))
        self.homeZButton.clicked.connect(lambda: self.octoprint_client.home(['z']))
        self.toolToggleMotionButton.clicked.connect(self.selectToolMotion)
        self.extruderButton.clicked.connect(lambda: self.octoprint_client.extrude(self.step))
        self.retractButton.clicked.connect(lambda: self.octoprint_client.extrude(-self.step))

        # Filament Buttons Signal Connections
        self.setFlowRateButton.clicked.connect(lambda: self.octoprint_client.flowrate(self.flowRateSpinBox.value()))
        self.changeFilamentButton.clicked.connect(self.open_change_filament_screen)
        self.toggleFilamentSensorButton.clicked.connect(self.toggleFilamentSensor)

        # Configure spinboxes
        for spinbox in [self.feedRateSpinBox, self.toolTempSpinBox, self.bedTempSpinBox, self.flowRateSpinBox]:
            if spinbox:
                spinbox.lineEdit().setReadOnly(True)
                spinbox.lineEdit().setDisabled(True)
                palette = QPalette()
                palette.setColor(QPalette.Highlight, QColor(40, 40, 40))
                spinbox.lineEdit().setPalette(palette)

        # Default to tab 0
        self.controlTabWidget.setCurrentIndex(0)

        # Initialize filament sensor state
        self.filament_sensor_enabled = True

        # local signal slot connections
        self.main_window.printer_model.filament_sensor_triggered.connect(self.filamentSensorHandler)
        # Connect to printer model for status updates
        self.main_window.printer_model.status_updated.connect(self.buttonStatusUpdate)
        self.logger.debug("Connected ControlScreen to printer model status updates")

    # ! To be commented out later
    def _initialize_sub_screens(self):
        """Initialize all control sub-screens"""
        try:
            # Create instance of change filament screen
            self.screens["change_filament"] = ChangeFilament(self.main_window)
            # Add reference to the parent screen for navigation
            self.screens["change_filament"].parent_screen = self
            self.main_window.stacked_widget.addWidget(self.screens["change_filament"])
            self.logger.info("Added change_filament screen to main stacked widget")
        except Exception as e:
            self.logger.exception(f"Error initializing sub-screens: {e}")

    def show_control_subscreen(self, target_screen=None):
        """Show a specific control subscreen

        Args:
            target_screen: String identifying which sub-screen to navigate to.
        """
        self.logger.debug(f"show_control_subscreen called with target_screen={target_screen}")

        # Only switch to this screen in the main window if we're not already on it
        if self.main_window.current_screen != self:
            self.main_window.switch_screen(self)

        # If no specific target is requested, do nothing
        if not target_screen:
            self.logger.debug("No target screen specified, staying on current screen")
            return

        # Check if the requested screen exists
        if target_screen not in self.screens:
            self.logger.error(f"Requested screen '{target_screen}' not found in available screens")
            return

        # Navigate to the requested sub-screen
        screen = self.screens[target_screen]
        self.main_window.switch_screen(screen)
        self.logger.info(f"Navigated to {target_screen}")

    def move_z_positive_baby_step(self):
        self.logger.info("Moving Z up slightly (baby step)")

    def move_z_negative_baby_step(self):
        self.logger.info("Moving Z down slightly (baby step)")

    def turn_fan_on(self):
        self.logger.info("Turning fan ON")

    def turn_fan_off(self):
        self.logger.info("Turning fan OFF")

    def cooldown(self):
        self.logger.info("Cooling down all heaters")

    def set_tool_temp(self):
        value = self.toolTempSpinBox.value()
        self.logger.info(f"Setting tool temperature to {value}°C")

    def set_bed_temp(self):
        value = self.bedTempSpinBox.value()
        self.logger.info(f"Setting bed temperature to {value}°C")

    def set_move_step(self, step):
        self.logger.info(f"Set movement step size to {step}mm")

    def move_x_positive(self):
        self.logger.info("Moving X+ axis")

    def move_x_negative(self):
        self.logger.info("Moving X- axis")

    def move_y_positive(self):
        self.logger.info("Moving Y+ axis")

    def move_y_negative(self):
        self.logger.info("Moving Y- axis")

    def set_flow_rate(self):
        value = self.flowRateSpinBox.value()
        self.logger.info(f"Setting flow rate to {value}%")

    def open_change_filament_screen(self):
        """Navigate to the Change Filament screen"""
        self.logger.info("Opening Change Filament screen")

        # Get the screen and make sure it's reset to initial state
        change_filament_screen = self.screens.get("change_filament")
        # if change_filament_screen and hasattr(change_filament_screen, "reset_wizard"):
        #     change_filament_screen.reset_wizard()

        # Use our consistent navigation method
        self.show_control_subscreen("change_filament")
        change_filament_screen.changeFilament()

    def toggleFilamentSensor(self):
        """
        Toggles the filament sensor
        """
        logger.info("ControlScreen.toggleFilamentSensor started")
        icon = 'filamentSensorOn' if self.toggleFilamentSensorButton.isChecked() else 'filamentSensorOff'
        # Use relative path for icon
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "img", "icons", icon)
        self.toggleFilamentSensorButton.setIcon(QtGui.QIcon(_fromUtf8(icon_path)))
        self.octoprint_client.gcode(
            command="PRIMARY_SFS_ENABLE{}".format(int(self.toggleFilamentSensorButton.isChecked())))

    def filamentSensorHandler(self, data):
        """
        Handles the filament sensor
        """
        logger.info("ControlScreen.filamentSensorHandler started")
        change_filament_screen = self.screens.get("change_filament")
        try:
            print(data)

            icon = 'filamentSensorOn' if self.toggleFilamentSensorButton.isChecked() else 'filamentSensorOff'
            self.toggleFilamentSensorButton.setIcon(QtGui.QIcon(_fromUtf8("templates/img/" + icon)))

            if not self.toggleFilamentSensorButton.isChecked():
                return

            triggered_extruder0 = False
            triggered_extruder1 = False

            if '0' in data:
                triggered_extruder0 = True

            if '1' in data:
                triggered_extruder1 = True

            if 'disabled' in data:
                self.toggleFilamentSensorButton.setIcon(QtGui.QIcon(_fromUtf8("templates/img/filamentSensorOff")))

            if 'enabled' in data:
                self.toggleFilamentSensorButton.setIcon(QtGui.QIcon(_fromUtf8("templates/img/filamentSensorOn")))

            if triggered_extruder0 and self.main_window.stacked_widget.currentWidget() not in [
                change_filament_screen.changeFilamentPage,
                change_filament_screen.changeFilamentProgressPage,
                change_filament_screen.changeFilamentExtrudePage,
                change_filament_screen.changeFilamentRetractPage,
                change_filament_screen.changeFilamentLoadPage]:
                self.octoprint_client.gcode(command='PAUSE')
                if dialog.WarningOk(self,
                                    "Filament outage or clog detected in Extruder 0. Please check the external motors. Print paused"):
                    pass

            if triggered_extruder1 and self.main_window.stacked_widget.currentWidget() not in [
                change_filament_screen.changeFilamentPage,
                change_filament_screen.changeFilamentProgressPage,
                change_filament_screen.changeFilamentExtrudePage,
                change_filament_screen.changeFilamentRetractPage,
                change_filament_screen.changeFilamentLoadPage]:
                self.octoprint_client.gcode(command='PAUSE')
                if dialog.WarningOk(self,
                                    "Filament outage or clog detected in Extruder 1. Please check the external motors. Print paused"):
                    pass

        except Exception as e:
            logger.error("Error in ControlScreen.filamentSensorHandler: {}".format(e))
            dialog.WarningOk(self, "Error in ControlScreen.filamentSensorHandler: {}".format(e), overlay=True)

    def coolDownAction(self):
        """'
        Turns all heaters and fans off
        """
        logger.info("ControlScreen.coolDownAction started")
        try:
            self.octoprint_client.gcode(command='M107')
            self.octoprint_client.setToolTemperature({"tool0": 0, "tool1": 0})
            # octopiclient.setToolTemperature({"tool0": 0})
            self.octoprint_client.setBedTemperature(0)
            self.toolTempSpinBox.setProperty("value", 0)
            self.bedTempSpinBox.setProperty("value", 0)
        except Exception as e:
            logger.error("Error in ControlScreen.coolDownAction: {}".format(e))
            dialog.WarningOk(self, "Error in ControlScreen.coolDownAction: {}".format(e), overlay=True)

    def setToolTemp(self):
        """
        Sets the temperature of the tool, depending on the tool selected
        """
        logger.info("ControlScreen.setToolTemp started")
        try:
            if self.toolToggleTemperatureButton.isChecked():
                self.octoprint_client.gcode(command='M104 T1 S' + str(self.toolTempSpinBox.value()))
                # octopiclient.setToolTemperature({"tool1": self.toolTempSpinBox.value()})
            else:
                self.octoprint_client.gcode(command='M104 T0 S' + str(self.toolTempSpinBox.value()))
                # octopiclient.setToolTemperature({"tool0": self.toolTempSpinBox.value()})
        except Exception as e:
            logger.error("Error in ControlScreen.setToolTemp: {}".format(e))
            dialog.WarningOk(self, "Error in ControlScreen.setToolTemp: {}".format(e), overlay=True)

    def preheatBedTemp(self, temp):
        """
        Preheats the bed to the given temperature
        param temp: temperature to preheat to
        """
        logger.info("ControlScreen.preheatBedTemp started")
        try:
            self.octoprint_client.gcode(command='M140 S' + str(temp))
            self.bedTempSpinBox.setProperty("value", temp)
        except Exception as e:
            logger.error("Error in ControlScreen.preheatBedTemp: {}".format(e))
            dialog.WarningOk(self, "Error in ControlScreen.preheatBedTemp: {}".format(e), overlay=True)

    def preheatToolTemp(self, temp):
        """
        Preheats the tool to the given temperature
        param temp: temperature to preheat to
        """
        logger.info("ControlScreen.preheatToolTemp started")
        try:
            if self.toolToggleTemperatureButton.isChecked():
                self.octoprint_client.gcode(command='M104 T1 S' + str(temp))
            else:
                self.octoprint_client.gcode(command='M104 T0 S' + str(temp))
            self.toolTempSpinBox.setProperty("value", temp)
        except Exception as e:
            logger.error("Error in ControlScreen.preheatToolTemp: {}".format(e))
            dialog.WarningOk(self, "Error in ControlScreen.preheatToolTemp: {}".format(e), overlay=True)

    def selectToolTemperature(self):
        """
        Selects the tool whose temperature needs to be changed.
        It accordingly changes the button text.it also updates the status of the other toggle buttons.
        """
        logger.info("ControlScreen.selectToolTemperature started")
        try:
            # self.toolToggleTemperatureButton.setText(
            #     "1") if self.toolToggleTemperatureButton.isChecked() else self.toolToggleTemperatureButton.setText("0")
            if self.toolToggleTemperatureButton.isChecked():
                print("extruder 1 Temperature")
                self.toolTempSpinBox.setProperty("value", float(self.main_window.home_screen.tool1TargetTemperature.text()))
            else:
                print("extruder 0 Temperature")
                self.toolTempSpinBox.setProperty("value", float(self.main_window.home_screen.tool0TargetTemperature.text()))
        except Exception as e:
            logger.error("Error in ControlScreen.selectToolTemperature: {}".format(e))
            dialog.WarningOk(self, "Error in ControlScreen.selectToolTemperature: {}".format(e), overlay=True)

    def selectToolMotion(self):
        """
        Selects the tool whose temperature needs to be changed. It accordingly changes the button text. it also updates the status of the other toggle buttons
        """
        logger.info("ControlScreen.selectToolMotion started")
        try:
            if self.toolToggleMotionButton.isChecked():
                self.octoprint_client.selectTool(1)
                self.setActiveExtruder(1)

            else:
                self.octoprint_client.selectTool(0)
                self.setActiveExtruder(0)
        except Exception as e:
            logger.error("Error in ControlScreen.selectToolMotion: {}".format(e))
            dialog.WarningOk(self, "Error in ControlScreen.selectToolMotion: {}".format(e), overlay=True)

    def setStep(self, stepRate):
        """
        Sets the class variable "Step" which would be needed for movement and joging
        :param stepRate: step multiplier for movement in the move
        :return: nothing
        """
        logger.info("ControlScreen.setStep started")
        try:
            if stepRate == 100:
                self.step100mmButton.setFlat(True)
                self.step1mmButton.setFlat(False)
                self.step10mmButton.setFlat(False)
                self.step = 100
            if stepRate == 1:
                self.step100mmButton.setFlat(False)
                self.step1mmButton.setFlat(True)
                self.step10mmButton.setFlat(False)
                self.step = 1
            if stepRate == 10:
                self.step100mmButton.setFlat(False)
                self.step1mmButton.setFlat(False)
                self.step10mmButton.setFlat(True)
                self.step = 10
        except Exception as e:
            logger.error("Error in ControlScreen.setStep: {}".format(e))
            dialog.WarningOk(self, "Error in ControlScreen.setStep: {}".format(e), overlay=True)

    def setActiveExtruder(self, activeNozzle):
        """
        Sets the active extruder, and changes the UI accordingly
        """
        logger.info("control_screen.setActiveExtruder started")
        try:
            if activeNozzle == 0:
                self.toolToggleMotionButton.setChecked(False)
                self.toolToggleMotionButton.setText("0")
                self.activeExtruder = 0
            elif activeNozzle == 1:
                self.toolToggleMotionButton.setChecked(True)
                self.toolToggleMotionButton.setText("1")
                self.activeExtruder = 1
        except Exception as e:
            logger.error("Error in control_screen.setActiveExtruder: {}".format(e))
            dialog.WarningOk(self, "Error in control_screen.setActiveExtruder: {}".format(e), overlay=True)

    def buttonStatusUpdate(self, status):
        """Update ControlScreen UI elements based on printer status"""
        try:
            # Disable motion controls during printing
            if status == "Printing":
                self.motionTab.setDisabled(True)
            else:  # Paused, Offline, Operational, etc.
                self.motionTab.setDisabled(False)
                    
            # TODO: Add other control-specific UI updates based on status
            # For example: disable certain temperature controls, etc.
        except Exception as e:
            logger.error(f"Error updating ControlScreen UI for status {status}: {e}")
            dialog.WarningOk(self, f"Error updating ControlScreen UI for status {status}: {e}", overlay=True)
