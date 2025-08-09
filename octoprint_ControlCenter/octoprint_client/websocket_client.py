"""
WebSocket Client for OctoPrint

This module handles real-time communication with OctoPrint via WebSockets
"""
import json
import random
import threading
import time
import uuid
import websocket
import requests
from PyQt5.QtCore import QThread, pyqtSignal

from utils.logger import get_logger
from utils.helpers import run_async
from config import IGNORED_PRINTER_ERRORS


class OctoPrintWebSocket(QThread):
    """
    WebSocket client for OctoPrint that connects to the WebSocket API
    and emits signals when events occur
    """
    # Define signals for UI updates
    # z_home_offset_signal = pyqtSignal(str) ... deprecated, uses probe_offset
    temperatures_signal = pyqtSignal(dict) #! done
    status_signal = pyqtSignal(str) #! done
    print_status_signal = pyqtSignal('PyQt_PyObject') #! done
    # Use class-level logger for all logging
    update_started_signal = pyqtSignal(dict) #! done
    update_log_signal = pyqtSignal(dict) #! done
    update_log_result_signal = pyqtSignal(dict) #! done
    update_failed_signal = pyqtSignal(dict) #! done
    connected_signal = pyqtSignal() #! done
    filament_sensor_triggered_signal = pyqtSignal(str) #! done
    # firmware_updater_signal = pyqtSignal(dict) ... likely not to be used, but can be added later
    set_z_tool_offset_signal = pyqtSignal(str, bool) #! done
    tool_offset_signal = pyqtSignal(str) # done
    active_extruder_signal = pyqtSignal(str) # done
    z_probe_offset_signal = pyqtSignal(str) # done
    z_probing_failed_signal = pyqtSignal() # done
    printer_error_signal = pyqtSignal(str) # done

    def __init__(self, ip="0.0.0.0:5000", api_key=None):
        """
        Initialize the WebSocket client
        :param ip: IP address of the OctoPrint server
        :param api_key: API key for OctoPrint
        """
        super(OctoPrintWebSocket, self).__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.ip = ip
        self.api_key = api_key
        self.ws = None
        self.heartbeat_timer = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

        self.logger.info(f"OctoPrintWebSocket initializing with IP: {self.ip}, API Key: {'***' + self.api_key[-4:] if self.api_key else 'None'}")
        self._initialize_websocket()

    def _initialize_websocket(self):
        """Initialize or reinitialize the WebSocket connection"""
        try:
            url = f"ws://{self.ip}/sockjs/{random.randrange(0, stop=999):0>3d}/{uuid.uuid4()}/websocket"
            self.logger.info(f"Creating WebSocket connection to: {url}")
            self.ws = websocket.WebSocketApp(
                url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            self.logger.info("WebSocket app created successfully")
        except Exception as e:
            self.logger.error(f"Error initializing WebSocket: {e}")
            raise

    def run(self):
        self.logger.info("WebSocket thread starting...")
        try:
            self.logger.info("Starting WebSocket run_forever() loop")
            self.ws.run_forever()
            self.reset_heartbeat_timer()
            self.logger.info("WebSocket run_forever() completed")
        except Exception as e:
            self.logger.error("Error in QtWebsocket.run: {}".format(e))

    def reset_heartbeat_timer(self):
        try:
            if self.heartbeat_timer is not None:
                self.heartbeat_timer.cancel()
                self.logger.debug("Previous heartbeat timer cancelled")

            self.heartbeat_timer = threading.Timer(120, self.reestablish_connection)  # 120 seconds = 2 minutes
            self.heartbeat_timer.start()
            self.logger.debug("Heartbeat timer reset - 120 seconds")
        except Exception as e:
            self.logger.error("Error in QtWebsocket.reset_heartbeat_timer: {}".format(e))

    def reestablish_connection(self):
        self.logger.info("Reestablishing WebSocket connection...")
        try:
            self.reconnect_attempts += 1
            self.logger.info(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")
            
            if self.reconnect_attempts > self.max_reconnect_attempts:
                self.logger.error("Max reconnect attempts reached. Giving up.")
                return

            self.logger.info("Reinitializing WebSocket...")
            self._initialize_websocket()
            self.logger.info("Starting new WebSocket thread...")
            self.start()
            self.logger.info("Reconnection attempt {} succeeded.".format(self.reconnect_attempts))
        except Exception as e:
            self.logger.error("Error in QtWebsocket.reestablish_connection: {}".format(e))

    def send(self, data):
        """
        Send data to the WebSocket
        :param data: Data to send
        """
        self.logger.info(f"Sending data via WebSocket: {data}")
        try:
            payload = '["' + json.dumps(data).replace('"', '\\"') + '"]'
            self.logger.debug(f"WebSocket payload: {payload}")
            self.ws.send(payload)
            self.logger.debug("Data sent successfully")
        except Exception as e:
            self.logger.error(f"Error sending data via WebSocket: {e}")

    def authenticate(self):
        """
        Authenticate with the OctoPrint server
        """
        self.logger.info("Authenticating WebSocket connection")
        try:
            # perform passive login to retrieve username and session key for API key
            url = f'http://{self.ip}/api/login'
            self.logger.info(f"Attempting passive login to: {url}")
            headers = {'content-type': 'application/json', 'X-Api-Key': self.api_key}
            payload = {"passive": True}
            
            self.logger.debug("Sending authentication request...")
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            self.logger.info(f"Authentication response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Authentication successful for user: {data.get('name', 'unknown')}")
                
                # prepare auth payload
                auth_message = {"auth": f"{data['name']}:{data['session']}"}
                self.logger.debug("Sending WebSocket auth message...")
                
                # send it
                self.send(auth_message)
            else:
                self.logger.error(f"Authentication failed with status {response.status_code}: {response.text}")
        except Exception as e:
            self.logger.error(f"Error authenticating WebSocket: {e}")
            raise

    def on_message(self, ws, message):
        """
        Handle messages from the WebSocket
        :param ws: WebSocket instance
        :param message: Message from the WebSocket
        """
        self.logger.debug(f"WebSocket message received: {message[:100]}{'...' if len(message) > 100 else ''}")
        
        message_type = message[0]
        if message_type == "h":
            # "heartbeat" message
            self.logger.debug("Received heartbeat message")
            self.reset_heartbeat_timer()
            return
        elif message_type == "o":
            # "open" message
            self.logger.info("WebSocket connection opened")
            return
        elif message_type == "c":
            # "close" message
            self.logger.warning("Received close message from WebSocket")
            return

        message_body = message[1:]
        if not message_body:
            self.logger.debug("Empty message body received")
            return
            
        try:
            data = json.loads(message_body)[0]
            self.logger.debug(f"Parsed message data keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
        except (json.JSONDecodeError, IndexError) as e:
            self.logger.error(f"Failed to parse message body: {e}")
            return

        if message_type == "m":
            data = [data, ]

        if message_type == "a":
            self.logger.debug("Processing message data...")
            self.process(data)

    def on_open(self, ws):
        """
        Handle WebSocket connection open
        :param ws: WebSocket instance
        """
        self.logger.info("WebSocket connection opened successfully")
        self.reconnect_attempts = 0  # Reset reconnect counter on successful connection
        self.logger.info("Starting authentication process...")
        self.authenticate()

    def on_close(self, ws, *args, **kwargs):
        self.logger.warning(f"WebSocket connection closed. Args: {args}, Kwargs: {kwargs}")
        self.logger.info("Attempting to reconnect...")
        self.reestablish_connection()

    def on_error(self, ws, error):
        self.logger.error("Error in WebSocket connection: {}".format(error))
        self.logger.info("Error occurred, attempting to reconnect...")
        self.reestablish_connection()

    @run_async
    def process(self, data):
        """
        Process data from the WebSocket
        :param data: Data from the WebSocket
        """
        try:
            self.logger.debug("Processing WebSocket data...")
            
            if "event" in data:
                self.logger.info(f"Event received: {data['event'].get('type', 'unknown')}")
                if data["event"]["type"] == "Connected":
                    self.logger.info("Emitting connected_signal")
                    self.connected_signal.emit()
                    self.logger.info("Connected to OctoPrint server")
            
            if "plugin" in data:
                plugin_name = data["plugin"]["plugin"]
                self.logger.info(f"Plugin message received from: {plugin_name}")

                if plugin_name == 'klipper':
                    # Extract the actual error message from the plugin data
                    plugin_data = data["plugin"]["data"]
                    if isinstance(plugin_data, dict) and plugin_data.get('subtype') == 'error':
                        error_message = plugin_data.get('payload', plugin_data.get('title', str(plugin_data)))
                        self.logger.error(f"Klipper error detected: {error_message}")
                        self.printer_error_signal.emit(str(error_message).strip()) 

                if plugin_name == 'JuliaFirmwareUpdater':
                    self.logger.info("Emitting firmware_updater_signal")
                    # Note: firmware_updater_signal not defined in this class
                    # self.firmware_updater_signal.emit(data["plugin"]["data"])

                elif plugin_name == 'softwareupdate':
                    update_type = data["plugin"]["data"]["type"]
                    self.logger.info(f"Software update message type: {update_type}")
                    
                    if update_type == "updating":
                        self.logger.info("Emitting update_started_signal")
                        self.update_started_signal.emit(data["plugin"]["data"]["data"])
                    elif update_type == "loglines":
                        self.logger.debug("Emitting update_log_signal")
                        self.update_log_signal.emit(data["plugin"]["data"]["data"]["loglines"])
                    elif update_type == "restarting":
                        self.logger.info("Emitting update_log_result_signal")
                        self.update_log_result_signal.emit(data["plugin"]["data"]["data"]["results"])
                    elif update_type == "update_failed":
                        self.logger.warning("Emitting update_failed_signal")
                        self.update_failed_signal.emit(data["plugin"]["data"]["data"])

            if "current" in data:
                self.logger.debug("Processing current state data...")
                
                # Process messages
                if data["current"]["messages"]:
                    self.logger.debug(f"Processing {len(data['current']['messages'])} messages")
                    for item in data["current"]["messages"]:
                        self.logger.debug(f"Processing message: {item}")
                        
                        if 'Filament Runout or clogged' in item:  # "Filament Runout on T0/T1"
                            tool = item[item.index('T') + 1:].split(' ', 1)[0]
                            self.logger.info(f"Filament sensor triggered for tool {tool}")
                            self.filament_sensor_triggered_signal.emit(tool)

                        if 'Primary FS Status' in item:
                            self.logger.info(f"Primary filament sensor status: {item}")
                            self.filament_sensor_triggered_signal.emit(item)
                            
                        if 'Count' in item:  # can get through the positionUpdate event
                            z_offset = item[item.index('z') + 2:].split(',', 1)[0]
                            self.logger.debug(f"Z tool offset update: {z_offset}")
                            self.set_z_tool_offset_signal.emit(z_offset, False)
                            
                        if 'M218' in item:
                            tool_offset_data = item[item.index('M218'):]
                            self.logger.info(f"Tool offset data: {tool_offset_data}")
                            self.tool_offset_signal.emit(tool_offset_data)
                            
                        if 'Active Extruder' in item:  # can get through the positionUpdate event
                            extruder = item[-1]
                            self.logger.info(f"Active extruder changed to: {extruder}")
                            self.active_extruder_signal.emit(extruder)

                        if 'M851' in item:
                            probe_offset = item[item.index('Z') + 1:].split(' ', 1)[0]
                            self.logger.info(f"Z probe offset: {probe_offset}")
                            self.z_probe_offset_signal.emit(probe_offset)
                            
                        if 'PROBING_FAILED' in item:
                            self.logger.warning("Z probing failed!")
                            self.z_probing_failed_signal.emit()

                        # Check for errors - emit all errors, let showPrinterError decide what to show
                        if item.startswith('!!') or item.startswith('Error'):
                            self.logger.error(f"Printer error detected: {item}")
                            self.printer_error_signal.emit(item)

                # Process printer status
                if data["current"]["state"]["text"]:
                    status = data["current"]["state"]["text"]
                    self.logger.debug(f"Printer status update: {status}")
                    self.status_signal.emit(status)

                # Process file/job information
                file_info = {"job": data["current"]["job"], "progress": data["current"]["progress"]}
                if file_info['job'] and file_info['job']['file']['name'] is not None:
                    filename = file_info['job']['file']['name']
                    progress = file_info.get('progress', {}).get('completion', 0)
                    self.logger.info(f"Print status update - File: {filename}, Progress: {progress}%")
                    self.print_status_signal.emit(file_info)
                else:
                    self.logger.debug("Emitting empty print status")
                    self.print_status_signal.emit({"job": None, "progress": None})

                # Process temperature data
                def temp(data, tool, temp):
                    try:
                        if tool in data["current"]["temps"][0]:
                            return data["current"]["temps"][0][tool][temp]
                    except:
                        pass
                    return 0

                if data["current"]["temps"] and len(data["current"]["temps"]) > 0:
                    try:
                        temperatures = {
                            'tool0Actual': temp(data, "tool0", "actual"),
                            'tool0Target': temp(data, "tool0", "target"),
                            'tool1Actual': temp(data, "tool1", "actual"),
                            'tool1Target': temp(data, "tool1", "target"),
                            'bedActual': temp(data, "bed", "actual"),
                            'bedTarget': temp(data, "bed", "target")
                        }
                        self.logger.debug(f"Temperature update: Tool0: {temperatures['tool0Actual']}°C/{temperatures['tool0Target']}°C, "
                                        f"Tool1: {temperatures['tool1Actual']}°C/{temperatures['tool1Target']}°C, "
                                        f"Bed: {temperatures['bedActual']}°C/{temperatures['bedTarget']}°C")
                        self.temperatures_signal.emit(temperatures)
                    except KeyError as e:
                        self.logger.warning(f"Error parsing temperature data: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error processing WebSocket data: {e}")
            self.logger.exception("Full traceback:")