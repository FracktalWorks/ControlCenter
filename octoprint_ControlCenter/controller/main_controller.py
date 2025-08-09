from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import QTimer 
from ui.main_window import MainWindow
from utils.logger import get_logger
from models.printer_model import PrinterModel
from octoprint_client.websocket_client import OctoPrintWebSocket
from utils import klipper_cfg_utils
from octoprint_client import octoprint_singleton
from PyQt5 import QtCore
import time
import subprocess
import os
import websocket
import json
import requests
import random
import uuid
import threading
from utils.helpers import run_async
from utils import dialog
from ui.loading_screen.loading_screen import LoadingScreen
from config import ip, apiKey, CRITICAL_PRINTER_ERRORS


logger = get_logger(__name__)

class ThreadConnectionCheck(QtCore.QThread):
    """
    Thread to check if OctoPrint is online and responding.
    This runs during startup to ensure connectivity before enabling UI features.
    """
    # Define signals for connection status and progress
    loaded_signal = QtCore.pyqtSignal()
    startup_error_signal = QtCore.pyqtSignal()
    progress_signal = QtCore.pyqtSignal(int, str)  # Progress percentage and message

    def __init__(self, ip=None, api_key=None, virtual=False):
        """Initialize the sanity check thread"""
        super(ThreadConnectionCheck, self).__init__()
        self.ip = ip
        self.api_key = api_key
        self.MKSPort = None
        self.virtual = virtual
        self.shutdown_flag = False
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initialized ThreadConnectionCheck with IP: {}, API Key: {}, Virtual Mode: {}".format(
            self.ip, self.api_key, self.virtual))

    def run(self):
        """Run the sanity check to verify OctoPrint connectivity"""        
        self.shutdown_flag = False
        uptime = 0
        
        self.logger.info("Running OctoPrint connectivity check")
        self.progress_signal.emit(10, "Starting OctoPrint connection check...")
        
        # Keep trying until OctoPrint connects or timeout
        while True:
            try:
                # If we've been trying for more than 60 seconds, give up
                if uptime > 60:
                    self.shutdown_flag = True
                    self.logger.error("OctoPrint connection timeout after 60 seconds")
                    self.progress_signal.emit(0, "Connection timeout - Please check OctoPrint service")
                    self.startup_error_signal.emit()
                    break
                
                # Update progress based on time elapsed
                progress = min(20 + (uptime * 40 / 60), 60)  # Progress from 20% to 60% over 60 seconds
                self.progress_signal.emit(int(progress), f"Connecting Hardware...")
                # Attempt to connect to OctoPrint
                octoprint_singleton.initialize(self.ip, self.api_key)
                
                # If we're not in virtual mode, try to connect to the printer
                if not self.virtual:
                    try:
                        self.progress_signal.emit(75, "Connecting to Klipper ...")
                        # First try to connect to the Klipper printer
                        octoprint_singleton.get_client().connectPrinter(port="/tmp/printer", baudrate=115200)
                        self.logger.info("Connected to Klipper printer on /tmp/printer")
                        self.progress_signal.emit(85, "Connected to Klipper printer")
                    except Exception as e:
                        # If that fails, try to connect in virtual mode
                        self.logger.warning(f"Failed to connect to Klipper printer: {e}")
                        self.progress_signal.emit(80, "Falling back to virtual printer...")
                        # Attempt to connect in virtual mode
                        try:
                            octoprint_singleton.get_client().connectPrinter(port="VIRTUAL", baudrate=115200)
                            self.logger.info("Connected to printer in VIRTUAL mode")
                            self.progress_signal.emit(85, "Connected to virtual printer")
                        except Exception as e:
                            self.logger.error(f"Failed to connect to printer in VIRTUAL mode: {e}")
                            self.progress_signal.emit(85, "Printer connection failed - continuing...")

                # If we got here, connection was successful
                self.progress_signal.emit(90, "OctoPrint connection successful")
                break
                
            except Exception as e:
                # Wait 1 second before trying again
                time.sleep(1)
                uptime += 1
                self.logger.warning(f"OctoPrint connection attempt failed: {e}")
                
        # If we didn't set the shutdown flag, we were successful
        if not self.shutdown_flag:
            self.logger.info("OctoPrint connectivity check successful")
            self.progress_signal.emit(95, "Connection check completed")
            self.loaded_signal.emit()

class MainController:
    """
    Main controller for the OctoPrint Control Center application.
    This class manages the connection to the OctoPrint server and handles startup sanity checks.
    """

    def __init__(self):
        """
        Initialize the main controller with the given IP address and API key.
        
        :param ip: The IP address of the OctoPrint server.
        :param apiKey: The API key for authenticating with the OctoPrint server.
        :param on_loaded: Callback function to call when the sanity check is loaded successfully.
        :param on_error: Callback function to call if there is an error during the sanity check.
        """
        self.logger = get_logger(__name__)
        self.logger.info("Initializing MainController")
        self.dialogShown = False
        self.printer_model = PrinterModel()
        self.octoprint_client = None
        self.main_window = MainWindow(controller=self, printer_model=self.printer_model)

    def start(self):
        """Start the application and begin connection check"""
        self.logger.info("Starting application")
        try:
            self.updateLoadingProgress(5, "Initializing application...")
            self.connection_check = ThreadConnectionCheck(ip=ip, api_key=apiKey, virtual=False)
            self.connection_check.loaded_signal.connect(self.handleStartupSuccess)
            self.connection_check.startup_error_signal.connect(self.handleStartupError)
            self.connection_check.progress_signal.connect(self.updateLoadingProgress)  # Connect progress signal
            self.connection_check.start()
        except Exception as e:
            self.logger.error(f"Error during startup: {e}")
            dialog.WarningOk(self.main_window, f"Error during startup: {e}", overlay=True)
            self.main_window.close()

    def updateLoadingProgress(self, progress, message):
        """Update the loading screen progress"""
        self.main_window.loading_screen.update_progress(progress, message)

    def handleStartupSuccess(self):
        """Handle successful OctoPrint connection"""
        self.logger.info("OctoPrint connection successful")
        
        try:
            # Update progress for different startup phases
            self.updateLoadingProgress(96, "Initializing client...")
            
            # Now that we know OctoPrint is available, initialize the client
            self.octoprint_client = octoprint_singleton.get_client()
            
            self.updateLoadingProgress(97, "Loading user interface...")
            
            # Load the full UI
            self.main_window.loadUI(minimalUI=False)
            
            self.updateLoadingProgress(98, "Initializing websocket connection...")
            
            # Initialize websocket
            self.initalize_websocket()
            
            self.updateLoadingProgress(99, "Checking Klipper configuration...")
            
            # Check Klipper config
            self.checkKlipperPrinterCFG()
            
            self.updateLoadingProgress(100, "Startup complete!")

            self.main_window.switch_to_home_screen()
            
        except Exception as e:
            self.logger.error(f"Error during startup success handling: {e}")
            self.handleStartupError()

    def handleStartupError(self):
        """Handle OctoPrint connection failure"""
        self.logger.info("OctoPrint connection failed")
        try:
            self.updateLoadingProgress(0, "Connection failed - showing options...")
                
            if dialog.WarningYesNo(self.main_window, "Server Error, Restore failsafe settings?", overlay=True):
                self.logger.info("Restoring Failsafe Settings")
                
                self.updateLoadingProgress(25, "Restoring failsafe settings...")
                
                # Restore failsafe settings
                os.system('sudo rm -rf /home/pi/.octoprint/users.yaml')
                os.system('sudo rm -rf /home/pi/.octoprint/config.yaml')
                os.system('sudo cp -f config/users.yaml /home/pi/.octoprint/users.yaml')
                os.system('sudo cp -f config/config.yaml /home/pi/.octoprint/config.yaml')
                
                self.updateLoadingProgress(50, "Restarting OctoPrint service...")
                
                subprocess.call(["sudo", "systemctl", "restart", "octoprint"])
                
                self.updateLoadingProgress(10, "Retrying connection...")
                
                # Restart the connection check
                self.connection_check.start()
            else:
                self.logger.info("User chose not to restore failsafe settings")
                self.main_window.loadUI(minimalUI=True)
        except Exception as e:
            self.logger.error(f"Error in handleStartupError: {e}")
            dialog.WarningOk(self.main_window, f"Error in startup error handling: {e}", overlay=True)

    def onWebSocketConnected(self):
        """
        When the  on Web Socket server is connected, check for filament sensor and previous print failure to complere
        """
        self.logger.info("MainController.onWebSocketConnected started")

        if self.octoprint_client:
            try:
                self.octoprint_client.gcode(command='status') # Check if needed, unsure about what this does
                try:
                    response = self.octoprint_client.isFailureDetected()
                    if response["canRestore"] is True:
                        self.printRestoreMessageBox(response["file"])
                    else:
                        #RODO: Check for updates on startup if prefered
                        pass
                    
                except:
                    pass
            except Exception as e:
                self.logger.error("Error in MainController.onWebSocketConnected: {}".format(e))
                dialog.WarningOk(self.main_window, "Error in MainController.onWebSocketConnected: {}".format(e), overlay=True)
        

    def initalize_websocket(self):
        self.octoprint_websocket = OctoPrintWebSocket(ip=ip, api_key=apiKey)
        self.octoprint_websocket.start()

        # Connect signals from the websocket to the printer model
        self.octoprint_websocket.temperatures_signal.connect(self.printer_model.updateTemperature)
        self.octoprint_websocket.status_signal.connect(self.printer_model.updateStatus)
        self.octoprint_websocket.set_z_tool_offset_signal.connect(self.printer_model.setZToolOffset)
        self.octoprint_websocket.print_status_signal.connect(self.printer_model.updatePrintStatus)
        self.octoprint_websocket.update_started_signal.connect(self.printer_model.softwareUpdateProgress)
        self.octoprint_websocket.update_log_signal.connect(self.printer_model.softwareUpdateProgressLog)
        self.octoprint_websocket.update_log_result_signal.connect(self.printer_model.softwareUpdateResult)
        self.octoprint_websocket.update_failed_signal.connect(self.printer_model.updateFailed)
        self.octoprint_websocket.connected_signal.connect(self.onWebSocketConnected)  # function is defined in main only
        self.octoprint_websocket.filament_sensor_triggered_signal.connect(self.printer_model.filamentSensorHandler)
        self.octoprint_websocket.tool_offset_signal.connect(self.printer_model.getToolOffset)
        self.octoprint_websocket.active_extruder_signal.connect(self.printer_model.setActiveExtruder)
        self.octoprint_websocket.z_probe_offset_signal.connect(self.printer_model.updateEEPROMProbeOffset)
        self.octoprint_websocket.z_probing_failed_signal.connect(self.showProbingFailed)
        self.octoprint_websocket.printer_error_signal.connect(self.showPrinterError)



    def checkKlipperPrinterCFG(self):
        """
        Checks for valid printer.cfg and restores if needed, using utility functions.
        """
        if not self.octoprint_client:
            return
        try:
            if not klipper_cfg_utils.is_config_valid():
                self.logger.error("Printer Config File Corrupted or Not Found, Attempting to restore Backup")
                restored = klipper_cfg_utils.restore_backup_config()
                if restored:
                    self.logger.info("Printer Config File Restored from backup")
                    return
                # If no valid backups found, show error dialog:
                dialog.WarningOk(self.main_window,
                                 "Printer Config File corrupted. Contact Fracktal support or raise a ticket at care.fracktal.in")
                if self.printer_model.printer_status in ["Printing", "Paused"]:
                    self.octoprint_client.cancelPrint()
                    self.coolDownAction()
            else:
                self.logger.info("Printer Config File OK")
                klipper_cfg_utils.cleanup_old_backups()
        except Exception as e:
            self.logger.error(f"Error in MainController.checkKlipperPrinterCFG: {e}")
            dialog.WarningOk(self.main_window, f"Error in MainController.checkKlipperPrinterCFG: {e}", overlay=True)

    def coolDownAction(self):
        """'
        Turns all heaters and fans off
        """
        self.logger.info("MainController.coolDownAction started")
        try:
            self.octoprint_client.gcode(command='M107')
            self.octoprint_client.setToolTemperature({"tool0": 0, "tool1": 0})
            # octopiclient.setToolTemperature({"tool0": 0})
            self.octoprint_client.setBedTemperature(0)
            self.main_window.control_screen.toolTempSpinBox.setProperty("value", 0)
            self.main_window.control_screen.bedTempSpinBox.setProperty("value", 0)
        except Exception as e:
            self.logger.error("Error in MainController.coolDownAction: {}".format(e))
            dialog.WarningOk(self.main_window, "Error in MainController.coolDownAction: {}".format(e), overlay=True)

    def printRestoreMessageBox(self, file):
        """
        Displays a message box alerting the user of a filament error
        """
        self.logger.info("MainController.printRestoreMessageBox started")
        if self.octoprint_client:
            try:
                if dialog.WarningYesNo(self.main_window, file + " Did not finish, would you like to restore?"):
                    response = self.octoprint_client.restore(restore=True)
                    if response["status"] == "Successfully Restored":
                        dialog.WarningOk(self.main_window, response["status"])
                    else:
                        dialog.WarningOk(self.main_window, response["status"])
            except Exception as e:
                self.logger.error("Error in MainController.printRestoreMessageBox: {}".format(e))
                dialog.WarningOk(self.main_window, "Error in MainController.printRestoreMessageBox: {}".format(e), overlay=True)

    def showProbingFailed(self, msg='Probing Failed, Calibrate bed again or check for hardware issue', overlay=True):
        self.logger.info("MainController.showProbingFailed started")
        if self.octoprint_client:
            try:
                if dialog.WarningOk(self.main_window, msg, overlay=overlay):
                    self.octoprint_client.cancelPrint()
                    return True
                return False
            except Exception as e:
                self.logger.error("Error in MainController.showProbingFailed: {}".format(e))
                dialog.WarningOk(self.main_window, "Error in MainController.showProbingFailed: {}".format(e), overlay=True)

    def showPrinterError(self, msg='Printer error, Check Terminal', overlay=False):
        self.logger.info("MainController.showPrinterError started")
        if self.octoprint_client:
            try:
                if any(error in msg for error in CRITICAL_PRINTER_ERRORS):
                    self.logger.error("CRITICAL ERROR SHUTDOWN NEEDED")
                    # Check printer status through main_window.home_screen if available
                    if self.printer_model.printer_status in ["Starting", "Printing", "Paused"]:
                        self.octoprint_client.cancelPrint()
                        self.octoprint_client.gcode(command='M112')
                        try:
                            self.octoprint_client.connectPrinter(port="/tmp/printer", baudrate=115200)
                        except Exception as e:
                            self.octoprint_client.connectPrinter(port="VIRTUAL", baudrate=115200)
                        self.octoprint_client.gcode(command='FIRMWARE_RESTART')
                        self.octoprint_client.gcode(command='RESTART')
                        if not self.dialogShown:
                            self.dialogShown = True
                            if dialog.WarningOk(self.main_window, msg + ", Cancelling Print.", overlay=overlay):
                                self.dialogShown = False
                        self.logger.error("CRITICAL ERROR SHUTDOWN DONE")
                    else:
                        if not self.dialogShown:
                            self.dialogShown = True
                            self.octoprint_client.gcode(command='FIRMWARE_RESTART')
                            self.octoprint_client.gcode(command='RESTART')
                            if dialog.WarningOk(self.main_window, msg, overlay=overlay):
                                self.dialogShown = False

                else:
                    if not self.dialogShown:
                        self.dialogShown = True
                        if dialog.WarningOk(self.main_window, msg, overlay=overlay):
                            self.dialogShown = False

            except Exception as e:
                self.logger.error("Error in MainController.showPrinterError: {}".format(e))
                dialog.WarningOk(self.main_window, "Error in MainController.showPrinterError: {}".format(e), overlay=True)