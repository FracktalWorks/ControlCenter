
import os
import time
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QComboBox, QProgressBar, QLabel
from utils.helpers import check_ui_elements, run_async
from utils.logger import get_logger
from utils import dialog

# Compatibility for PyQt5 string conversion
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

logger = get_logger(__name__)


class ChangeFilament(QWidget):
    """
    Widget for handling the filament change process in the UI.
    Handles UI state, button connections, and printer commands for loading/unloading filament.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.model = main_window.printer_model
        self.octoprint_client = main_window.octoprint_client
        self.changeFilamentHeatingFlag = False
        self.loadFlag = None
        self.activeExtruder = 0  # Default to extruder 0
        self.loadStopFlag = False

        # Use centralized logger
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing ChangeFilament widget")

        # Load UI
        try:
            # Use relative path from the current module's directory
            ui_file_path = os.path.join(os.path.dirname(__file__), "changeFilament.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("ChangeFilament UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load ChangeFilament UI file: {e}", exc_info=True)
            return

        # Initialize UI components
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.changeFilamentPage = self.findChild(QWidget, "changeFilamentPage")
        self.changeFilamentProgressPage = self.findChild(QWidget, "changeFilamentProgressPage")
        self.changeFilamentLoadPage = self.findChild(QWidget, "changeFilamentLoadPage")
        self.changeFilamentExtrudePage = self.findChild(QWidget, "changeFilamentExtrudePage")
        self.changeFilamentRetractPage = self.findChild(QWidget, "changeFilamentRetractPage")
        self.changeFilamentBackButton = self.findChild(QPushButton, "changeFilamentBackButton")
        self.changeFilamentBackButton2 = self.findChild(QPushButton, "changeFilamentBackButton2")
        self.changeFilamentBackButton3 = self.findChild(QPushButton, "changeFilamentBackButton3")
        self.changeFilamentLoadButton = self.findChild(QPushButton, "changeFilamentLoadButton")
        self.changeFilamentUnloadButton = self.findChild(QPushButton, "changeFilamentUnloadButton")
        self.toolToggleChangeFilamentButton = self.findChild(QPushButton, "toolToggleChangeFilamentButton")
        self.loadedTillExtruderButton = self.findChild(QPushButton, "loadedTillExtruderButton")
        self.loadDoneButton = self.findChild(QPushButton, "loadDoneButton")
        self.unloadDoneButton = self.findChild(QPushButton, "unloadDoneButton")
        self.changeFilamentComboBox = self.findChild(QComboBox, "changeFilamentComboBox")
        self.changeFilamentProgress = self.findChild(QProgressBar, "changeFilamentProgress")
        self.changeFilamentStatus = self.findChild(QLabel, "changeFilamentStatus")
        self.changeFilamentNameOperation = self.findChild(QLabel, "changeFilamentNameOperation")

        # Validate UI components
        components = [
            self.stackedWidget, self.changeFilamentPage, self.changeFilamentProgressPage,
            self.changeFilamentLoadPage, self.changeFilamentExtrudePage, self.changeFilamentRetractPage,
            self.changeFilamentBackButton, self.changeFilamentBackButton2, self.changeFilamentBackButton3,
            self.changeFilamentLoadButton, self.changeFilamentUnloadButton, self.toolToggleChangeFilamentButton,
            self.loadedTillExtruderButton, self.loadDoneButton, self.unloadDoneButton,
            self.changeFilamentComboBox, self.changeFilamentProgress, self.changeFilamentStatus
        ]
        check_ui_elements(self, components, "ChangeFilament")

        # Connect signals to slots
        self._connect_signals()

        self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
        self.setActiveExtruder(0)  # Default to extruder 0

    def showEvent(self, event):
        """Reset to changeFilamentPage whenever this widget is shown."""
        super().showEvent(event)
        try:
            if self.stackedWidget and self.changeFilamentPage:
                self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
                self.logger.debug("Reset stacked widget to changeFilamentPage on show")
        except Exception as e:
            self.logger.error(f"Error resetting to changeFilamentPage: {e}")

    def _connect_signals(self):
        """Connect all UI signals to their respective slots."""
        self.model.active_extruder_changed.connect(self.setActiveExtruder)

        button_slot_map = [
            (self.changeFilamentBackButton, self.changeFilamentDone),
            (self.changeFilamentBackButton2, self.changeFilamentCancel),
            (self.changeFilamentBackButton3, self.changeFilamentCancel),
            (self.changeFilamentLoadButton, self.loadFilament),
            (self.changeFilamentUnloadButton, self.unloadFilament),
            (self.toolToggleChangeFilamentButton, self.selectToolChangeFilament),
            (self.loadedTillExtruderButton, self.changeFilamentExtrudePageFunction),
            (self.loadDoneButton, self.changeFilamentDone),
            (self.unloadDoneButton, self.changeFilament),
        ]
        for button, slot in button_slot_map:
            if button:
                button.clicked.connect(slot)

    def changeFilament(self):
        """
        Initialize the change filament screen, populate filament options, and set the current extruder.
        """
        logger.info("ChangeFilament.changeFilament() started")
        self.loadFlag = False
        self.changeFilamentHeatingFlag = False
        self.loadStopFlag = True
        try:
            self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
            time.sleep(1)
            if self.model.printer_status not in ["Printing", "Paused"]:
                self.octoprint_client.gcode("G28")
            self.selectToolChangeFilament()
            self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
            self.changeFilamentComboBox.clear()
            self.changeFilamentComboBox.addItems(self.model.filaments.keys())
            tool0TargetTemperature = self.model.temperatures.get('tool0Target', None)
            if tool0TargetTemperature and self.model.printer_status in ["Printing", "Paused"]:
                self.changeFilamentComboBox.addItem("Loaded Filament")
                index = self.changeFilamentComboBox.findText("Loaded Filament")
                if index >= 0:
                    self.changeFilamentComboBox.setCurrentIndex(index)
        except Exception as e:
            logger.error(f"Error in ChangeFilament.changeFilament: {e}")
            dialog.WarningOk(self, f"Error in ChangeFilament.changeFilament: {e}", overlay=True)

    def selectToolChangeFilament(self):
        """
        Select the tool whose temperature needs to be changed and update UI/button state.
        """
        logger.info("changeFilament.selectToolChangeFilament started")
        try:
            if self.toolToggleChangeFilamentButton.isChecked():
                self.setActiveExtruder(1)
                self.octoprint_client.selectTool(1)
                self.octoprint_client.jog(self.model.tool1PurgePosition['X'], self.model.tool1PurgePosition["Y"], absolute=True, speed=10000)
            else:
                self.setActiveExtruder(0)
                self.octoprint_client.selectTool(0)
                self.octoprint_client.jog(self.model.tool0PurgePosition['X'], self.model.tool0PurgePosition["Y"], absolute=True, speed=10000)
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error in changeFilament.selectToolChangeFilament: {e}")
            dialog.WarningOk(self, f"Error in changeFilament.selectToolChangeFilament: {e}", overlay=True)

    def changeFilamentCancel(self):
        """
        Cancel the filament change process and reset UI/state.
        """
        logger.info("ChangeFilament.changeFilamentCancel started")
        try:
            self._disconnect_temperature_signal()
            if self.model.printer_status not in ["Printing", "Paused"]:
                self.main_window.control_screen.coolDownAction()
            self.main_window.switch_to_control_screen()
            self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
            self.loadFlag = False
            self.changeFilamentHeatingFlag = False
        except Exception as e:
            logger.error(f"Error in ChangeFilament.changeFilamentCancel: {e}")
            dialog.WarningOk(self, f"Error in ChangeFilament.changeFilamentCancel: {e}", overlay=True)

    def loadFilament(self):
        """
        Start the filament loading process: jog to purge position, set temperature, update UI.
        """
        logger.info("changeFilament.loadFilament started - Updated one")
        try:
            self.loadStopFlag = False
            purge_pos = self.model.tool1PurgePosition if self.activeExtruder == 1 else self.model.tool0PurgePosition
            if self.model.printer_status not in ["Printing", "Paused"]:
                self.octoprint_client.jog(purge_pos['X'], purge_pos["Y"], absolute=True, speed=10000)
            print("Jogging done")
            if self.changeFilamentComboBox.findText("Loaded Filament") == -1:
                print("reached here")
                tool_key = f"tool{self.activeExtruder}"
                temp = self.model.filaments[str(self.changeFilamentComboBox.currentText())]
                self.octoprint_client.setToolTemperature({tool_key: temp})
            self.stackedWidget.setCurrentWidget(self.changeFilamentProgressPage)
            self.model.temperatures_updated.connect(self.updateTemperature)
            self.changeFilamentStatus.setText(f"Heating Tool {self.activeExtruder}, Please Wait...")
            self.changeFilamentNameOperation.setText(f"Loading {self.changeFilamentComboBox.currentText()}")
            self.changeFilamentHeatingFlag = True
            self.loadFlag = True
        except Exception as e:
            self.loadFlag = False
            self.changeFilamentHeatingFlag = False
            logger.error(f"Error in changeFilament.loadFilament: {e}")
            dialog.WarningOk(self, f"Error in changeFilament.loadFilament: {e}", overlay=True)

    def unloadFilament(self):
        """
        Start the filament unloading process: jog to purge position, set temperature, update UI.
        """
        logger.info("changeFilament.unloadFilament started")
        try:
            purge_pos = self.model.tool1PurgePosition if self.activeExtruder == 1 else self.model.tool0PurgePosition
            if self.model.printer_status not in ["Printing", "Paused"]:
                self.octoprint_client.jog(purge_pos['X'], purge_pos["Y"], absolute=True, speed=10000)
            if self.changeFilamentComboBox.findText("Loaded Filament") == -1:
                tool_key = f"tool{self.activeExtruder}"
                temp = self.model.filaments[str(self.changeFilamentComboBox.currentText())]
                self.octoprint_client.setToolTemperature({tool_key: temp})
            self.stackedWidget.setCurrentWidget(self.changeFilamentProgressPage)
            self.model.temperatures_updated.connect(self.updateTemperature)
            self.changeFilamentStatus.setText(f"Heating Tool {self.activeExtruder}, Please Wait...")
            self.changeFilamentNameOperation.setText(f"Unloading {self.changeFilamentComboBox.currentText()}")
            self.changeFilamentHeatingFlag = True
            self.loadFlag = False
        except Exception as e:
            self.loadFlag = False
            self.changeFilamentHeatingFlag = False
            logger.error(f"Error in changeFilament.unloadFilament: {e}")
            dialog.WarningOk(self, f"Error in changeFilament.unloadFilament: {e}", overlay=True)

    def _disconnect_temperature_signal(self):
        """Disconnect the temperature update signal if connected."""
        try:
            self.model.temperatures_updated.disconnect(self.updateTemperature)
        except TypeError:
            # Signal was not connected, which is fine
            pass

    def updateTemperature(self, temp):
        """
        Update the temperature progress bar and trigger next step when heating is complete.
        """
        try:
            if not self.changeFilamentHeatingFlag:
                return
            extruder = self.activeExtruder
            tool_target = temp.get(f'tool{extruder}Target', 0)
            tool_actual = temp.get(f'tool{extruder}Actual', 0)
            if tool_target == 0:
                self.changeFilamentProgress.setMaximum(300)
            elif tool_target - tool_actual > 1:
                self.changeFilamentProgress.setMaximum(tool_target)
            else:
                self.changeFilamentProgress.setMaximum(tool_actual)
                self.changeFilamentHeatingFlag = False
                self._disconnect_temperature_signal()
                if self.loadFlag:
                    self.changeFilamentLoadFunction()
                else:
                    self.octoprint_client.extrude(5)
                    self.changeFilamentRetractFunction()
            self.changeFilamentProgress.setValue(tool_actual)
        except Exception as e:
            logger.error(f"Error in changeFilament.updateTemperature: {e}")
            dialog.WarningOk(self, f"Error in changeFilament.updateTemperature: {e}", overlay=True)

    @run_async
    def changeFilamentLoadFunction(self):
        """
        Called after heating: slowly move extruder to pull filament in.
        """
        logger.info("ChangeFilament.changeFilamentLoadFunction started")
        try:
            self.stackedWidget.setCurrentWidget(self.changeFilamentLoadPage)
            while self.stackedWidget.currentWidget() == self.changeFilamentLoadPage:
                self.octoprint_client.gcode("G91")
                self.octoprint_client.gcode("G1 E5 F500")
                self.octoprint_client.gcode("G90")
                time.sleep(self.calcExtrudeTime(5, 500))
        except Exception as e:
            logger.error(f"Error in ChangeFilament.changeFilamentLoadFunction: {e}")
            dialog.WarningOk(self, f"Error in ChangeFilament.changeFilamentLoadFunction: {e}", overlay=True)

    @run_async
    def changeFilamentExtrudePageFunction(self, *args, **kwargs):
        """
        After loading, extrude filament until it reaches the toolhead.
        """
        logger.info("ChangeFilament.changeFilamentExtrudePageFunction started")
        try:
            print("______________________________Entered extrusion function____________________________")
            self.stackedWidget.setCurrentWidget(self.changeFilamentExtrudePage)
            for i in range(int(self.model.ptfeTubeLength / 150)):
                print("___________________________Entered the for loop______________________________")
                self.octoprint_client.gcode("G91")
                self.octoprint_client.gcode("G1 E150 F1500")
                self.octoprint_client.gcode("G90")
                time.sleep(self.calcExtrudeTime(150, 1500))
                if self.stackedWidget.currentWidget() is not self.changeFilamentExtrudePage:
                    print("___________________________widget not set____________________________")
                    break
            print("___________________________Exited the for loop______________________________")
            while self.stackedWidget.currentWidget() == self.changeFilamentExtrudePage:
                print("___________________________Still extruding____________________________")
                is_tpu = self.changeFilamentComboBox.currentText() == "TPU"
                feed = 300 if is_tpu else 600
                self.octoprint_client.gcode("G91")
                self.octoprint_client.gcode(f"G1 E20 F{feed}")
                self.octoprint_client.gcode("G90")
                time.sleep(self.calcExtrudeTime(20, feed))
            print("___________________________Exited the while loop______________________________")
        except Exception as e:
            logger.error(f"Error in ChangeFilament.changeFilamentExtrudePageFunction: {e}")
            dialog.WarningOk(self, f"Error in ChangeFilament.changeFilamentExtrudePageFunction: {e}", overlay=True)

    @run_async
    def changeFilamentRetractFunction(self):
        """
        Remove the filament from the toolhead, including tip shaping and full retraction.
        """
        logger.info("ChangeFilament.changeFilamentRetractFunction started")
        try:
            print("______________________________Entered retraction function____________________________")
            self.stackedWidget.setCurrentWidget(self.changeFilamentRetractPage)
            is_tpu = self.changeFilamentComboBox.currentText() == "TPU"
            feed = 300 if is_tpu else 600
            self.octoprint_client.gcode("G91")
            self.octoprint_client.gcode(f"G1 E10 F{feed}")
            time.sleep(self.calcExtrudeTime(10, feed))
            self.octoprint_client.gcode("G1 E-25 F6000")
            time.sleep(self.calcExtrudeTime(20, 6000))
            time.sleep(8)  # wait for filament to cool inside the nozzle
            self.octoprint_client.gcode("G1 E-150 F5000")
            time.sleep(self.calcExtrudeTime(150, 5000))
            self.octoprint_client.gcode("G90")
            for _ in range(int(self.model.ptfeTubeLength / 150)):
                print("___________________________Entered the for loop______________________________")
                self.octoprint_client.gcode("G91")
                self.octoprint_client.gcode("G1 E-150 F2000")
                self.octoprint_client.gcode("G90")
                time.sleep(self.calcExtrudeTime(150, 2000))
                if self.stackedWidget.currentWidget() is not self.changeFilamentRetractPage:
                    print("___________________________widget not set____________________________")
                    break

            while self.stackedWidget.currentWidget() == self.changeFilamentRetractPage:
                print("___________________________Still retracting____________________________")
                self.octoprint_client.gcode("G91")
                self.octoprint_client.gcode("G1 E-5 F1000")
                self.octoprint_client.gcode("G90")
                time.sleep(self.calcExtrudeTime(5, 1000))
            print("___________________________Exited the while loop______________________________")
        except Exception as e:
            logger.error(f"Error in ChangeFilament.changeFilamentRetractFunction: {e}")
            dialog.WarningOk(self, f"Error in ChangeFilament.changeFilamentRetractFunction: {e}", overlay=True)

    def calcExtrudeTime(self, length, speed):
        """
        Calculate the time in seconds to extrude a given length at a given speed (mm/min).
        """
        return length / (speed / 60)

    def setActiveExtruder(self, activeNozzle):
        """
        Set the active extruder and update the toggle button state.
        Slot for the active_extruder_changed signal from the printer model.
        """
        logger.info("changeFilament.setActiveExtruder started")
        try:
            activeNozzle = int(activeNozzle)
            self.toolToggleChangeFilamentButton.setChecked(activeNozzle == 1)
            self.activeExtruder = activeNozzle
        except Exception as e:
            logger.error(f"Error in changeFilament.setActiveExtruder: {e}")
            dialog.WarningOk(self, f"Error in changeFilament.setActiveExtruder: {e}", overlay=True)

    def changeFilamentDone(self):
        """
        Complete the filament change process and return to the control screen.
        """
        logger.info("ChangeFilament.changeFilamentDone started")
        try:
            self._disconnect_temperature_signal()
            self.stackedWidget.setCurrentWidget(self.changeFilamentPage)  # Stops retract and extruding loop as well
            self.main_window.switch_to_control_screen()
            self.changeFilamentHeatingFlag = False
        except Exception as e:
            logger.error(f"Error in ChangeFilament.changeFilamentDone: {e}")
            dialog.WarningOk(self, f"Error in ChangeFilament.changeFilamentDone: {e}", overlay=True)