import os

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton, QLabel, QProgressBar
from PyQt5.QtCore import QTimer
from utils.helpers import check_ui_elements
from models.printer_model import PrinterModel  # Import the printer status model
from utils import logger  # Import the logger
from utils.styles import printer_status_green, printer_status_red, printer_status_amber
from utils import dialog
from utils import styles
from utils.network_utils import getIP

from utils.helpers import run_async
import time


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

        # Load the UI
        try:
            uic.loadUi("/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/home_screen/home_screen.ui", self)
            logger.info("HomeScreen UI loaded successfully")
        except Exception as e:
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

        # Temperature displays - Tool 1
        self.tool1TargetTemperature = self.findChild(QLabel, "tool1TargetTemperature")
        self.tool1ActualTemperature = self.findChild(QLabel, "tool1ActualTemperature")
        self.tool1TempBar = self.findChild(QProgressBar, "tool1TempBar")

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
            self.tool0TargetTemperature, self.tool0ActualTemperature, self.tool0TempBar,
            self.tool1TargetTemperature, self.tool1ActualTemperature, self.tool1TempBar,
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

        # # Set up update timer
        # self.update_timer = QTimer(self)
        # self.update_timer.timeout.connect(self.update_ui_from_printer_status)
        # self.update_timer.start(1000)  # Update every second

    def updatePrinterStatus(self, status):
        """
        Updates the status bar, is a slot for the signal emited from the thread that constantly polls for printer status
        this function updates the status bar, as well as enables/disables relavent buttons
        :param status: String of the status text
        """
        logger.info("HomeScreen.updatePrinterStatus called with status: {}".format(status))
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

    # def update_ui_from_printer_status(self):
    #     """Update UI based on current printer status"""
    #     if hasattr(self.main_window, 'octoprint_client'):
    #         client = self.main_window.octoprint_client
    #         if client and client.is_connected():
    #             # Get latest status information
    #             printer_data = client.get_printer_status()
    #             job_data = client.get_job_status()
    #
    #             # Update our internal data
    #             self._update_temperature_data(printer_data)
    #             self._update_job_data(job_data)
    #
    #             # Update UI
    #             self._update_temperature_displays()
    #             self._update_print_info()
    #             self._update_printer_status(printer_data.get("state", {}).get("text", "Unknown"))
    #
    #             # Update connection status
    #             self._update_connection_status(True, client.get_ip_address())
    #         else:
    #             self._update_connection_status(False)

    # def _update_temperature_data(self, printer_data):
    #     """Update internal temperature data from printer status"""
    #     if not printer_data or "temperature" not in printer_data:
    #         return
    #
    #     temp_data = printer_data["temperature"]
    #
    #     # Update tool0 temperature
    #     if "tool0" in temp_data:
    #         self.temperature_data["tool0"]["actual"] = temp_data["tool0"]["actual"]
    #         self.temperature_data["tool0"]["target"] = temp_data["tool0"]["target"]
    #
    #     # Update tool1 temperature
    #     if "tool1" in temp_data:
    #         self.temperature_data["tool1"]["actual"] = temp_data["tool1"]["actual"]
    #         self.temperature_data["tool1"]["target"] = temp_data["tool1"]["target"]
    #
    #     # Update bed temperature
    #     if "bed" in temp_data:
    #         self.temperature_data["bed"]["actual"] = temp_data["bed"]["actual"]
    #         self.temperature_data["bed"]["target"] = temp_data["bed"]["target"]

    # def _update_job_data(self, job_data):
    #     """Update internal job data from printer status"""
    #     if not job_data:
    #         return
    #
    #     # Update file name
    #     if "file" in job_data and "name" in job_data["file"]:
    #         self.current_file = job_data["file"]["name"]
    #     else:
    #         self.current_file = "No file selected"
    #
    #     # Update progress
    #     if "progress" in job_data and "completion" in job_data["progress"]:
    #         progress = job_data["progress"]["completion"]
    #         self.print_progress = int(progress) if progress is not None else 0
    #
    #     # Update time information
    #     if "progress" in job_data:
    #         # Print time
    #         if "printTime" in job_data["progress"]:
    #             seconds = job_data["progress"]["printTime"] or 0
    #             self.print_time = self._format_time(seconds)
    #
    #         # Time left
    #         if "printTimeLeft" in job_data["progress"]:
    #             seconds = job_data["progress"]["printTimeLeft"] or 0
    #             self.time_left = self._format_time(seconds)

    # def _format_time(self, seconds):
    #     """Format seconds to HH:MM:SS"""
    #     if seconds is None:
    #         return "00:00:00"
    #
    #     hours = int(seconds // 3600)
    #     minutes = int((seconds % 3600) // 60)
    #     seconds = int(seconds % 60)
    #     return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # def _update_temperature_displays(self):
    #     """Update all temperature displays"""
    #     # Tool 0
    #     if self.tool0ActualTemperature and self.tool0TargetTemperature and self.tool0TempBar:
    #         actual = self.temperature_data["tool0"]["actual"]
    #         target = self.temperature_data["tool0"]["target"]
    #
    #         self.tool0ActualTemperature.setText(f"{actual:.1f}")
    #         self.tool0TargetTemperature.setText(f"{target:.1f}")
    #         self.tool0TempBar.setValue(min(int(actual), self.tool0TempBar.maximum()))
    #
    #     # Tool 1
    #     if self.tool1ActualTemperature and self.tool1TargetTemperature and self.tool1TempBar:
    #         actual = self.temperature_data["tool1"]["actual"]
    #         target = self.temperature_data["tool1"]["target"]
    #
    #         self.tool1ActualTemperature.setText(f"{actual:.1f}")
    #         self.tool1TargetTemperature.setText(f"{target:.1f}")
    #         self.tool1TempBar.setValue(min(int(actual), self.tool1TempBar.maximum()))
    #
    #     # Bed
    #     if self.bedActualTemperatute and self.bedTargetTemperature and self.bedTempBar:
    #         actual = self.temperature_data["bed"]["actual"]
    #         target = self.temperature_data["bed"]["target"]
    #
    #         self.bedActualTemperatute.setText(f"{actual:.1f}")
    #         self.bedTargetTemperature.setText(f"{target:.1f}")
    #         self.bedTempBar.setValue(min(int(actual), self.bedTempBar.maximum()))

    # def _update_print_info(self):
    #     """Update print job information"""
    #     if self.fileName:
    #         self.fileName.setText(self.current_file)
    #
    #     if self.printTime:
    #         self.printTime.setText(self.print_time)
    #
    #     if self.timeLeft:
    #         self.timeLeft.setText(self.time_left)
    #
    #     if self.printProgressBar:
    #         self.printProgressBar.setValue(self.print_progress)

    # def _update_printer_status(self, status_text):
    #     """Update printer status display and indicator"""
    #     if not self.printerStatus or not self.printerStatusColour:
    #         return
    #
    #     self.printerStatus.setText(status_text)
    #
    #     # Set color based on status
    #     if status_text.lower() in ["operational", "ready"]:
    #         self.printerStatusColour.setStyleSheet(printer_status_green)
    #     elif status_text.lower() in ["printing", "paused"]:
    #         self.printerStatusColour.setStyleSheet(printer_status_amber)
    #     else:
    #         self.printerStatusColour.setStyleSheet(printer_status_red)

    # def _update_connection_status(self, connected, ip_address=None):
    #     """Update printer connection status"""
    #     self.printer_connected = connected
    #
    #     if self.ipStatus:
    #         if connected and ip_address:
    #             self.ipStatus.setText(f"Connected: {ip_address}")
    #         else:
    #             self.ipStatus.setText("Not Connected")
    #
    #     # Disable controls when not connected
    #     for button_name in ["doorLockButton", "playPauseButton", "stopButton"]:
    #         button = self.all_components.get(button_name, {}).get("instance")
    #         if button:
    #             button.setEnabled(connected)

    # Event handlers

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
                    logger.error("Error in MainUiClass.playPauseAction: {}".format(e))
                    dialog.WarningOk(self, "Error in MainUiClass.playPauseAction: {}".format(e), overlay=True)

    def open_control_panel(self):
        """Navigate to control panel screen"""
        self.main_window.switch_to_control_screen()
        logger.debug("Control Panel button clicked")
