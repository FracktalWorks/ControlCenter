import time
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from utils.logger import get_logger
from octoprint_client import octoprint_singleton
import config


logger = get_logger(__name__)


class OctoPrintConnectionThread(QThread):
    """
    Thread to check if OctoPrint is online and responding.
    This runs during startup to ensure connectivity before enabling UI features.
    """
    # Define signals for connection status
    connection_successful = pyqtSignal()
    connection_failed = pyqtSignal()

    def __init__(self, ip=None, api_key=None, virtual=False, timeout=60):
        """Initialize the connection check thread"""
        super(OctoPrintConnectionThread, self).__init__()
        self.ip = ip
        self.api_key = api_key
        self.virtual = virtual
        self.timeout = timeout
        self.shutdown_flag = False
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initialized OctoPrintConnectionThread")

    def run(self):
        """Run the sanity check to verify OctoPrint connectivity"""
        self.shutdown_flag = False
        uptime = 0
        
        self.logger.info("Running OctoPrint connectivity check")
        
        # Keep trying until OctoPrint connects or timeout
        while not self.shutdown_flag:
            try:
                # If we've been trying for more than the timeout, give up
                if uptime >= self.timeout:
                    self.shutdown_flag = True
                    self.logger.error(f"OctoPrint connection timeout after {self.timeout} seconds")
                    self.connection_failed.emit()
                    return  # Exit the thread immediately
                
                # Emit status updates periodically
                if uptime % 10 == 0 and uptime > 0:
                    self.logger.debug(f"Connection attempt ongoing... {uptime}s elapsed")
                    
                # Try to create an OctoPrint API client
                octoprint_singleton.initialize(self.ip, self.api_key)
                
                # If we're not in virtual mode, try to connect to the printer
                if not self.virtual:
                    try:
                        # First try to connect to the Klipper printer
                        octoprint_singleton.get_client().connectPrinter(port="/tmp/printer", baudrate=115200)
                        self.logger.info("Connected to Klipper printer on /tmp/printer")
                    except Exception as e:
                        # If that fails, try to connect in virtual mode
                        self.logger.warning(f"Failed to connect to Klipper printer: {e}")
                        octoprint_singleton.get_client().connectPrinter(port="VIRTUAL", baudrate=115200)
                        self.logger.info("Connected to printer in VIRTUAL mode")
                
                # If we got here, connection was successful
                if not self.shutdown_flag:
                    self.logger.info("OctoPrint connectivity check successful")
                    self.connection_successful.emit()
                return  # Exit the thread
                
            except Exception as e:
                # Wait 1 second before trying again
                time.sleep(1)
                uptime += 1
                if uptime % 5 == 0:  # Log every 5 seconds to avoid spam
                    self.logger.warning(f"OctoPrint connection attempt failed: {e}")
                    
        # If we reach here, shutdown was requested
        self.logger.info("Connection check stopped due to shutdown request")

    def stop(self):
        """Stop the connection thread gracefully"""
        self.shutdown_flag = True
        self.logger.info("Connection thread stop requested")


class ConnectionController(QObject):
    """
    Controller dedicated to managing OctoPrint connections and connection state.
    Handles connection attempts, retries, and status reporting.
    """
    
    # Signals for communication with main controller
    connection_established = pyqtSignal()
    connection_failed = pyqtSignal()
    connection_status_changed = pyqtSignal(str)  # status message
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing ConnectionController")
        
        # Connection components
        self.connection_thread = None
        self.is_connected = False
        self.connection_type = None  # 'klipper', 'virtual', or None
        
        # Connection parameters
        self.ip = config.ip
        self.api_key = config.apiKey
        self.timeout = 60
    
    def start_connection_attempt(self, virtual=False, timeout=None):
        """
        Start an OctoPrint connection attempt.
        
        Args:
            virtual (bool): Whether to force virtual mode
            timeout (int): Connection timeout in seconds (defaults to 60)
        """
        if timeout is not None:
            self.timeout = timeout
            
        logger.info(f"Starting connection attempt - Virtual: {virtual}, Timeout: {self.timeout}s")
        self.connection_status_changed.emit("Starting connection attempt...")
        
        # Stop any existing connection thread
        if self.connection_thread and self.connection_thread.isRunning():
            self.stop_connection_attempt()
        
        # Create and configure new connection thread
        self.connection_thread = OctoPrintConnectionThread(
            ip=self.ip,
            api_key=self.api_key,
            virtual=virtual,
            timeout=self.timeout
        )
        
        # Connect signals
        self.connection_thread.connection_successful.connect(self._on_connection_successful)
        self.connection_thread.connection_failed.connect(self._on_connection_failed)
        
        # Start the thread
        self.connection_thread.start()
    
    def stop_connection_attempt(self):
        """Stop any ongoing connection attempt."""
        if self.connection_thread and self.connection_thread.isRunning():
            logger.info("Stopping connection attempt")
            self.connection_thread.stop()
            self.connection_thread.wait(5000)  # Wait up to 5 seconds for thread to finish
            if self.connection_thread.isRunning():
                logger.warning("Connection thread did not stop gracefully")
                self.connection_thread.terminate()
    
    def _on_connection_successful(self):
        """Handle successful connection."""
        logger.info("Connection established successfully")
        self.is_connected = True
        
        # Determine connection type based on the connection attempt
        try:
            client = octoprint_singleton.get_client()
            # This is a simplified check - in reality you might want to query the printer status
            self.connection_type = "klipper"  # or "virtual" based on actual connection
        except Exception as e:
            logger.warning(f"Could not determine connection type: {e}")
            self.connection_type = "unknown"
        
        self.connection_status_changed.emit("Connected successfully")
        self.connection_established.emit()
    
    def _on_connection_failed(self):
        """Handle failed connection."""
        logger.info("Connection attempt failed")
        self.is_connected = False
        self.connection_type = None
        
        self.connection_status_changed.emit("Connection failed")
        self.connection_failed.emit()
    
    def retry_connection(self, virtual=False):
        """Retry the connection attempt."""
        logger.info("Retrying connection")
        self.start_connection_attempt(virtual=virtual)
    
    def get_connection_status(self):
        """
        Get current connection status.
        
        Returns:
            dict: Connection status information
        """
        return {
            'is_connected': self.is_connected,
            'connection_type': self.connection_type,
            'ip': self.ip,
            'api_key_configured': bool(self.api_key)
        }
    
    def is_connection_active(self):
        """Check if connection is currently active."""
        return self.is_connected
    
    def get_connection_type(self):
        """Get the type of current connection."""
        return self.connection_type
    
    def set_connection_parameters(self, ip=None, api_key=None, timeout=None):
        """
        Update connection parameters.
        
        Args:
            ip (str): OctoPrint IP address
            api_key (str): OctoPrint API key
            timeout (int): Connection timeout in seconds
        """
        if ip is not None:
            self.ip = ip
            logger.info(f"Connection IP updated to: {ip}")
        
        if api_key is not None:
            self.api_key = api_key
            logger.info("Connection API key updated")
        
        if timeout is not None:
            self.timeout = timeout
            logger.info(f"Connection timeout updated to: {timeout}s")
    
    def cleanup(self):
        """Clean up resources when shutting down."""
        logger.info("Cleaning up ConnectionController")
        self.stop_connection_attempt()
        self.is_connected = False
        self.connection_type = None
