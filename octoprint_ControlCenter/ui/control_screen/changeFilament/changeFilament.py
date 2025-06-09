import time

from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QComboBox, QProgressBar, QLabel
from utils.helpers import check_ui_elements
from utils import logger
from utils import dialog
from utils.logger import setup_logger
from utils.helpers import run_async

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class ChangeFilament(QWidget):
    def __init__(self, main_window, control_screen, home_screen):
        super(ChangeFilament, self).__init__()
        self.main_window = main_window
        self.control_screen = control_screen
        self.home_screen = home_screen
        self.changeFilamentHeatingFlag = False
        self.loadFlag = None
        self.activeExtruder = 0  # Default to extruder 0

        # Setup logger
        self.logger = setup_logger(f"{self.__class__.__name__}")
        self.logger.info("Initializing ChangeFilament widget")

        # Load UI
        try:
            uic.loadUi(
                '/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/control_screen/changeFilament/changeFilament.ui',
                self)
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
            self.stackedWidget,
            self.changeFilamentPage, self.changeFilamentProgressPage,
            self.changeFilamentLoadPage, self.changeFilamentExtrudePage,
            self.changeFilamentRetractPage,
            self.changeFilamentBackButton, self.changeFilamentBackButton2,
            self.changeFilamentBackButton3,
            self.changeFilamentLoadButton, self.changeFilamentUnloadButton,
            self.toolToggleChangeFilamentButton, self.loadedTillExtruderButton,
            self.loadDoneButton, self.unloadDoneButton,
            self.changeFilamentComboBox, self.changeFilamentProgress,
            self.changeFilamentStatus
        ]
        check_ui_elements(self, components, "ChangeFilament")

        # ! Local Signal Slot Connections
        self.main_window.printer_model.active_extruder_changed.connect(self.setActiveExtruder)
        self.main_window.printer_model.temperatures_updated.connect(self.updateTemperature)

        # Connect signals to slots
        if self.changeFilamentBackButton:
            self.changeFilamentBackButton.clicked.connect(self.control)
        if self.changeFilamentBackButton2:
            self.changeFilamentBackButton2.clicked.connect(self.changeFilamentCancel)
        if self.changeFilamentBackButton3:
            self.changeFilamentBackButton3.clicked.connect(self.changeFilamentCancel)
        if self.changeFilamentLoadButton:
            self.changeFilamentLoadButton.clicked.connect(self.loadFilament)
        if self.changeFilamentUnloadButton:
            self.changeFilamentUnloadButton.clicked.connect(self.unloadFilament)
        if self.toolToggleChangeFilamentButton:
            self.toolToggleChangeFilamentButton.clicked.connect(self.selectToolChangeFilament)
        if self.loadedTillExtruderButton:
            self.loadedTillExtruderButton.clicked.connect(self.changeFilamentExtrudePageFunction)
        if self.loadDoneButton:
            self.loadDoneButton.clicked.connect(self.control)
        if self.unloadDoneButton:
            self.unloadDoneButton.clicked.connect(self.changeFilament)

        # # Set the default screen
        # self._show_page('change_filament_screen')

        try:
            # Wait for components to initialize
            QtCore.QTimer.singleShot(1000, self._init_change_filament)
        except Exception as e:
            logger.error(f"Error initializing change filament screen: {e}")
            dialog.WarningOk(self, f"Error initializing change filament screen: {e}", overlay=True)

    def _init_change_filament(self):
        """Initialize the change filament screen with required settings"""
        try:
            if self.home_screen.printerStatusText not in ["Printing", "Paused"]:
                self.main_window.octoprint_client.gcode("G28")

            # Clear and update the filament combo box
            if self.changeFilamentComboBox:
                self.changeFilamentComboBox.clear()
                self.changeFilamentComboBox.addItems(self.main_window.printer_model.filaments.keys())

                # Add "Loaded Filament" option if printing
                if (self.home_screen.tool0TargetTemperature and
                        self.home_screen.printerStatusText in ["Printing", "Paused"]):
                    self.changeFilamentComboBox.addItem("Loaded Filament")
                    index = self.changeFilamentComboBox.findText("Loaded Filament")
                    if index >= 0:
                        self.changeFilamentComboBox.setCurrentIndex(index)

            # Show the change filament page
            self._show_page('change_filament_screen')

        except Exception as e:
            self.logger.error(f"Error in _init_change_filament: {e}")
            dialog.WarningOk(self, f"Error in _init_change_filament: {e}", overlay=True)

    def _show_page(self, page_name):
        """Show a specific page in the stacked widget."""
        if not self.stackedWidget:
            self.logger.error("Cannot show page - stacked widget is missing")
            return False
        page = getattr(self, page_name, None)
        if page:
            self.stackedWidget.setCurrentWidget(page)
            self.logger.info(f"Showing page: {page_name}")
            return True
        else:
            self.logger.error(f"Cannot show page {page_name} - page not found")
            return False

    def control(self):
        """
        Sets the current page to the control page
        """
        logger.info("MainUiClass.control started")
        try:
            # self.stackedWidget.setCurrentWidget(self.control_screen)
            self.main_window.switch_to_control_screen()
            if self.control_screen.toolToggleTemperatureButton.isChecked():
                self.control_screen.toolTempSpinBox.setProperty(
                    "value", float(self.home_screen.tool1TargetTemperature.text())
                )
            else:
                self.control_screen.toolTempSpinBox.setProperty(
                    "value", float(self.home_screen.tool0TargetTemperature.text())
                )
            self.control_screen.bedTempSpinBox.setProperty(
                "value", float(self.home_screen.bedTargetTemperature.text())
            )
        except Exception as e:
            logger.error("Error in MainUiClass.control: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.control: {}".format(e), overlay=True)

    def loadFilament(self):
        logger.info("MainUiClass.loadFilament started - Updated one")
        try:
            if self.home_screen.printerStatusText not in ["Printing", "Paused"]:
                if self.activeExtruder == 1:
                    self.main_window.octoprint_client.jog(
                        self.main_window.printer_model.tool1PurgePosition['X'],
                        self.main_window.printer_model.tool1PurgePosition["Y"],
                        absolute=True, speed=10000
                    )

                else:
                    self.main_window.octoprint_client.jog(
                        self.main_window.printer_model.tool0PurgePosition['X'],
                        self.main_window.printer_model.tool0PurgePosition["Y"],
                        absolute=True, speed=10000
                    )
            print("Jogging done")
            if self.changeFilamentComboBox.findText("Loaded Filament") == -1:
                print("reached here")
                self.main_window.octoprint_client.setToolTemperature(
                    {"tool1": self.main_window.printer_model.filaments[str(
                        self.changeFilamentComboBox.currentText())]}) if self.activeExtruder == 1 else self.main_window.octoprint_client.setToolTemperature(
                    {"tool0": self.main_window.printer_model.filaments[str(self.changeFilamentComboBox.currentText())]})
            self.stackedWidget.setCurrentWidget(self.changeFilamentProgressPage)
            self.changeFilamentStatus.setText("Heating Tool {}, Please Wait...".format(str(self.activeExtruder)))
            self.changeFilamentNameOperation.setText(
                "Loading {}".format(str(self.changeFilamentComboBox.currentText())))
            # this flag tells the updateTemperature function that runs every second to update the filament change progress bar as well, and to load or unload after heating done
            self.changeFilamentHeatingFlag = True
            self.loadFlag = True
        except Exception as e:
            self.loadFlag = False
            self.changeFilamentHeatingFlag = False
            logger.error("Error in MainUiClass.loadFilament: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.loadFilament: {}".format(e), overlay=True)

    def unloadFilament(self):
        logger.info("MainUiClass.unloadFilament started")
        try:
            if self.home_screen.printerStatusText not in ["Printing", "Paused"]:
                if self.activeExtruder == 1:
                    self.main_window.octoprint_client.jog(
                        self.main_window.printer_model.tool1PurgePosition['X'],
                        self.main_window.printer_model.tool1PurgePosition["Y"],
                        absolute=True, speed=10000
                    )

                else:
                    self.main_window.octoprint_client.jog(
                        self.main_window.printer_model.tool0PurgePosition['X'],
                        self.main_window.printer_model.tool0PurgePosition["Y"],
                        absolute=True, speed=10000
                    )

            if self.changeFilamentComboBox.findText("Loaded Filament") == -1:
                self.main_window.octoprint_client.setToolTemperature({"tool1": self.main_window.printer_model.filaments[str(
                    self.changeFilamentComboBox.currentText())]}) if self.activeExtruder == 1 else self.main_window.octoprint_client.setToolTemperature(
                    {"tool0": self.main_window.printer_model.filaments[str(self.changeFilamentComboBox.currentText())]})
            self.stackedWidget.setCurrentWidget(self.changeFilamentProgressPage)
            self.changeFilamentStatus.setText("Heating Tool {}, Please Wait...".format(str(self.activeExtruder)))
            self.changeFilamentNameOperation.setText("Unloading {}".format(str(self.changeFilamentComboBox.currentText())))
            # this flag tells the updateTemperature function that runs every second to update the filament change progress bar as well, and to load or unload after heating done
            self.changeFilamentHeatingFlag = True
            self.loadFlag = False
        except Exception as e:
            self.loadFlag = False
            self.changeFilamentHeatingFlag = False
            logger.error("Error in MainUiClass.unloadFilament: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.unloadFilament: {}".format(e), overlay=True)

    def updateTemperature(self, temperature):
        try:
            if self.changeFilamentHeatingFlag:
                if self.activeExtruder == 0:
                    if temperature['tool0Target'] == 0:
                        self.changeFilamentProgress.setMaximum(300)
                    elif temperature['tool0Target'] - temperature['tool0Actual'] > 1:
                        self.changeFilamentProgress.setMaximum(temperature['tool0Target'])
                    else:
                        self.changeFilamentProgress.setMaximum(temperature['tool0Actual'])
                        self.changeFilamentHeatingFlag = False
                        if self.loadFlag:
                            self.changeFilamentLoadFunction()
                            # self.stackedWidget.setCurrentWidget(self.changeFilamentExtrudePage)
                        else:
                            # self.stackedWidget.setCurrentWidget(self.changeFilamentRetractPage)
                            self.main_window.octoprint_client.extrude(5)  # extrudes some amount of filament to prevent plugging
                            self.changeFilamentRetractFunction()

                    self.changeFilamentProgress.setValue(temperature['tool0Actual'])
                elif self.activeExtruder == 1:
                    if temperature['tool1Target'] == 0:
                        self.changeFilamentProgress.setMaximum(300)
                    elif temperature['tool1Target'] - temperature['tool1Actual'] > 1:
                        self.changeFilamentProgress.setMaximum(temperature['tool1Target'])
                    else:
                        self.changeFilamentProgress.setMaximum(temperature['tool1Actual'])
                        self.changeFilamentHeatingFlag = False
                        if self.loadFlag:
                            self.changeFilamentLoadFunction()
                            # self.stackedWidget.setCurrentWidget(self.changeFilamentExtrudePage)
                        else:
                            # self.stackedWidget.setCurrentWidget(self.changeFilamentRetractPage)
                            self.main_window.octoprint_client.extrude(5)  # extrudes some amount of filament to prevent plugging
                            self.changeFilamentRetractFunction()

                    self.changeFilamentProgress.setValue(temperature['tool1Actual'])

        except Exception as e:
            logger.error("Error in MainUiClass.updateTemperature: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.updateTemperature: {}".format(e), overlay=True)

    def setActiveExtruder(self, activeNozzle):
        """
        Sets the active extruder, and changes the UI accordingly
        Is a slot for the active_extruder_changed signal from the printer model.
        """
        logger.info("MainUiClass.setActiveExtruder started")
        try:
            activeNozzle = int(activeNozzle)
            if activeNozzle == 0:
                # self.home_screen.tool0Label.setPixmap(QtGui.QPixmap(_fromUtf8("ui/resources/img/icons/activeNozzle.png")))
                # self.home_screen.tool1Label.setPixmap(QtGui.QPixmap(_fromUtf8("ui/resources/img/icons/Nozzle.png")))
                self.toolToggleChangeFilamentButton.setChecked(False)
                self.toolToggleChangeFilamentButton.setText("0")
                self.control_screen.toolToggleMotionButton.setChecked(False)
                self.control_screen.toolToggleMotionButton.setText("0")
                self.activeExtruder = 0
            elif activeNozzle == 1:
                # self.home_screen.tool0Label.setPixmap(QtGui.QPixmap(_fromUtf8("ui/resources/img/icons/Nozzle.png")))
                # self.home_screen.tool1Label.setPixmap(QtGui.QPixmap(_fromUtf8("ui/resources/img/icons/activeNozzle.png")))
                self.toolToggleChangeFilamentButton.setChecked(True)
                self.toolToggleChangeFilamentButton.setText("1")
                self.control_screen.toolToggleMotionButton.setChecked(True)
                self.control_screen.toolToggleMotionButton.setText("1")
                self.activeExtruder = 1

                # set button states
                # set octoprint if mismatch
        except Exception as e:
            logger.error("Error in MainUiClass.setActiveExtruder: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.setActiveExtruder: {}".format(e), overlay=True)

    def changeFilament(self):
        """
        Called when the change filament screen is initialized.
        Adds the filaments to the changeFilamentComboBox and sets the current extruder.
        """
        logger.info("MainUiClass.changeFilament started")
        try:
            time.sleep(1)
            if self.home_screen.printerStatusText not in ["Printing", "Paused"]:
                self.main_window.octoprint_client.gcode("G28")
            self.selectToolChangeFilament()

            # self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
            self.changeFilamentComboBox.clear()
            self.changeFilamentComboBox.addItems(self.main_window.printer_model.filaments.keys())
            # Update
            print(self.home_screen.tool0TargetTemperature)
            if self.home_screen.tool0TargetTemperature and self.home_screen.printerStatusText in ["Printing", "Paused"]:
                self.changeFilamentComboBox.addItem("Loaded Filament")
                index = self.changeFilamentComboBox.findText("Loaded Filament")
                if index >= 0:
                    self.changeFilamentComboBox.setCurrentIndex(index)
        except Exception as e:
            logger.error("Error in MainUiClass.changeFilament: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.changeFilament: {}".format(e), overlay=True)

    def selectToolChangeFilament(self):
        """
        Selects the tool whose temperature needs to be changed. It accordingly changes the button text. it also updates the status of the other toggle buttons
        """
        logger.info("MainUiClass.selectToolChangeFilament started")
        try:
            if self.toolToggleChangeFilamentButton.isChecked():
                self.setActiveExtruder(1)
                self.main_window.octoprint_client.selectTool(1)
                self.main_window.octoprint_client.jog(
                    self.main_window.printer_model.tool1PurgePosition['X'],
                    self.main_window.printer_model.tool1PurgePosition["Y"],
                    absolute=True, speed=10000
                )
                time.sleep(1)

            else:
                self.setActiveExtruder(0)
                self.main_window.octoprint_client.selectTool(0)
                self.main_window.octoprint_client.jog(
                    self.main_window.printer_model.tool0PurgePosition['X'],
                    self.main_window.printer_model.tool0PurgePosition["Y"],
                    absolute=True, speed=10000
                )
                time.sleep(1)
        except Exception as e:
            logger.error("Error in MainUiClass.selectToolChangeFilament: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.selectToolChangeFilament: {}".format(e), overlay=True)

    @run_async
    def changeFilamentLoadFunction(self):
        """
        This function is called once the heating is done, which slowly moves the extruder so that it starts pulling filament
        """
        logger.info("MainUiClass.changeFilamentLoadFunction started")
        try:
            self.stackedWidget.setCurrentWidget(self.changeFilamentLoadPage)
            while self.stackedWidget.currentWidget() == self.changeFilamentLoadPage:
                self.main_window.octoprint_client.gcode("G91")
                self.main_window.octoprint_client.gcode("G1 E5 F500")
                self.main_window.octoprint_client.gcode("G90")
                time.sleep(self.calcExtrudeTime(5, 500))
        except Exception as e:
            logger.error("Error in MainUiClass.changeFilamentLoadFunction: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.changeFilamentLoadFunction: {}".format(e), overlay=True)

    @run_async
    def changeFilamentExtrudePageFunction(self):
        """
        once filament is loaded, this function is called to extrude filament till the toolhead
        """
        logger.info("MainUiClass.changeFilamentExtrudePageFunction started")
        try:
            self.stackedWidget.setCurrentWidget(self.changeFilamentExtrudePage)
            for i in range(int(self.main_window.printer_model.ptfeTubeLength / 150)):
                self.main_window.octoprint_client.gcode("G91")
                self.main_window.octoprint_client.gcode("G1 E150 F1500")
                self.main_window.octoprint_client.gcode("G90")
                time.sleep(self.calcExtrudeTime(150, 1500))
                if self.stackedWidget.currentWidget() is not self.changeFilamentExtrudePage:
                    break

            while self.stackedWidget.currentWidget() == self.changeFilamentExtrudePage:
                if self.changeFilamentComboBox.currentText() == "TPU":
                    self.main_window.octoprint_client.gcode("G91")
                    self.main_window.octoprint_client.gcode("G1 E20 F300")
                    self.main_window.octoprint_client.gcode("G90")
                    time.sleep(self.calcExtrudeTime(20, 300))
                else:
                    self.main_window.octoprint_client.gcode("G91")
                    self.main_window.octoprint_client.gcode("G1 E20 F600")
                    self.main_window.octoprint_client.gcode("G90")
                    time.sleep(self.calcExtrudeTime(20, 600))
        except Exception as e:
            logger.error("Error in MainUiClass.changeFilamentExtrudePageFunction: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.changeFilamentExtrudePageFunction: {}".format(e), overlay=True)

    @run_async
    def changeFilamentRetractFunction(self):
        """
        Remove the filament from the toolhead
        """
        logger.info("MainUiClass.changeFilamentRetractFunction started")
        try:
            self.stackedWidget.setCurrentWidget(self.changeFilamentRetractPage)
            # Tip Shaping to prevent filament jamming in nozzle
            if self.changeFilamentComboBox.currentText() == "TPU":
                self.main_window.octoprint_client.gcode("G91")
                self.main_window.octoprint_client.gcode("G1 E10 F300")
                time.sleep(self.calcExtrudeTime(10, 300))
            else:
                self.main_window.octoprint_client.gcode("G91")
                self.main_window.octoprint_client.gcode("G1 E10 F600")
                time.sleep(self.calcExtrudeTime(10, 600))
            self.main_window.octoprint_client.gcode("G1 E-25 F6000")
            time.sleep(self.calcExtrudeTime(20, 6000))
            time.sleep(8)  # wait for filament to cool inside the nozzle
            self.main_window.octoprint_client.gcode("G1 E-150 F5000")
            time.sleep(self.calcExtrudeTime(150, 5000))
            self.main_window.octoprint_client.gcode("G90")
            for i in range(int(self.main_window.printer_model.ptfeTubeLength / 150)):
                self.main_window.octoprint_client.gcode("G91")
                self.main_window.octoprint_client.gcode("G1 E-150 F2000")
                self.main_window.octoprint_client.gcode("G90")
                time.sleep(self.calcExtrudeTime(150, 2000))
                if self.stackedWidget.currentWidget() is not self.changeFilamentRetractPage:
                    break

            while self.stackedWidget.currentWidget() == self.changeFilamentRetractPage:
                self.main_window.octoprint_client.gcode("G91")
                self.main_window.octoprint_client.gcode("G1 E-5 F1000")
                self.main_window.octoprint_client.gcode("G90")
                time.sleep(self.calcExtrudeTime(5, 1000))
        except Exception as e:
            logger.error("Error in MainUiClass.changeFilamentRetractFunction: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.changeFilamentRetractFunction: {}".format(e), overlay=True)

    def calcExtrudeTime(self, length, speed):
        """
        Calculate the time it takes to extrude a certain length of filament at a certain speed
        :param length: length of filament to extrude
        :param speed: speed at which to extrude
        :return: time in seconds
        """
        return length / (speed / 60)

    def changeFilamentCancel(self):
        logger.info("MainUiClass.changeFilamentCancel started")
        try:
            self.changeFilamentHeatingFlag = False
            if self.home_screen.printerStatusText not in ["Printing", "Paused"]:
                self.control_screen.coolDownAction()
            self.control()
            self.loadFlag = False
            self.changeFilamentHeatingFlag = False
        except Exception as e:
            logger.error("Error in MainUiClass.changeFilamentCancel: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.changeFilamentCancel: {}".format(e), overlay=True)
