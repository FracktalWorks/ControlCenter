"""Main controller module for OctoPrint Control Center.

This module contains the primary application controller that manages
OctoPrint connections, websocket communications, error handling, and
application startup/shutdown procedures.
"""

"""
To Implement Multiple Material Bays:"
Load each active material bay using update_tool_bay_state
and also set this up in Klipper Variables.
Depending on the state of the KLipper Variables, SYNC_EXTRUDER_MOTION
is set where ever applicable (homing overide, mirror/duplication modes etc)
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
from config import ip, apiKey, CRITICAL_PRINTER_ERRORS, IGNORED_PRINTER_ERRORS


logger = get_logger(__name__)

class ThreadConnectionCheck(QtCore.QThread):
    """Check if OctoPrint is online and responding.
    
    This thread runs during startup to ensure connectivity before enabling UI features.
    """
    # Define signals for connection status and progress
    loaded_signal = QtCore.pyqtSignal()
    startup_error_signal = QtCore.pyqtSignal()
    progress_signal = QtCore.pyqtSignal(int, str)  # Progress percentage and message
    virtual_fallback_signal = QtCore.pyqtSignal(str)  # Emitted when falling back to virtual printer

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
                            # Notify UI thread to show fallback dialog
                            self.virtual_fallback_signal.emit("There was an issue conencting to Klipper, conencted to Virtual Printer instead for diagnosis")
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

    # =========================================================================
    # SECTION: Initialization / Startup Lifecycle
    # =========================================================================

    def __init__(self):
        """Initialize controller state, model and main window."""
        self.logger = get_logger(__name__)
        self.logger.info("Initializing MainController")
        self.dialogShown = False
        self.printer_model = PrinterModel()
        self.octoprint_client = None
        self.main_window = MainWindow(controller=self, printer_model=self.printer_model)

    def start(self):
        """Kick off application startup and async connectivity check."""
        self.logger.info("Starting application")
        try:
            self.updateLoadingProgress(5, "Initializing application...")
            self.connection_check = ThreadConnectionCheck(ip=ip, api_key=apiKey, virtual=False)
            self.connection_check.loaded_signal.connect(self.handleStartupSuccess)
            self.connection_check.startup_error_signal.connect(self.handleStartupError)
            self.connection_check.progress_signal.connect(self.updateLoadingProgress)
            self.connection_check.virtual_fallback_signal.connect(self.handleVirtualFallback)
            self.connection_check.start()
        except Exception as e:
            self.logger.error(f"Error during startup: {e}")
            dialog.WarningOk(self.main_window, f"Error during startup: {e}", overlay=True)
            self.main_window.close()

    def updateLoadingProgress(self, progress, message):
        """Proxy progress updates to loading screen."""
        self.main_window.loading_screen.update_progress(progress, message)

    def handleStartupSuccess(self):
        """Complete startup after connectivity check passes."""
        self.logger.info("OctoPrint connection successful")
        try:
            self.updateLoadingProgress(96, "Initializing client...")
            self.octoprint_client = octoprint_singleton.get_client()
            self.updateLoadingProgress(97, "Loading user interface...")
            self.main_window.loadUI(minimalUI=False)
            self.updateLoadingProgress(98, "Initializing websocket connection...")
            self.initialize_websocket()
            self.updateLoadingProgress(99, "Checking Klipper configuration...")
            self.checkKlipperPrinterCFG()
            self.updateLoadingProgress(100, "Startup complete!")
            self.main_window.switch_to_home_screen()
        except Exception as e:
            self.logger.error(f"Error during startup success handling: {e}")
            self.handleStartupError()

    def handleVirtualFallback(self, message):
        """Show dialog if physical Klipper connection failed and virtual printer used."""
        try:
            self.logger.warning("Virtual printer fallback engaged: %s", message)
            dialog.WarningOk(self.main_window, message, overlay=True)
        except Exception as e:
            self.logger.error(f"Error showing virtual fallback dialog: {e}")

    def handleStartupError(self):
        """Display recovery options when OctoPrint isn't reachable."""
        self.logger.info("OctoPrint connection failed")
        try:
            self.updateLoadingProgress(0, "Connection failed - showing options...")
            if dialog.WarningYesNo(self.main_window, "Server Error, Restore failsafe settings?", overlay=True):
                self.logger.info("Restoring Failsafe Settings")
                self.updateLoadingProgress(25, "Restoring failsafe settings...")
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
                self.connection_check.start()
            else:
                self.logger.info("User chose not to restore failsafe settings")
                self.main_window.loadUI(minimalUI=True)
        except Exception as e:
            self.logger.error(f"Error in handleStartupError: {e}")
            dialog.WarningOk(self.main_window, f"Error in startup error handling: {e}", overlay=True)

    # =========================================================================
    # SECTION: Websocket / Connection Management
    # =========================================================================

    def initialize_websocket(self):
        """Start websocket and bind signals to model/controller."""
        self.octoprint_websocket = OctoPrintWebSocket(ip=ip, api_key=apiKey)
        self.octoprint_websocket.start()
        # Model signal wiring
        self.octoprint_websocket.temperatures_signal.connect(self.printer_model.updateTemperature)
        self.octoprint_websocket.status_signal.connect(self.printer_model.updateStatus)
        self.octoprint_websocket.set_z_tool_offset_signal.connect(self.printer_model.setZToolOffset)
        self.octoprint_websocket.print_status_signal.connect(self.printer_model.updatePrintStatus)
        self.octoprint_websocket.update_started_signal.connect(self.printer_model.softwareUpdateProgress)
        self.octoprint_websocket.update_log_signal.connect(self.printer_model.softwareUpdateProgressLog)
        self.octoprint_websocket.update_log_result_signal.connect(self.printer_model.softwareUpdateResult)
        self.octoprint_websocket.update_failed_signal.connect(self.printer_model.updateFailed)
        self.octoprint_websocket.tool_offset_signal.connect(self.printer_model.getToolOffset)
        self.octoprint_websocket.active_extruder_signal.connect(self.printer_model.setActiveExtruder)
        self.octoprint_websocket.z_probe_offset_signal.connect(self.printer_model.updateEEPROMProbeOffset)
        self.octoprint_websocket.klipper_state_signal.connect(self.printer_model.update_klipper_state)
        self.octoprint_websocket.filament_runout_state_signal.connect(self.printer_model.filamentRunoutState)
        # Controller signal wiring
        self.octoprint_websocket.connected_signal.connect(self.onWebSocketConnected)
        self.octoprint_websocket.filament_runout_sensor_triggered_signal.connect(self.filamentRunoutSensorTriggered)
        self.octoprint_websocket.filament_jam_sensor_triggered_signal.connect(self.filamentJamSensorTriggered)
        self.printer_model.filament_runout_state.connect(self.onFilamentRunoutState)
        self.octoprint_websocket.z_probing_failed_signal.connect(self.showProbingFailed)
        self.octoprint_websocket.printer_error_signal.connect(self.showPrinterError)
        # Print lifecycle events
        self.octoprint_websocket.print_cancelled_signal.connect(self.onPrintCancelled)
        self.octoprint_websocket.print_started_signal.connect(self.onPrintStarted)
        self.octoprint_websocket.print_resumed_signal.connect(self.onPrintResumed)
        self.octoprint_websocket.print_paused_signal.connect(self.onPrintPaused)

    def onWebSocketConnected(self):
        """Respond to websocket connection with status sync & sensor setup."""
        self.logger.info("MainController.onWebSocketConnected started")
        if self.octoprint_client:
            try:
                status_response = self.octoprint_client.gcode(command='status')
                if status_response:
                    self.logger.debug(f"Printer status response: {status_response}")
                try:
                    response = self.octoprint_client.isFailureDetected()
                    if response.get("canRestore"):
                        self.printRestoreMessageBox(response.get("file"))
                except (KeyError, TypeError, AttributeError) as e:
                    self.logger.warning(f"Failed to check for print failure: {e}")
                except Exception as e:
                    self.logger.error(f"Unexpected error checking print failure: {e}")
                try:
                    self.apply_filament_sensor_state()
                except Exception as e:
                    self.logger.warning(f"Failed applying initial filament sensor state: {e}")
            except Exception as e:
                self.logger.error(f"Error in MainController.onWebSocketConnected: {e}")
                dialog.WarningOk(self.main_window, f"Error in MainController.onWebSocketConnected: {e}", overlay=True)

    def checkKlipperPrinterCFG(self):
        """Validate printer.cfg; attempt restore or cleanup backups."""
        if not self.octoprint_client:
            return
        try:
            if not klipper_cfg_utils.is_config_valid():
                self.logger.error("Printer Config File Corrupted or Not Found, Attempting to restore Backup")
                if klipper_cfg_utils.restore_backup_config():
                    self.logger.info("Printer Config File Restored from backup")
                    return
                dialog.WarningOk(self.main_window, "Printer Config File corrupted. Contact Fracktal support or raise a ticket at care.fracktal.in")
                if self.printer_model.printer_status in ["Printing", "Paused"]:
                    self.octoprint_client.cancelPrint()
                    self.coolDownAction()
            else:
                self.logger.info("Printer Config File OK")
                klipper_cfg_utils.cleanup_old_backups()
        except Exception as e:
            self.logger.error(f"Error in MainController.checkKlipperPrinterCFG: {e}")
            dialog.WarningOk(self.main_window, f"Error in MainController.checkKlipperPrinterCFG: {e}", overlay=True)

    # =========================================================================
    # SECTION: Filament Sensor Management
    # =========================================================================

    def apply_filament_sensor_state(self):
        """Enable/disable sensors per preferences & active print state."""
        if not self.octoprint_client:
            return
        try:
            runout_pref = getattr(self.printer_model, 'filament_runout_sensor_persistent_state', False)
            jam_pref = getattr(self.printer_model, 'filament_jam_sensor_persistent_state', False)
            status = self.printer_model.printer_status
            active_printing = status in ["Printing"]
            desired_runout = 1 if (runout_pref and active_printing) else 0
            desired_jam = 1 if (jam_pref and active_printing) else 0
            self.octoprint_client.gcode(command=f'SET_FILAMENT_RUNOUT_SENSOR S{desired_runout}')
            self.octoprint_client.gcode(command=f'SET_FILAMENT_JAM_SENSOR S{desired_jam}')
            self.logger.info(f"Applied filament sensor state: runout={desired_runout} jam={desired_jam} (status={status})")
        except Exception as e:
            self.logger.error(f"Failed applying filament sensor state: {e}")

    def filamentRunoutSensorTriggered(self, tool):
        self.logger.info(f"Filament runout sensor triggered for tool: {tool}")
        # Future: pause print / prompt user

    def filamentJamSensorTriggered(self, tool):
        self.logger.info(f"Filament jam sensor triggered for tool: {tool}")
        # Future: pause / recovery logic

    def onFilamentRunoutState(self, sensor, state):
        self.logger.info(f"Filament runout state changed: {sensor} is {'present' if state else 'not present'}")

    # =========================================================================
    # SECTION: Print Lifecycle Events
    # =========================================================================

    def validate_gcode_compatibility(self, filename):
        """
        Validate GCODE file compatibility with current printer configuration.
        Returns (is_compatible, mismatches) where mismatches is a list of issues.
        """
        if not self.octoprint_client or not filename:
            return True, []

        try:
            # Extract metadata from GCODE file
            gcode_metadata = self.octoprint_client.getGcodeMetadata(filename)
            if not gcode_metadata:
                self.logger.warning(f"Could not extract metadata from {filename}, skipping validation")
                return True, []

            # Get current printer configuration
            current_config = self.printer_model.get_current_tool_config()
            
            mismatches = []
            
            # Check tool0 nozzle
            if gcode_metadata.get('nozzle_t0') is not None:
                expected_nozzle = gcode_metadata['nozzle_t0']
                current_nozzle = current_config['tool0']['nozzle']
                if current_nozzle != 'Unknown' and expected_nozzle != current_nozzle:
                    mismatches.append(f"Tool0 nozzle mismatch: GCODE expects {expected_nozzle}mm, printer has {current_nozzle}mm")

            # Check tool1 nozzle
            if gcode_metadata.get('nozzle_t1') is not None:
                expected_nozzle = gcode_metadata['nozzle_t1']
                current_nozzle = current_config['tool1']['nozzle']
                if current_nozzle != 'Unknown' and expected_nozzle != current_nozzle:
                    mismatches.append(f"Tool1 nozzle mismatch: GCODE expects {expected_nozzle}mm, printer has {current_nozzle}mm")

            # Check tool0 material
            if gcode_metadata.get('material_t0') is not None:
                expected_material = gcode_metadata['material_t0']
                current_material = current_config['tool0']['material']
                if current_material is not None and expected_material != current_material:
                    mismatches.append(f"Tool0 material mismatch: GCODE expects {expected_material}, printer has {current_material}")

            # Check tool1 material
            if gcode_metadata.get('material_t1') is not None:
                expected_material = gcode_metadata['material_t1']
                current_material = current_config['tool1']['material']
                if current_material is not None and expected_material != current_material:
                    mismatches.append(f"Tool1 material mismatch: GCODE expects {expected_material}, printer has {current_material}")

            is_compatible = len(mismatches) == 0
            self.logger.info(f"GCODE compatibility check for {filename}: {'PASS' if is_compatible else 'FAIL'}")
            if mismatches:
                self.logger.warning(f"Compatibility issues found: {mismatches}")
            
            return is_compatible, mismatches

        except Exception as e:
            self.logger.error(f"Error validating GCODE compatibility: {e}")
            return True, []  # Default to compatible on error

    def onPrintStarted(self, event):
        try:
            self.logger.info("MainController.onPrintStarted invoked")
            self.logger.debug(f"PrintStarted event data: {event}")
            
            # Check GCODE compatibility if enabled and we have file information
            # According to OctoPrint docs, PrintStarted event contains: name, path, origin, size, owner, user
            if (self.printer_model.print_compatibility_check_enabled and event):
                filename = event.get('name')  # Direct access to filename from event payload
                
                if filename:
                    self.logger.info(f"Validating GCODE compatibility for file: {filename}")
                    is_compatible, mismatches = self.validate_gcode_compatibility(filename)
                    
                    if not is_compatible:
                        # Pause the print immediately (if not already paused)
                        if self.octoprint_client:
                            try:
                                job_info = self.octoprint_client.getJobInformation()
                                if job_info and job_info.get('state') not in ['Paused', 'Pausing']:
                                    self.octoprint_client.pausePrint()
                            except Exception as e:
                                self.logger.error(f"Error pausing print: {e}")
                                # Try to pause anyway
                                self.octoprint_client.pausePrint()
                        
                        # Show dialog with mismatch information
                        mismatch_text = "Print configuration mismatch detected:\n\n" + "\n".join(mismatches)
                        mismatch_text += "\n\nWould you like to continue printing anyway?"
                        
                        if dialog.WarningYesNo(self.main_window, mismatch_text, overlay=True):
                            # User wants to continue - resume the print
                            self.logger.info("User chose to continue print despite mismatches")
                            if self.octoprint_client:
                                self.octoprint_client.startPrint()  # Resume from pause
                        else:
                            # User wants to cancel - cancel the print
                            self.logger.info("User chose to cancel print due to mismatches")
                            if self.octoprint_client:
                                self.octoprint_client.cancelPrint()
                            return
                else:
                    self.logger.warning("PrintStarted event received but no filename found in event data")
            elif not self.printer_model.print_compatibility_check_enabled:
                self.logger.info("Print compatibility check is disabled, skipping validation")
            
            # Apply filament sensor state if print continues
            self.apply_filament_sensor_state()
            
        except Exception as e:
            self.logger.error(f"Error in onPrintStarted: {e}")

    def onPrintResumed(self, event):
        try:
            self.logger.info("MainController.onPrintResumed invoked")
            self.apply_filament_sensor_state()
        except Exception as e:
            self.logger.error(f"Error in onPrintResumed: {e}")

    def onPrintPaused(self, event):
        try:
            self.logger.info("MainController.onPrintPaused invoked")
            if self.octoprint_client:
                self.octoprint_client.gcode(command='SET_FILAMENT_RUNOUT_SENSOR S0')
                self.octoprint_client.gcode(command='SET_FILAMENT_JAM_SENSOR S0')
        except Exception as e:
            self.logger.error(f"Error in onPrintPaused: {e}")

    def onPrintCancelled(self, event):
        try:
            self.logger.info("MainController.onPrintCancelled invoked")
            if self.octoprint_client:
                self.octoprint_client.gcode(command='SET_FILAMENT_RUNOUT_SENSOR S0')
                self.octoprint_client.gcode(command='SET_FILAMENT_JAM_SENSOR S0')
        except Exception as e:
            self.logger.error(f"Error in onPrintCancelled: {e}")

    # =========================================================================
    # SECTION: Error & Recovery Dialogs
    # =========================================================================

    def showProbingFailed(self, msg='Probing Failed, Calibrate bed again or check for hardware issue', overlay=True):
        self.logger.info("MainController.showProbingFailed started")
        if self.octoprint_client:
            try:
                if dialog.WarningOk(self.main_window, msg, overlay=overlay):
                    self.octoprint_client.cancelPrint()
                    return True
                return False
            except Exception as e:
                self.logger.error(f"Error in MainController.showProbingFailed: {e}")
                dialog.WarningOk(self.main_window, f"Error in MainController.showProbingFailed: {e}", overlay=True)

    def showPrinterError(self, msg='Printer error, Check Terminal', overlay=False):
        self.logger.info("MainController.showPrinterError started")
        cleaned_msg = msg.strip()
        while cleaned_msg.startswith('!'):
            cleaned_msg = cleaned_msg[1:].lstrip()
        self.logger.error(f"Printer error received: {msg}")
        self.logger.debug(f"Cleaned message for processing: {cleaned_msg}")
        for ignore_item in IGNORED_PRINTER_ERRORS:
            if ignore_item in cleaned_msg:
                self.logger.debug(f"Ignoring error message for UI display: {cleaned_msg}")
                return
        if self.octoprint_client:
            try:
                if any(error in cleaned_msg for error in CRITICAL_PRINTER_ERRORS):
                    self.logger.error("CRITICAL ERROR SHUTDOWN NEEDED")
                    if self.printer_model.printer_status in ["Starting", "Printing", "Paused"]:
                        self.octoprint_client.cancelPrint()
                        self.octoprint_client.gcode(command='M112')
                        try:
                            self.octoprint_client.connectPrinter(port="/tmp/printer", baudrate=115200)
                        except Exception:
                            self.octoprint_client.connectPrinter(port="VIRTUAL", baudrate=115200)
                        self.octoprint_client.gcode(command='FIRMWARE_RESTART')
                        self.octoprint_client.gcode(command='RESTART')
                        if not self.dialogShown:
                            self.dialogShown = True
                            if dialog.WarningOk(self.main_window, cleaned_msg + ", Cancelling Print.", overlay=overlay):
                                self.dialogShown = False
                        self.logger.error("CRITICAL ERROR SHUTDOWN DONE")
                    else:
                        if not self.dialogShown:
                            self.dialogShown = True
                            self.octoprint_client.gcode(command='FIRMWARE_RESTART')
                            self.octoprint_client.gcode(command='RESTART')
                            if dialog.WarningOk(self.main_window, cleaned_msg, overlay=overlay):
                                self.dialogShown = False
                else:
                    if not self.dialogShown:
                        self.dialogShown = True
                        if dialog.WarningOk(self.main_window, cleaned_msg, overlay=overlay):
                            self.dialogShown = False
            except Exception as e:
                self.logger.error(f"Error in MainController.showPrinterError: {e}")
                dialog.WarningOk(self.main_window, f"Error in MainController.showPrinterError: {e}", overlay=True)

    def printRestoreMessageBox(self, file):
        self.logger.info("MainController.printRestoreMessageBox started")
        if self.octoprint_client:
            try:
                if dialog.WarningYesNo(self.main_window, file + " Did not finish, would you like to restore?"):
                    response = self.octoprint_client.restore(restore=True)
                    dialog.WarningOk(self.main_window, response.get("status", "Unknown status"))
            except Exception as e:
                self.logger.error(f"Error in MainController.printRestoreMessageBox: {e}")
                dialog.WarningOk(self.main_window, f"Error in MainController.printRestoreMessageBox: {e}", overlay=True)

    # =========================================================================
    # SECTION: Utility / Convenience Actions
    # =========================================================================

    def coolDownAction(self):
        self.logger.info("MainController.coolDownAction started")
        try:
            self.octoprint_client.gcode(command='M107')
            self.octoprint_client.setToolTemperature({"tool0": 0, "tool1": 0})
            self.octoprint_client.setBedTemperature(0)
            self.main_window.control_screen.toolTempSpinBox.setProperty("value", 0)
            self.main_window.control_screen.bedTempSpinBox.setProperty("value", 0)
        except Exception as e:
            self.logger.error(f"Error in MainController.coolDownAction: {e}")
            dialog.WarningOk(self.main_window, f"Error in MainController.coolDownAction: {e}", overlay=True)