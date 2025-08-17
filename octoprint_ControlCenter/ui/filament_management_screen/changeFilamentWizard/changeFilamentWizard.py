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


class ChangeFilamentWizard(QWidget):
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
            ui_file_path = os.path.join(os.path.dirname(__file__), "changeFilamentWizard.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("changeFilamentWizard UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load changeFilamentWizard UI file: {e}", exc_info=True)
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
            self.changeFilamentLoadButton, self.changeFilamentUnloadButton,
            self.loadedTillExtruderButton, self.loadDoneButton, self.unloadDoneButton,
            self.changeFilamentComboBox, self.changeFilamentProgress, self.changeFilamentStatus
        ]
        check_ui_elements(self, components, "ChangeFilament")

        # Connect signals directly here (simplified)
        # model signal
        self.model.active_extruder_changed.connect(self.setActiveExtruder)

        # UI button connections (fixed mapping; backButton2 uses same slot as backButton)
        # Back buttons should cancel without persisting any state
        self.changeFilamentBackButton.clicked.connect(self.changeFilamentCancel)
        self.changeFilamentBackButton2.clicked.connect(self.changeFilamentCancel)
        self.changeFilamentBackButton3.clicked.connect(self.changeFilamentCancel)
        self.changeFilamentLoadButton.clicked.connect(self.loadFilament)
        self.changeFilamentUnloadButton.clicked.connect(self.unloadFilament)
        self.loadedTillExtruderButton.clicked.connect(self.changeFilamentExtrudePageFunction)
        self.loadDoneButton.clicked.connect(self.changeFilamentDone)
        # On unload completion, finalize via changeFilamentDone (persists only if loadFlag was set)
        self.unloadDoneButton.clicked.connect(self.changeFilamentDone)

        self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
        self.setActiveExtruder(0)  # Default to extruder 0

    def showEvent(self, event):
        """Reset to changeFilamentPage whenever this widget is shown."""
        super().showEvent(event)
        try:
            self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
            self.logger.debug("Reset stacked widget to changeFilamentPage on show")
        except Exception as e:
            self.logger.error(f"Error resetting to changeFilamentPage: {e}")

    def changeFilament(self):
        """
        Initialize the change filament screen, populate filament options, and set the current extruder.
        """
        logger.info("ChangeFilament.changeFilament() started")
        # None means no operation yet; set True on load, False on unload
        self.loadFlag = None
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
        Select the tool based on current activeExtruder (no UI toggle).
        """
        logger.info("changeFilament.selectToolChangeFilament started")
        try:
            # Use the activeExtruder value (set by setup() or model signal) to select tool and jog
            if int(self.activeExtruder) == 1:
                self.octoprint_client.selectTool(1)
                self.octoprint_client.jog(self.model.tool1PurgePosition['X'], self.model.tool1PurgePosition["Y"], absolute=True, speed=10000)
            else:
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
            self.main_window.filament_management_screen.show_material_nozzle_screen()     
            self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
            self.loadFlag = None
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
            # On error, ensure no persistence happens if user taps Done
            self.loadFlag = None
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
            # On error, ensure no persistence happens if user taps Done
            self.loadFlag = None
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
        Set the active extruder (slot for model signal or external caller).
        """
        logger.info("changeFilament.setActiveExtruder started")
        try:
            activeNozzle = int(activeNozzle)
            # UI toggle removed; just store activeExtruder
            self.activeExtruder = activeNozzle
        except Exception as e:
            logger.error(f"Error in changeFilament.setActiveExtruder: {e}")
            dialog.WarningOk(self, f"Error in changeFilament.setActiveExtruder: {e}", overlay=True)

    # New setup API so filamentManagementScreen can pass which tool/bay opened the wizard
    def setup(self, params=None):
        """
        Params can be:
          - dict with 'tool': e.g. {"tool": "tool0"} or {"tool": "tool1"}
          - str: e.g. "tool0" (legacy)
          - None
        """
        try:
            # Normalize params to a dict
            if isinstance(params, str):
                params = {'tool': params}
            elif params is None:
                params = {}
            elif not isinstance(params, dict):
                params = {}

            # If a tool is provided, use it to set active extruder
            tool = params.get('tool')
            if isinstance(tool, str) and tool.startswith('tool'):
                try:
                    nozzle_index = int(tool.replace('tool', ''))
                    self.setActiveExtruder(nozzle_index)
                except Exception:
                    # ignore malformed tool string
                    pass
            self.changeFilament()
        except Exception as e:
            logger.error(f"Error in ChangeFilament.setup: {e}", exc_info=True)
            dialog.WarningOk(self, f"Error in ChangeFilament.setup: {e}", overlay=True)

    def changeFilamentDone(self):
        """
        Complete the filament change process and return to the main screen.
        """
        logger.info("ChangeFilament.changeFilamentDone started")
        try:
            # Persist tool state only if a load/unload operation was initiated
            if self.loadFlag is not None:
                try:
                    tool_key = f"tool{int(self.activeExtruder)}"
                    bay = self.main_window.printer_model.get_default_bay(tool_key)
                    # Determine selected filament name if any
                    selected = None
                    try:
                        selected_text = self.changeFilamentComboBox.currentText()
                        if selected_text and selected_text != "Loaded Filament":
                            selected = selected_text
                    except Exception:
                        # If combobox is unavailable, keep existing filament on load
                        selected = None

                    if bool(self.loadFlag):
                        # Loading: status Loaded; filament to selected (if provided), else unchanged
                        self.model.update_tool_bay_state(tool_key, bay=bay, filament=selected, status="Loaded", persist=True)
                    else:
                        # Unloading: status Empty; filament cleared
                        self.model.update_tool_bay_state(tool_key, bay=bay, filament=None, status="Empty", persist=True)
                except Exception as e:
                    logger.warning(f"Failed to persist tool state on filament change done: {e}")

            self._disconnect_temperature_signal()
            self.stackedWidget.setCurrentWidget(self.changeFilamentPage)  # Stops retract and extruding loop as well
            self.main_window.filament_management_screen.show_material_nozzle_screen()
            self.changeFilamentHeatingFlag = False
            # Reset the flag to avoid unintended reuse
            self.loadFlag = None
        except Exception as e:
            logger.error(f"Error in ChangeFilament.changeFilamentDone: {e}")
            dialog.WarningOk(self, f"Error in ChangeFilament.changeFilamentDone: {e}", overlay=True)