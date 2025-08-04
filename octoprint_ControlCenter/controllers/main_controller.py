import time
import requests
import os
import subprocess
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from utils.logger import get_logger
from models.printer_model import PrinterModel
from octoprint_client import octoprint_singleton
from octoprint_client.websocket_client import OctoPrintWebSocket
from controllers.connection_controller import ConnectionController
import config
from config import ip, apiKey
from utils import klipper_cfg_utils
from utils import dialog


logger = get_logger(__name__)


class MainController(QObject):
    """
    Controller class that handles core application logic, OctoPrint communication,
    and system operations, separated from UI concerns.
    """
    
    # Signals for communication with UI
    startup_success = pyqtSignal()
    startup_error = pyqtSignal()
    connection_established = pyqtSignal()
    printer_error = pyqtSignal(str, bool)  # message, overlay
    probing_failed = pyqtSignal(str, bool)  # message, overlay
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing MainController")
        
        # Core components
        self.octoprint_client = None
        self.octoprint_websocket = None
        self.printer_model = PrinterModel()
        
        # UI components - controller owns the views
        self.main_window = None
        self.loading_screen = None
        
        # Connection management
        self.connection_controller = ConnectionController()
        
        # Application state
        self.minimal_ui_mode = False
        self.dialog_shown = False
    
    def start_application(self):
        """Start the application by showing loading screen and beginning connection attempt."""
        logger.info("Starting application with loading screen")
        
        # Create and show loading screen
        from ui.loading_screen.loading_screen import LoadingScreen
        self.loading_screen = LoadingScreen(controller=self)
        self.loading_screen.show()
        
        # Connect connection controller signals
        self._connect_connection_signals()
        
        # Start connection attempt
        self.start_connection_check()
    
    def _connect_connection_signals(self):
        """Connect signals from the connection controller."""
        self.connection_controller.connection_established.connect(self.on_connection_success)
        self.connection_controller.connection_failed.connect(self.on_connection_failed)
        self.connection_controller.connection_status_changed.connect(self._on_connection_status_changed)
    
    def _on_connection_status_changed(self, status):
        """Handle connection status updates."""
        logger.debug(f"Connection status: {status}")
        # Update loading screen with current status if possible
        self._update_loading_status(status)
        
        # Provide incremental progress updates during connection
        if self.loading_screen and hasattr(self.loading_screen, 'increment_progress'):
            if "ongoing" in status.lower() or "attempt" in status.lower():
                self.loading_screen.increment_progress(2)  # Small increments during connection
    
    def _update_loading_status(self, status, progress_step=None):
        """
        Update the loading screen status and progress if available.
        
        Args:
            status (str): Status message to display
            progress_step (str): Optional progress step name for progress bar
        """
        if self.loading_screen and hasattr(self.loading_screen, 'update_status'):
            self.loading_screen.update_status(status, progress_step)
    
    def start_connection_check(self):
        """Start the OctoPrint connection check via connection controller."""
        logger.info("Starting OctoPrint connection check")
        self._update_loading_status("Connecting to OctoPrint...", 'connecting')
        
        # Check if we should force connection failure for testing
        if hasattr(config, 'FORCE_CONNECTION_FAILURE') and config.FORCE_CONNECTION_FAILURE:
            logger.info("FORCE_CONNECTION_FAILURE is enabled - skipping connection and going to minimal UI")
            self._update_loading_status("Simulating connection failure...", 'connecting')
            # Use a timer to simulate the delay before failure
            QTimer.singleShot(3000, lambda: self.on_connection_failed())
            return
        
        # Start periodic progress updates during connection
        self._start_connection_progress_updates()
        
        # Use a shorter timeout for testing purposes - change back to 60 if needed
        connection_timeout = 20  # 20 seconds for easier testing
        self.connection_controller.start_connection_attempt(virtual=False, timeout=connection_timeout)
        
        # Add a safety timeout in case connection thread doesn't respond
        self.safety_timeout_timer = QTimer()
        self.safety_timeout_timer.setSingleShot(True)
        self.safety_timeout_timer.timeout.connect(self._on_safety_timeout)
        self.safety_timeout_timer.start((connection_timeout + 5) * 1000)  # 5 seconds extra buffer
    
    def _on_safety_timeout(self):
        """Handle safety timeout when connection takes too long."""
        logger.warning("Safety timeout reached - forcing connection failure")
        self._update_loading_status("Connection timeout. Loading offline mode...")
        
        # Stop the connection controller
        if hasattr(self, 'connection_controller'):
            self.connection_controller.stop_connection_attempt()
        
        # Force minimal UI mode
        self.on_connection_failed()
    
    def _start_connection_progress_updates(self):
        """Start periodic progress updates during connection attempts."""
        self.connection_progress_timer = QTimer()
        self.connection_progress_counter = 0
        
        def update_connection_progress():
            self.connection_progress_counter += 1
            
            # Update status message based on time elapsed
            if self.connection_progress_counter <= 5:
                status_msg = "Connecting to OctoPrint..."
            elif self.connection_progress_counter <= 10:
                status_msg = "Waiting for OctoPrint response..."
            elif self.connection_progress_counter <= 15:
                status_msg = "Still trying to connect..."
            else:
                status_msg = f"Connection attempt {self.connection_progress_counter}s..."
            
            self._update_loading_status(status_msg)
            
            if self.loading_screen and hasattr(self.loading_screen, 'increment_progress'):
                # Small increments during connection (max 2% per second to avoid hitting 100%)
                if self.loading_screen.current_progress < 45:  # Don't go past authenticating stage
                    self.loading_screen.increment_progress(2)
            
            # Stop after 25 seconds of updates (longer than connection timeout)
            if self.connection_progress_counter >= 25:
                self.connection_progress_timer.stop()
        
        self.connection_progress_timer.timeout.connect(update_connection_progress)
        self.connection_progress_timer.start(1000)  # Update every second
    
    def on_connection_success(self):
        """Handle successful OctoPrint connection."""
        logger.info("OctoPrint connection successful - enabling full UI mode")
        
        # Update status with authentication step
        self._update_loading_status("Connection established. Authenticating...", 'authenticating')
        
        # Add a small delay to show the authentication step
        QTimer.singleShot(800, self._continue_successful_connection)
    
    def _continue_successful_connection(self):
        """Continue the successful connection process after showing authentication."""
        # Stop the connection progress timer and safety timeout
        if hasattr(self, 'connection_progress_timer'):
            self.connection_progress_timer.stop()
        if hasattr(self, 'safety_timeout_timer'):
            self.safety_timeout_timer.stop()
        
        # Initialize main window first (while loading screen is still showing)
        self.initialize_ui()
        
        # Enable full UI mode and fully load all screens
        self._update_loading_status("Loading application screens...", 'loading_ui')
        
        # Add delay to show loading UI step
        QTimer.singleShot(1000, self._finalize_successful_connection)
    
    def _finalize_successful_connection(self):
        """Finalize the successful connection process."""
        self.enable_full_ui_mode()
        
        # Only after everything is loaded, show main window and hide loading screen
        if self.main_window:
            self._update_loading_status("Finalizing...", 'finalizing')
            self.main_window.show()
            logger.info("Main window displayed - hiding loading screen")
        
        # Complete the progress and hide loading screen
        if self.loading_screen:
            self.loading_screen.complete_progress()
            # Give a brief moment to show completion before hiding
            QTimer.singleShot(1000, lambda: (
                self.loading_screen.hide(),
                logger.info("Loading screen hidden after main window is ready")
            ))
    
    def on_connection_failed(self):
        """Handle failed OctoPrint connection."""
        logger.info("OctoPrint connection failed - enabling minimal UI mode")
        
        # Update status with connection failure
        self._update_loading_status("Connection failed. Loading basic interface...", 'loading_ui')
        
        # Add delay to show the failure message
        QTimer.singleShot(1000, self._continue_failed_connection)
    
    def _continue_failed_connection(self):
        """Continue the failed connection process after showing error."""
        # Stop the connection progress timer and safety timeout
        if hasattr(self, 'connection_progress_timer'):
            self.connection_progress_timer.stop()
        if hasattr(self, 'safety_timeout_timer'):
            self.safety_timeout_timer.stop()
        
        # Initialize main window first (while loading screen is still showing)
        self.initialize_ui()
        
        # Enable minimal UI mode
        self.enable_minimal_ui_mode()
        
        # Only after everything is loaded, show main window and hide loading screen
        if self.main_window:
            self._update_loading_status("Ready in offline mode!", 'finalizing')
            self.main_window.show()
            logger.info("Main window displayed in minimal mode - hiding loading screen")
        
        # Complete the progress and hide loading screen after a brief delay
        if self.loading_screen:
            # Set progress to indicate offline mode (75% to show incomplete)
            self.loading_screen.animate_progress_to(75, "Offline mode ready", 800)
            QTimer.singleShot(2000, lambda: (
                self.loading_screen.hide(),
                logger.info("Loading screen hidden after minimal UI is ready")
            ))
    
    def initialize_ui(self):
        """Initialize and return the main window UI."""
        if self.main_window is None:
            self._update_loading_status("Creating main window...")
            # Import here to avoid circular imports
            from ui.main_window import MainWindow
            
            # Show incremental progress during UI creation
            if self.loading_screen and hasattr(self.loading_screen, 'increment_progress'):
                self.loading_screen.increment_progress(5)
            
            self.main_window = MainWindow(controller=self)
            logger.info("MainWindow created and assigned to controller")
            
            # Ensure main window has proper size
            import config
            self.main_window.resize(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
            
            # Increment progress to show UI creation progress
            if self.loading_screen and hasattr(self.loading_screen, 'increment_progress'):
                self.loading_screen.increment_progress(10)
            
            self._update_loading_status("Main window created...")
        return self.main_window
    
    def _initialize_octoprint(self, emit_signals=True):
        """Initialize the OctoPrint singleton and client."""
        try:
            logger.info("Initializing OctoPrint singleton")
            octoprint_singleton.initialize(config.ip, config.apiKey)
            self.octoprint_client = octoprint_singleton.get_client()
            logger.info("OctoPrint singleton initialized successfully")
            if emit_signals:
                self.startup_success.emit()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OctoPrint singleton: {e}")
            if emit_signals:
                self.startup_error.emit()
            raise  # Re-raise the exception so caller can handle it
    
    def handle_startup_error(self):
        """Handle startup errors by offering to restore failsafe settings."""
        logger.info("MainController.handle_startup_error started")
        try:
            # This would typically show a dialog, but we'll emit a signal for the UI to handle
            return True  # Return True if user wants to restore settings
        except Exception as e:
            logger.error(f"Error in MainController.handle_startup_error: {e}")
            return False
    
    def restore_failsafe_settings(self):
        """Restore failsafe OctoPrint settings."""
        logger.info("Restoring Failsafe Settings")
        try:
            os.system('sudo rm -rf /home/pi/.octoprint/users.yaml')
            os.system('sudo rm -rf /home/pi/.octoprint/config.yaml')
            os.system('sudo cp -f config/users.yaml /home/pi/.octoprint/users.yaml')
            os.system('sudo cp -f config/config.yaml /home/pi/.octoprint/config.yaml')
            subprocess.call(["sudo", "systemctl", "restart", "octoprint"])
            return True
        except Exception as e:
            logger.error(f"Error restoring failsafe settings: {e}")
            return False
    
    def enable_minimal_ui_mode(self):
        """Enable minimal UI mode due to connection issues."""
        logger.info("Enabling minimal UI mode due to startup error")
        self.minimal_ui_mode = True
        
        # Directly call the UI method instead of emitting signal
        if self.main_window:
            logger.info("Calling showMinimalUI on main window")
            self.main_window.showMinimalUI()
            
            # Ensure home screen is loaded and displayed properly even in minimal mode
            logger.info("Ensuring home screen is properly loaded in minimal mode")
            self.main_window.switch_to_home_screen()
        else:
            logger.warning("Main window not available for showMinimalUI call")
        print(".......LOADED IN MINIMAL MODE .......")
    
    def enable_full_ui_mode(self):
        """Enable full UI mode when OctoPrint connection is successful."""
        logger.info("Enabling full UI mode - OctoPrint connection successful")
        
        # Initialize OctoPrint connection since the connection thread verified it's accessible
        try:
            self._initialize_octoprint(emit_signals=False)
        except Exception as e:
            logger.error(f"Failed to initialize OctoPrint after successful connection check: {e}")
            # Fall back to minimal UI mode
            self.enable_minimal_ui_mode()
            return
        
        self.minimal_ui_mode = False
        
        # Directly call the UI method instead of emitting signal
        if self.main_window:
            self.main_window.loadFullUI()
            logger.info("Full UI loaded - ensuring home screen is properly set up")
            
            # Ensure home screen is loaded and displayed
            self.main_window.switch_to_home_screen()
            
        print(".......LOADED IN FULL MODE .......")
        
        # Initialize websocket connection
        self._initialize_websocket()
        
        # Perform post-connection checks
        self._perform_startup_checks()
    
    def _initialize_websocket(self):
        """Initialize and connect websocket signals to printer model."""
        if not self.octoprint_websocket:
            self.octoprint_websocket = OctoPrintWebSocket()
            self.octoprint_websocket.start()
            
            # Connect websocket signals to printer model
            self.octoprint_websocket.temperatures_signal.connect(self.printer_model.updateTemperature)
            self.octoprint_websocket.status_signal.connect(self.printer_model.updateStatus)
            self.octoprint_websocket.set_z_tool_offset_signal.connect(self.printer_model.setZToolOffset)
            self.octoprint_websocket.print_status_signal.connect(self.printer_model.updatePrintStatus)
            self.octoprint_websocket.update_started_signal.connect(self.printer_model.softwareUpdateProgress)
            self.octoprint_websocket.update_log_signal.connect(self.printer_model.softwareUpdateProgressLog)
            self.octoprint_websocket.update_log_result_signal.connect(self.printer_model.softwareUpdateResult)
            self.octoprint_websocket.update_failed_signal.connect(self.printer_model.updateFailed)
            self.octoprint_websocket.connected_signal.connect(self.on_server_connected)
            self.octoprint_websocket.filament_sensor_triggered_signal.connect(self.printer_model.filamentSensorHandler)
            self.octoprint_websocket.tool_offset_signal.connect(self.printer_model.getToolOffset)
            self.octoprint_websocket.active_extruder_signal.connect(self.printer_model.setActiveExtruder)
            self.octoprint_websocket.z_probe_offset_signal.connect(self.printer_model.updateEEPROMProbeOffset)
            self.octoprint_websocket.z_probing_failed_signal.connect(self.show_probing_failed)
            self.octoprint_websocket.printer_error_signal.connect(self.show_printer_error)
    
    def _perform_startup_checks(self):
        """Perform various startup checks after successful connection."""
        self.check_klipper_printer_cfg()
    
    def check_klipper_printer_cfg(self):
        """Check for valid printer.cfg and restore if needed."""
        logger.info("MainController.check_klipper_printer_cfg started")
        if not self.octoprint_client:
            return
        
        try:
            if not klipper_cfg_utils.is_config_valid():
                logger.error("Printer Config File Corrupted or Not Found, Attempting to restore Backup")
                restored = klipper_cfg_utils.restore_backup_config()
                if restored:
                    logger.info("Printer Config File Restored from backup")
                    return
                
                # If no valid backups found, show error dialog
                # Emit signal for UI to handle
                self.printer_error.emit(
                    "Printer Config File corrupted. Contact Fracktal support or raise a ticket at care.fracktal.in",
                    True
                )
                
                if getattr(self.printer_model, 'printerStatus', None) == "Printing":
                    self.octoprint_client.cancelPrint()
                    # Signal control screen to cool down (UI responsibility)
            else:
                logger.info("Printer Config File OK")
                klipper_cfg_utils.cleanup_old_backups()
        except Exception as e:
            logger.error(f"Error in MainController.check_klipper_printer_cfg: {e}")
            self.printer_error.emit(f"Error in check_klipper_printer_cfg: {e}", True)
    
    def on_server_connected(self):
        """Handle server connection event."""
        logger.info("MainController.on_server_connected started")
        if not self.octoprint_client:
            return
        
        try:
            self.octoprint_client.gcode(command='status')
            self.is_filament_sensor_installed()
            
            try:
                response = self.octoprint_client.isFailureDetected()
                if response["canRestore"] is True:
                    self.handle_print_restore(response["file"])
            except:
                pass  # Firmware update functionality not needed for Twin Dragon
        except Exception as e:
            logger.error(f"Error in MainController.on_server_connected: {e}")
    
    def is_filament_sensor_installed(self):
        """Check if the filament sensor is installed."""
        logger.info("MainController.is_filament_sensor_installed started")
        if not self.octoprint_client:
            return False
        
        try:
            success = False
            try:
                headers = {'X-Api-Key': apiKey}
                req = requests.get(f'http://{ip}/plugin/Julia2018FilamentSensor/status', headers=headers)
                success = req.status_code == requests.codes.ok
            except:
                pass
            
            return success
        except Exception as e:
            logger.error(f"Error in MainController.is_filament_sensor_installed: {e}")
            return False
    
    def handle_print_restore(self, filename):
        """Handle print restoration after filament error."""
        logger.info("MainController.handle_print_restore started")
        if not self.octoprint_client:
            return
        
        try:
            # This would typically show a dialog, but we'll emit a signal for the UI to handle
            # For now, return the response for the UI to handle
            return {
                'filename': filename,
                'message': f"{filename} Did not finish, would you like to restore?"
            }
        except Exception as e:
            logger.error(f"Error in MainController.handle_print_restore: {e}")
            return None
    
    def restore_print(self):
        """Restore a previously failed print."""
        if not self.octoprint_client:
            return False
        
        try:
            response = self.octoprint_client.restore(restore=True)
            return response
        except Exception as e:
            logger.error(f"Error restoring print: {e}")
            return {"status": f"Error: {e}"}
    
    def show_probing_failed(self, msg='Probing Failed, Calibrate bed again or check for hardware issue'):
        """Handle probing failure."""
        logger.info("MainController.show_probing_failed started")
        self.probing_failed.emit(msg, True)
        
        if self.octoprint_client:
            try:
                self.octoprint_client.cancelPrint()
                return True
            except Exception as e:
                logger.error(f"Error in MainController.show_probing_failed: {e}")
        return False
    
    def show_printer_error(self, msg='Printer error, Check Terminal'):
        """Handle printer errors with appropriate responses."""
        logger.info("MainController.show_printer_error started")
        if not self.octoprint_client:
            return
        
        try:
            critical_errors = [
                "Can not update MCU", "Error loading template", "Must home axis first", "probe",
                "Error during homing move", "still triggered after retract", "'mcu' must be specified"
            ]
            
            if any(error in msg for error in critical_errors):
                logger.error("CRITICAL ERROR SHUTDOWN NEEDED")
                self._handle_critical_error(msg)
            else:
                if not self.dialog_shown:
                    self.dialog_shown = True
                    self.printer_error.emit(msg, False)
                    
        except Exception as e:
            logger.error(f"Error in MainController.show_printer_error: {e}")
    
    def _handle_critical_error(self, msg):
        """Handle critical printer errors that require immediate action."""
        try:
            printer_status = getattr(self.printer_model, 'printerStatusText', None)
            if printer_status in ["Starting", "Printing", "Paused"]:
                self.octoprint_client.cancelPrint()
                self.octoprint_client.gcode(command='M112')
                try:
                    self.octoprint_client.connectPrinter(port="/tmp/printer", baudrate=115200)
                except Exception:
                    self.octoprint_client.connectPrinter(port="VIRTUAL", baudrate=115200)
                
                self.octoprint_client.gcode(command='FIRMWARE_RESTART')
                self.octoprint_client.gcode(command='RESTART')
                
                if not self.dialog_shown:
                    self.dialog_shown = True
                    self.printer_error.emit(f"{msg}, Cancelling Print.", True)
                logger.error("CRITICAL ERROR SHUTDOWN DONE")
            else:
                if not self.dialog_shown:
                    self.dialog_shown = True
                    self.octoprint_client.gcode(command='FIRMWARE_RESTART')
                    self.octoprint_client.gcode(command='RESTART')
                    self.printer_error.emit(msg, True)
        except Exception as e:
            logger.error(f"Error handling critical error: {e}")
    
    def reset_dialog_flag(self):
        """Reset the dialog shown flag."""
        self.dialog_shown = False
    
    def get_main_window(self):
        """Get the main window instance."""
        return self.main_window
    
    def get_printer_model(self):
        """Get the printer model instance."""
        return self.printer_model
    
    def get_octoprint_client(self):
        """Get the OctoPrint client instance."""
        return self.octoprint_client
    
    def get_octoprint_websocket(self):
        """Get the OctoPrint websocket instance."""
        return self.octoprint_websocket
    
    def is_minimal_ui_mode(self):
        """Check if in minimal UI mode."""
        return self.minimal_ui_mode
    
    def get_connection_controller(self):
        """Get the connection controller instance."""
        return self.connection_controller
    
    def get_connection_status(self):
        """Get current connection status information."""
        return self.connection_controller.get_connection_status()
    
    def retry_connection(self, virtual=False):
        """Retry the OctoPrint connection."""
        logger.info("Retrying connection from MainController")
        self.connection_controller.retry_connection(virtual=virtual)
    
    def cleanup(self):
        """Clean up resources when shutting down."""
        logger.info("Cleaning up MainController")
        if self.connection_controller:
            self.connection_controller.cleanup()
        
        if self.octoprint_websocket:
            self.octoprint_websocket.stop()
            
        if self.loading_screen:
            self.loading_screen.close()
            
        if self.main_window:
            self.main_window.close()
