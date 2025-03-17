import requests
import logging
from threading import Lock

class MoonrakerAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.api_mutex = Lock()
        
        # Configure the logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Create a file handler
        file_handler = logging.FileHandler('moonraker.log')
        file_handler.setLevel(logging.INFO)
        
        # Create a formatter and set it for the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Remove all existing handlers
        self.logger.handlers.clear()
        
        # Add the file handler to the logger
        self.logger.addHandler(file_handler)

    def reconnect(self):
        """
        Attempt to reconnect to the Moonraker server.
        """
        try:
            # No specific action needed for reconnecting in this context
            self.logger.info("Reconnected to Moonraker server.")
        except Exception as e:
            self.logger.error(f"Failed to reconnect: {e}")

    def send_gcode(self, cmd):
        self.logger.info(f"Sending G-code command: {cmd}")
        try:
            self.api_mutex.acquire()
            response = requests.post(
                url=f"{self.base_url}/printer/gcode/script",
                json={"script": cmd},
                timeout=10
            )
            response.raise_for_status()
            response_data = response.json()
            self.logger.info(f"Response from Moonraker: {response_data}")
            return response_data
        except requests.exceptions.Timeout:
            self.logger.error("Request to Moonraker timed out.")
            self.reconnect()
            return "Timeout"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending G-code: {e}")
            self.reconnect()
            return str(e)
        finally:
            self.api_mutex.release()

    def query_status(self):
        self.logger.info("Querying printer status.")
        try:
            self.api_mutex.acquire()
            response = requests.get(
                url=f"{self.base_url}/printer/objects/query?status",
                timeout=10
            )
            response.raise_for_status()
            response_data = response.json()
            self.logger.info(f"Response from Moonraker: {response_data}")
            return response_data
        except requests.exceptions.Timeout:
            self.logger.error("Request to Moonraker timed out.")
            self.reconnect()
            return "Timeout"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error querying status: {e}")
            self.reconnect()
            return str(e)
        finally:
            self.api_mutex.release()

    def query_temperatures(self):
        self.logger.info("Querying printer temperatures.")
        try:
            self.api_mutex.acquire()
            response = requests.get(
                url=f"{self.base_url}/printer/objects/query?temperature",
                timeout=10
            )
            response.raise_for_status()
            response_data = response.json()
            self.logger.info(f"Response from Moonraker: {response_data}")
            return response_data
        except requests.exceptions.Timeout:
            self.logger.error("Request to Moonraker timed out.")
            self.reconnect()
            return "Timeout"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error querying temperatures: {e}")
            self.reconnect()
            return str(e)
        finally:
            self.api_mutex.release()

