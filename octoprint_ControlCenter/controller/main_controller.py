"""Main controller module for OctoPrint Control Center.

This module contains the primary application controller that manages
OctoPrint connections, websocket communications, error handling, and
application startup/shutdown procedures.
"""
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
from utils.helpers import run_async
from utils import dialog
from ui.loading_screen.loading_screen import LoadingScreen
from config import ip, apiKey, CRITICAL_PRINTER_ERRORS


logger = get_logger(__name__)

class ThreadConnectionCheck(QtCore.QThread):
    """Check if OctoPrint is online and responding.
    
    This thread runs during startup to ensure connectivity before enabling UI features.
    """
    # Define signals for connection status and progress
    loaded_signal = QtCore.pyqtSignal()
    startup_error_signal = QtCore.pyqtSignal()
    progress_signal = QtCore.pyqtSignal(int, str)  # Progress percentage and message

    def __init__(self, ip=None, api_key=None, virtual=False):
        """Initialize the connection check thread.
        
        Args:
            ip: IP address of the OctoPrint server.
            api_key: API key for authentication.
            virtual: Whether to use virtual mode.
        """
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
        """Run the connectivity check to verify OctoPrint is accessible.
        
        Attempts to connect to OctoPrint with a 60-second timeout. If connection
        fails, emits startup_error_signal. On success, emits loaded_signal.
        """        
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
                self.progress_signal.emit(int(progress), f"Connecting hardware, attempt {uptime + 1}/60")
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
    """Main controller for the OctoPrint Control Center application.
    
    Manages the connection to the OctoPrint server and handles startup
    initialization, error recovery, and websocket communications.
    """

    def __init__(self):
        """Initialize the main controller.
        
        Sets up the logger, printer model, and main window components.
        """
        self.logger = get_logger(__name__)
        self.logger.info("Initializing MainController")
        self.dialogShown = False
        self.printer_model = PrinterModel()
        self.octoprint_client = None
        self.main_window = MainWindow(controller=self, printer_model=self.printer_model)

    def start(self):
        """Start the application and begin connection check.
        
        Initializes the connection check thread and connects signal handlers.
        Shows error dialog and closes application if startup fails.
        """
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
        """Update the loading screen progress.
        
        Args:
            progress: Progress percentage (0-100).
            message: Status message to display.
        """
        self.main_window.loading_screen.update_progress(progress, message)

    def handleStartupSuccess(self):
        """Handle successful OctoPrint connection.
        
        Initializes the OctoPrint client, loads the UI, establishes websocket
        connection, checks Klipper configuration, and switches to home screen.
        """
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
            self.initialize_websocket()
            
            self.updateLoadingProgress(99, "Checking Klipper configuration...")
            
            # Check Klipper config
            self.checkKlipperPrinterCFG()
            
            self.updateLoadingProgress(100, "Startup complete!")

            self.main_window.switch_to_home_screen()
            
        except Exception as e:
            self.logger.error(f"Error during startup success handling: {e}")
            self.handleStartupError()

    def handleStartupError(self):
        """Handle OctoPrint connection failure.
        
        Prompts user to restore failsafe settings or load minimal UI.
        If user chooses to restore, attempts to restore configuration files
        and restart OctoPrint service.
        """
        self.logger.info("OctoPrint connection failed")
        try:
            self.updateLoadingProgress(0, "Connection failed - showing options...")
                
            if dialog.WarningYesNo(self.main_window, "Server Error, Restore failsafe settings?", overlay=True):
                self.logger.info("Restoring Failsafe Settings")
                
                self.updateLoadingProgress(25, "Restoring failsafe settings...")
                
                # Restore failsafe settings
                try:
                    subprocess.run(["sudo", "rm", "-rf", "/home/pi/.octoprint/users.yaml"], check=True)
                    subprocess.run(["sudo", "rm", "-rf", "/home/pi/.octoprint/config.yaml"], check=True)
                    subprocess.run(["sudo", "cp", "-f", "config/users.yaml", "/home/pi/.octoprint/users.yaml"], check=True)
                    subprocess.run(["sudo", "cp", "-f", "config/config.yaml", "/home/pi/.octoprint/config.yaml"], check=True)
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Failed to restore failsafe settings: {e}")
                    dialog.WarningOk(self.main_window, f"Failed to restore settings: {e}", overlay=True)
                    return
                
                self.updateLoadingProgress(50, "Restarting OctoPrint service...")
                
                try:
                    subprocess.run(["sudo", "systemctl", "restart", "octoprint"], check=True)
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Failed to restart OctoPrint service: {e}")
                    dialog.WarningOk(self.main_window, f"Failed to restart service: {e}", overlay=True)
                
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
        """Handle websocket connection establishment.
        
        Checks printer status, detects previous print failures, and offers
        print restoration if applicable. Called when websocket connects.
        """
        self.logger.info("MainController.onWebSocketConnected started")

        if self.octoprint_client:
            try:
                # Send status command to check printer state
                status_response = self.octoprint_client.gcode(command='status')
                if status_response:
                    self.logger.debug(f"Printer status response: {status_response}")
                try:
                    response = self.octoprint_client.isFailureDetected()
                    if response["canRestore"] is True:
                        self.printRestoreMessageBox(response["file"])
                    else:
                        #TODO: Check for updates on startup if preferred
                        pass
                    
                except (KeyError, TypeError, AttributeError) as e:
                    self.logger.warning(f"Failed to check for print failure: {e}")
                except Exception as e:
                    self.logger.error(f"Unexpected error checking print failure: {e}")
            except Exception as e:
                self.logger.error("Error in MainController.onWebSocketConnected: {}".format(e))
                dialog.WarningOk(self.main_window, "Error in MainController.onWebSocketConnected: {}".format(e), overlay=True)
        

    def initialize_websocket(self):
        """Initialize websocket connection and signal bindings.
        
        Creates OctoPrint websocket client and connects all websocket signals
        to appropriate handlers in the printer model and main controller.
        """
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
        """Check for valid printer.cfg and restore if needed.
        
        Validates the Klipper printer configuration file and attempts to
        restore from backup if corrupted. Cancels active print and cools
        down if configuration is invalid.
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
        """Turn off all heaters and fans.
        
        Sends commands to disable all heating elements and fans, then updates
        the UI temperature controls to reflect the zero values.
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
        """Display a message box for print restoration options.
        
        Args:
            file: Name of the file that did not finish printing.
            
        Shows a dialog asking if the user wants to restore a failed print
        and handles the restoration process if confirmed.
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
        """Show probing failure dialog and handle response.
        
        Args:
            msg: Error message to display to the user.
            overlay: Whether to show dialog as overlay.
            
        Returns:
            bool: True if user acknowledged the error, False otherwise.
            
        Displays an error dialog for probing failures and cancels the current
        print if user confirms.
        """
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
        """Show printer error dialog and handle critical errors.
        
        Args:
            msg: Error message to display to the user.
            overlay: Whether to show dialog as overlay.
            
        Displays printer error messages and performs emergency shutdown
        procedures for critical errors. Handles dialog state to prevent
        multiple simultaneous error dialogs.
        """
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