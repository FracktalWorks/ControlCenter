import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton, QLabel, QProgressBar
from PyQt5.QtCore import QTimer
from PyQt5 import QtGui
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils.styles import printer_status_green, printer_status_red, printer_status_amber
from utils import dialog
from utils import styles
from utils.network_utils import getIP

from utils.helpers import run_async
import time


logger = get_logger(__name__)

class HomeScreen(QWidget):
    def __init__(self, main_window):
        super(HomeScreen, self).__init__()
        self.main_window = main_window
        self.printer_connected = False
        self.is_printing = False
        self.temperature_data = {"tool0": {"actual": 0, "target": 0},
                                 "tool1": {"actual": 0, "target": 0},
                                 "bed": {"actual": 0, "target": 0}}

        # Job info
        self.current_file = "No file selected"
        self.current_image = None
        self.print_progress = 0
        self.print_time = "-"
        self.time_left = "-"
        self.printerStatusText = ""
        self._last_status = ""

        # Use class-level logger
        self.logger = get_logger(self.__class__.__name__)
        # Load the UI
        try:
            # Use relative path from the current module's directory
            ui_file_path = os.path.join(os.path.dirname(__file__), "home_screen.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("HomeScreen UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load HomeScreen UI file: {e}")
            logger.exception(f"Failed to load HomeScreen UI file: {e}")

        """ ---------- Initialize UI components by group ---------- """

        # Control buttons
        self.doorLockButton = self.findChild(QToolButton, "doorLockButton")  # Done
        self.menuButton = self.findChild(QPushButton, "menuButton")  # Done
        self.stopButton = self.findChild(QPushButton, "stopButton")  # Done
        self.playPauseButton = self.findChild(QPushButton, "playPauseButton")
        self.controlButton = self.findChild(QPushButton, "controlButton")

        # Temperature displays - Tool 0
        self.tool0TargetTemperature = self.findChild(QLabel, "tool0TargetTemperature")
        self.tool0ActualTemperature = self.findChild(QLabel, "tool0ActualTemperature")
        self.tool0TempBar = self.findChild(QProgressBar, "tool0TempBar")
        self.tool0Label = self.findChild(QLabel, "tool0Label")

        # Temperature displays - Tool 1
        self.tool1TargetTemperature = self.findChild(QLabel, "tool1TargetTemperature")
        self.tool1ActualTemperature = self.findChild(QLabel, "tool1ActualTemperature")
        self.tool1TempBar = self.findChild(QProgressBar, "tool1TempBar")
        self.tool1Label = self.findChild(QLabel, "tool1Label")

        # Temperature displays - Bed
        self.bedTargetTemperature = self.findChild(QLabel, "bedTargetTemperature")
        self.bedActualTemperatute = self.findChild(QLabel, "bedActualTemperatute")
        self.bedTempBar = self.findChild(QProgressBar, "bedTempBar")

        # Status components
        self.printerStatus = self.findChild(QLabel, "printerStatus")
        self.printerStatusColour = self.findChild(QLabel, "printerStatusColour")
        self.ipStatus = self.findChild(QLabel, "ipStatus")

        # Print information
        self.fileName = self.findChild(QLabel, "fileName")
        self.printTime = self.findChild(QLabel, "printTime")
        self.timeLeft = self.findChild(QLabel, "timeLeft")
        self.printProgressBar = self.findChild(QProgressBar, "printProgressBar")
        self.printPreviewMain = self.findChild(QLabel, "printPreviewMain")

        # Validate UI components
        all_components = [
            self.doorLockButton, self.menuButton, self.stopButton, self.playPauseButton, self.controlButton,
            self.tool0TargetTemperature, self.tool0ActualTemperature, self.tool0TempBar, self.tool0Label,
            self.tool1TargetTemperature, self.tool1ActualTemperature, self.tool1TempBar, self.tool1Label,
            self.bedTargetTemperature, self.bedActualTemperatute, self.bedTempBar,
            self.printerStatus, self.printerStatusColour, self.ipStatus,
            self.fileName, self.printTime, self.timeLeft, self.printProgressBar, self.printPreviewMain
        ]
        check_ui_elements(self, all_components, "HomeScreen")

        # ! Local Signal-Slot Connections
        # Connect signals from model to slots from home_screen
        self.main_window.printer_model.status_updated.connect(self.updatePrinterStatus)
        self.main_window.printer_model.print_status_updated.connect(self.updatePrintStatus)
        self.main_window.printer_model.temperatures_updated.connect(self.updateTemperature)
        self.main_window.printer_model.active_extruder_changed.connect(self.setActiveExtruder)

        # Connect button signals to their handlers
        if self.doorLockButton:
            self.doorLockButton.clicked.connect(self.toggle_door_lock)

        if self.menuButton:
            self.menuButton.clicked.connect(self.open_menu)

        if self.stopButton:
            self.stopButton.clicked.connect(self.stop_print)

        if self.playPauseButton:
            self.playPauseButton.clicked.connect(self.play_pause_print)

        if self.controlButton:
            self.controlButton.clicked.connect(self.open_control_panel)

        # Initialize UI state
        # Update temperature displays
        if self.tool0ActualTemperature and self.tool0TargetTemperature:
            self.tool0ActualTemperature.setText("0.0")
            self.tool0TargetTemperature.setText("0.0")
            if self.tool0TempBar:
                self.tool0TempBar.setValue(0)

        if self.tool1ActualTemperature and self.tool1TargetTemperature:
            self.tool1ActualTemperature.setText("0.0")
            self.tool1TargetTemperature.setText("0.0")
            if self.tool1TempBar:
                self.tool1TempBar.setValue(0)

        if self.bedActualTemperatute and self.bedTargetTemperature:
            self.bedActualTemperatute.setText("0.0")
            self.bedTargetTemperature.setText("0.0")
            if self.bedTempBar:
                self.bedTempBar.setValue(0)

        # Update print info
        if self.fileName:
            self.fileName.setText(self.current_file)
        if self.printTime:
            self.printTime.setText(self.print_time)
        if self.timeLeft:
            self.timeLeft.setText(self.time_left)
        if self.printProgressBar:
            self.printProgressBar.setValue(self.print_progress)

        # Update printer status
        if self.printerStatus:
            self.printerStatus.setText("Disconnected")
        if self.printerStatusColour:
            self.printerStatusColour.setStyleSheet(printer_status_red)
        if self.ipStatus:
            self.ipStatus.setText("Not Connected")

        self.setActiveExtruder(0)  # Default to extruder 0


    def updatePrinterStatus(self, status):
        """
        Updates the status bar, is a slot for the signal emited from the thread that constantly polls for printer status
        this function updates the status bar, as well as enables/disables relavent buttons
        :param status: String of the status text
        """
        if getattr(self, "_last_status", None) != status:
            logger.info("HomeScreen.updatePrinterStatus called with status: {}".format(status))
            self._last_status = status
        try:
            self.printerStatusText = status
            self.printerStatus.setText(status)

            if status == "Printing":  # Green
                self.printerStatusColour.setStyleSheet(styles.printer_status_green)
            elif status == "Offline":  # Red
                self.printerStatusColour.setStyleSheet(styles.printer_status_red)
            elif status == "Paused":  # Amber
                self.printerStatusColour.setStyleSheet(styles.printer_status_amber)
            elif status == "Operational":  # Amber
                self.printerStatusColour.setStyleSheet(styles.printer_status_blue)

            '''
            Depending on Status, enable and Disable Buttons
            '''
            if status == "Printing":
                self.playPauseButton.setChecked(True)
                self.stopButton.setDisabled(False)
                # self.motionTab.setDisabled(True)
                # self.changeFilamentButton.setDisabled(True) in some different file
                self.main_window.menu_screen.menuCalibrateButton.setDisabled(True)
                self.main_window.menu_screen.menuPrintButton.setDisabled(True)
                self.doorLockButton.setDisabled(False)
                # if not self.__timelapse_enabled:
                #     octopiclient.cancelPrint()
                #     self.coolDownAction()

            elif status == "Paused":
                self.playPauseButton.setChecked(False)
                self.stopButton.setDisabled(False)
                # self.motionTab.setDisabled(False)
                # self.changeFilamentButton.setDisabled(False)
                self.main_window.menu_screen.menuCalibrateButton.setDisabled(True)
                self.main_window.menu_screen.menuPrintButton.setDisabled(True)
                self.doorLockButton.setDisabled(False)

            else:
                self.stopButton.setDisabled(True)
                self.playPauseButton.setChecked(False)
                # self.motionTab.setDisabled(False)
                # self.changeFilamentButton.setDisabled(False)
                self.main_window.menu_screen.menuCalibrateButton.setDisabled(False)
                self.main_window.menu_screen.menuPrintButton.setDisabled(False)
                self.doorLockButton.setDisabled(True)

        except Exception as e:
            logger.error("Error in HomeScreen.updatePrinterStatus: {}".format(e))
            dialog.WarningOk(self, "Error in HomeScreen.updatePrinterStatus: {}".format(e), overlay=True)

    def updatePrintStatus(self, file):
        """
        displays infromation of a particular file on the home page
        It is a slot for the signal emited from the thread that keeps pooling for printer status
        runs at 1HZ, so do things that need to be constantly updated only
        :param file: dict of all the attributes of a particualr file
        """
        try:
            if file["job"] is None:
                self.current_image = None
                self.timeLeft.setText("-")
                self.fileName.setText("-")
                self.printProgressBar.setValue(0)
                self.printTime.setText("-")
                self.playPauseButton.setDisabled(True)  # if file is not available, disable playPauseButton

            else:
                self.playPauseButton.setDisabled(False)  # if file available, make play buttom visible
                self.fileName.setText(file['job']['file']['name'])
                self.current_file = file['job']['file']['name']
                if file['progress']['printTime'] is None:
                    self.printTime.setText("-")
                else:
                    m, s = divmod(file['progress']['printTime'], 60)
                    h, m = divmod(m, 60)
                    d, h = divmod(h, 24)
                    self.printTime.setText("%d:%d:%02d:%02d" % (d, h, m, s))

                if file['progress']['printTimeLeft'] is None:
                    self.timeLeft.setText("-")
                else:
                    m, s = divmod(file['progress']['printTimeLeft'], 60)
                    h, m = divmod(m, 60)
                    d, h = divmod(h, 24)
                    self.timeLeft.setText("%d:%d:%02d:%02d" % (d, h, m, s))

                if file['progress']['completion'] is None:
                    self.printProgressBar.setValue(0)
                else:
                    self.printProgressBar.setValue(file['progress']['completion'])

                '''
                If image is available from server, set it, otherwise display default image.
                If the image was already loaded, dont load it again.
                '''
                if self.current_image != self.current_file:
                    self.current_image = self.current_file
                    self.main_window.print_location_screen.displayThumbnail(self.printPreviewMain, self.current_file, usb=False)
        except Exception as e:
            logger.error("Error in MainUiClass.updatePrintStatus: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.updatePrintStatus: {}".format(e), overlay=True)

    def updateTemperature(self, temperature):
        """
        Slot that gets a signal originating from the thread that keeps polling for printer status
        runs at 1HZ, so do things that need to be constantly updated only. This also controls the cooling fan depending on the temperatures
        :param temperature: dict containing key:value pairs with keys being the tools, bed and their values being their corresponding temperratures
        """
        try:
            # ideally the none to 0 conversion should happen here
            if temperature['tool0Actual'] is None:
                temperature['tool0Actual'] = 0
            if temperature['tool0Target'] is None:
                temperature['tool0Target'] = 180
            if temperature['tool1Actual'] is None:
                temperature['tool1Actual'] = 0
            if temperature['tool1Target'] is None:
                temperature['tool1Target'] = 180
            if temperature['bedActual'] is None:
                temperature['bedActual'] = 0
            if temperature['bedTarget'] is None:
                temperature['bedTarget'] = 60

            # Update extruder 0 temperature
            if temperature['tool0Target'] == 0:
                self.tool0TempBar.setMaximum(300)
                self.tool0TempBar.setStyleSheet(styles.bar_heater_cold)
            elif temperature['tool0Actual'] <= temperature['tool0Target']:
                self.tool0TempBar.setMaximum(temperature['tool0Target'])
                self.tool0TempBar.setStyleSheet(styles.bar_heater_heating)
            else:
                self.tool0TempBar.setMaximum(temperature['tool0Actual'])
            self.tool0TempBar.setValue(temperature['tool0Actual'])
            self.tool0ActualTemperature.setText(str(int(temperature['tool0Actual'])))  # + unichr(176)
            self.tool0TargetTemperature.setText(str(int(temperature['tool0Target'])))

            # Update extruder 1 temperature
            if temperature['tool1Target'] == 0:
                self.tool1TempBar.setMaximum(300)
                self.tool1TempBar.setStyleSheet(styles.bar_heater_cold)
            elif temperature['tool1Actual'] <= temperature['tool1Target']:
                self.tool1TempBar.setMaximum(temperature['tool1Target'])
                self.tool1TempBar.setStyleSheet(styles.bar_heater_heating)
            else:
                self.tool1TempBar.setMaximum(temperature['tool1Actual'])
            self.tool1TempBar.setValue(temperature['tool1Actual'])
            self.tool1ActualTemperature.setText(str(int(temperature['tool1Actual'])))  # + unichr(176)
            self.tool1TargetTemperature.setText(str(int(temperature['tool1Target'])))

            # Update bed temperature
            if temperature['bedTarget'] == 0:
                self.bedTempBar.setMaximum(150)
                self.bedTempBar.setStyleSheet(styles.bar_heater_cold)
            elif temperature['bedActual'] <= temperature['bedTarget']:
                self.bedTempBar.setMaximum(temperature['bedTarget'])
                self.bedTempBar.setStyleSheet(styles.bar_heater_heating)
            else:
                self.bedTempBar.setMaximum(temperature['bedActual'])
            self.bedTempBar.setValue(temperature['bedActual'])
            self.bedActualTemperatute.setText(str(int(temperature['bedActual'])))  # + unichr(176))
            self.bedTargetTemperature.setText(str(int(temperature['bedTarget'])))  # + unichr(176))

        except:
            pass

    @run_async
    def setIPStatus(self):
        """
        Function to update IP address of printer on the status bar. Refreshes at a particular interval.
        """
        try:
            while True:
                try:
                    if getIP("eth0"):
                        self.ipStatus.setText(getIP("eth0"))
                    elif getIP("wlan0"):
                        self.ipStatus.setText(getIP("wlan0"))
                    else:
                        self.ipStatus.setText("Not connected")

                except:
                    self.ipStatus.setText("Not connected")
                time.sleep(60)
        except Exception as e:
            logger.error("Error in MainUiClass.setIPStatus: {}".format(e))

    # ! Below are the boilerplate functions

    def toggle_door_lock(self):
        """Toggle printer door lock"""
        # if not self.printer_connected:
        #     return

        logger.debug("Toggle Door Lock button clicked")
        is_locked = self.doorLockButton.isChecked()
        door_status = "locked" if is_locked else "unlocked"
        logger.info(f"Door {door_status}")

        # Send command to OctoPrint if connected
        if hasattr(self.main_window, 'octoprint_client'):
            client = self.main_window.octoprint_client
            if client:
                # Replace with actual command for your printer
                try:
                    command = "M280 P0 S10" if is_locked else "M280 P0 S90"
                    client.gcode(command=command)
                    client.overrideDoorLock()
                except Exception as e:
                    logger.error("Error in MainUiClass.doorLock: {}".format(e))
                    dialog.WarningOk(self, "Error in MainUiClass.doorLock: {}".format(e), overlay=True)

    def open_menu(self):
        """Navigate to menu screen"""
        self.main_window.switch_to_menu_screen()
        logger.debug("Menu button clicked")

    def stop_print(self):
        """Stop current print job"""
        # if not self.printer_connected:
        #     return

        logger.info("MainUiClass.stopActionMessageBox started")
        logger.debug("Stop Print button clicked")

        # Send command to OctoPrint if connected
        if hasattr(self.main_window, 'octoprint_client'):
            client = self.main_window.octoprint_client
            if client:
                try:
                    if dialog.WarningYesNo(self, "Are you sure you want to stop the print?"):
                        client.cancelPrint()
                except Exception as e:
                    logger.error("Error in MainUiClass.stopActionMessageBox: {}".format(e))
                    dialog.WarningOk(self, "Error in MainUiClass.stopActionMessageBox: {}".format(e), overlay=True)

    def play_pause_print(self):
        """Play or pause print job based on current state"""
        # if not self.printer_connected:
        #     return

        is_paused = self.playPauseButton.isChecked()
        logger.debug(f"Play/Pause button clicked: {'Pausing' if not is_paused else 'Resuming'}")

        # Send command to OctoPrint if connected
        if hasattr(self.main_window, 'octoprint_client'):
            client = self.main_window.octoprint_client
            if client:
                try:
                    if self.printerStatusText == "Operational":
                        if self.playPauseButton.isChecked:
                            self.main_window.checkKlipperPrinterCFG()
                            client.startPrint()
                    elif self.printerStatusText == "Printing":
                        client.pausePrint()
                    elif self.printerStatusText == "Paused":
                        client.pausePrint()
                except Exception as e:
                    logger.error("Error in home_screen.playPauseAction: {}".format(e))
                    dialog.WarningOk(self, "Error in home_screen.playPauseAction: {}".format(e), overlay=True)

    def open_control_panel(self):
        """Navigate to control panel screen"""
        self.main_window.switch_to_control_screen()
        logger.debug("Control Panel button clicked")

    def setActiveExtruder(self, activeNozzle):
        """
        Sets the active extruder, and changes the UI accordingly
        """
        logger.info("home_screen.setActiveExtruder started with activeNozzle: {}".format(activeNozzle))
        try:
            # Debug: Check if labels exist
            logger.debug("tool0Label found: {}".format(self.tool0Label is not None))
            logger.debug("tool1Label found: {}".format(self.tool1Label is not None))
            
            if activeNozzle == 0:
                if self.tool0Label:
                    pixmap = QtGui.QPixmap(":/img/icons/activeNozzle.png")
                    if not pixmap.isNull():
                        self.tool0Label.setPixmap(pixmap)
                        logger.debug("Set tool0Label to activeNozzle.png")
                    else:
                        logger.error("Failed to load activeNozzle.png pixmap")
                if self.tool1Label:
                    pixmap = QtGui.QPixmap(":/img/icons/Nozzle.png")
                    if not pixmap.isNull():
                        self.tool1Label.setPixmap(pixmap)
                        logger.debug("Set tool1Label to Nozzle.png")
                    else:
                        logger.error("Failed to load Nozzle.png pixmap")
            elif activeNozzle == 1:
                if self.tool0Label:
                    pixmap = QtGui.QPixmap(":/img/icons/Nozzle.png")
                    if not pixmap.isNull():
                        self.tool0Label.setPixmap(pixmap)
                        logger.debug("Set tool0Label to Nozzle.png")
                    else:
                        logger.error("Failed to load Nozzle.png pixmap")
                if self.tool1Label:
                    pixmap = QtGui.QPixmap(":/img/icons/activeNozzle.png")
                    if not pixmap.isNull():
                        self.tool1Label.setPixmap(pixmap)
                        logger.debug("Set tool1Label to activeNozzle.png")
                    else:
                        logger.error("Failed to load activeNozzle.png pixmap")
                # Note: toolToggleChangeFilamentButton is not defined in this screen
                # if hasattr(self, 'toolToggleChangeFilamentButton'):
                #     self.toolToggleChangeFilamentButton.setChecked(True)
        except Exception as e:
            logger.error("Error in MainUiClass.setActiveExtruder: {}".format(e))
            dialog.WarningOk(self, "Error in home_screen.setActiveExtruder: {}".format(e), overlay=True)
