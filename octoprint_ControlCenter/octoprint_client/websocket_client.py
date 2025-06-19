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

from utils.logger import setup_logger
from utils.helpers import run_async

logger = setup_logger("printer")

class OctoPrintWebSocket(QThread):
    """
    WebSocket client for OctoPrint that runs in its own thread
    and emits signals when events occur
    """
    # Define signals for UI updates
    # z_home_offset_signal = pyqtSignal(str) ... deprecated, uses probe_offset
    temperatures_signal = pyqtSignal(dict) #! done
    status_signal = pyqtSignal(str) #! done
    print_status_signal = pyqtSignal('PyQt_PyObject') #! done
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
        self.ip = ip
        self.api_key = api_key
        self.ws = None
        self.heartbeat_timer = None

        try:
            url = f"ws://{self.ip}/sockjs/{random.randrange(0, stop=999):0>3d}/{uuid.uuid4()}/websocket"
            self.ws = websocket.WebSocketApp(
                url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
        except Exception as e:
            logger.error(f"Error initializing WebSocket: {e}")

    def run(self):
        logger.info("QtWebsocket.run started")
        try:
            self.ws.run_forever()
            self.reset_heartbeat_timer()
        except Exception as e:
            logger.error("Error in QtWebsocket.run: {}".format(e))

    def reset_heartbeat_timer(self):
        try:
            if self.heartbeat_timer is not None:
                self.heartbeat_timer.cancel()

            self.heartbeat_timer = threading.Timer(120, self.reestablish_connection)  # 120 seconds = 2 minutes
            self.heartbeat_timer.start()
        except Exception as e:
            logger.error("Error in QtWebsocket.reset_heartbeat_timer: {}".format(e))

    def reestablish_connection(self):
        logger.info("Reestablishing WebSocket connection...")
        try:
            self.reconnect_attempts += 1
            if self.reconnect_attempts > self.max_reconnect_attempts:
                logger.error("Max reconnect attempts reached. Giving up.")
                return

            self._initialize_websocket()
            self.start()
            logger.info("Reconnection attempt {} succeeded.".format(self.reconnect_attempts))
        except Exception as e:
            logger.error("Error in QtWebsocket.reestablish_connection: {}".format(e))

    def send(self, data):
        """
        Send data to the WebSocket
        :param data: Data to send
        """
        logger.info("Sending data via WebSocket")
        try:
            payload = '["' + json.dumps(data).replace('"', '\\"') + '"]'
            self.ws.send(payload)
        except Exception as e:
            logger.error(f"Error sending data via WebSocket: {e}")

    def authenticate(self):
        """
        Authenticate with the OctoPrint server
        """
        logger.info("Authenticating WebSocket connection")
        try:
            # perform passive login to retrieve username and session key for API key
            url = f'http://{self.ip}/api/login'
            headers = {'content-type': 'application/json', 'X-Api-Key': self.api_key}
            payload = {"passive": True}
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            data = response.json()

            # prepare auth payload
            auth_message = {"auth": f"{data['name']}:{data['session']}"}

            # send it
            self.send(auth_message)
        except Exception as e:
            logger.error(f"Error authenticating WebSocket: {e}")

    def on_message(self, ws, message):
        """
        Handle messages from the WebSocket
        :param ws: WebSocket instance
        :param message: Message from the WebSocket
        """
        message_type = message[0]
        if message_type == "h":
            # "heartbeat" message
            self.reset_heartbeat_timer()
            return
        elif message_type == "o":
            # "open" message
            return
        elif message_type == "c":
            # "close" message
            return

        message_body = message[1:]
        if not message_body:
            return
        data = json.loads(message_body)[0]

        if message_type == "m":
            data = [data, ]

        if message_type == "a":
            self.process(data)

    def on_open(self, ws):
        """
        Handle WebSocket connection open
        :param ws: WebSocket instance
        """
        self.authenticate()

    def on_close(self, ws, *args, **kwargs):
        logger.warning("WebSocket connection closed. Attempting to reconnect...")
        self.reestablish_connection()

    def on_error(self, ws, error):
        logger.error("Error in WebSocket connection: {}".format(error))
        self.reestablish_connection()

    @run_async
    def process(self, data):
        """
        Process data from the WebSocket
        :param data: Data from the WebSocket
        """
        try:
            if "event" in data:
                if data["event"]["type"] == "Connected":
                    self.connected_signal.emit()
                    logger.info("Connected to OctoPrint server")
            
            if "plugin" in data:
                if data["plugin"]["plugin"] == 'JuliaFirmwareUpdater':
                    self.firmware_updater_signal.emit(data["plugin"]["data"])

                elif data["plugin"]["plugin"] == 'softwareupdate':
                    if data["plugin"]["data"]["type"] == "updating":
                        self.update_started_signal.emit(data["plugin"]["data"]["data"])
                    elif data["plugin"]["data"]["type"] == "loglines":
                        self.update_log_signal.emit(data["plugin"]["data"]["data"]["loglines"])
                    elif data["plugin"]["data"]["type"] == "restarting":
                        self.update_log_result_signal.emit(data["plugin"]["data"]["data"]["results"])
                    elif data["plugin"]["data"]["type"] == "update_failed":
                        self.update_failed_signal.emit(data["plugin"]["data"]["data"])

            if "current" in data:
                if data["current"]["messages"]:
                    for item in data["current"]["messages"]:
                        if 'Filament Runout or clogged' in item:  # "Filament Runout on T0/T1"
                            self.filament_sensor_triggered_signal.emit(item[item.index('T') + 1:].split(' ', 1)[0])

                        if 'Primary FS Status' in item:
                            self.filament_sensor_triggered_signal.emit(item)

                        # if 'M206' in item:  # response to M503, send current Z offset value
                        #     self.z_home_offset_signal.emit(item[item.index('Z') + 1:].split(' ', 1)[0])
                            
                        if 'Count' in item:  # can get through the positionUpdate event
                            self.set_z_tool_offset_signal.emit(item[item.index('z') + 2:].split(',', 1)[0], False)
                            
                        if 'M218' in item:
                            self.tool_offset_signal.emit(item[item.index('M218'):])
                            
                        if 'Active Extruder' in item:  # can get through the positionUpdate event
                            self.active_extruder_signal.emit(item[-1])

                        if 'M851' in item:
                            self.z_probe_offset_signal.emit(item[item.index('Z') + 1:].split(' ', 1)[0])
                            
                        if 'PROBING_FAILED' in item:
                            self.z_probing_failed_signal.emit()

                        for ignore_item in [
                            "!! Printer is not ready",
                            "!! Move out of range:",
                            "!! Shutdown due to M112"
                        ]:
                            if ignore_item in item:
                                # Ignore this item
                                break
                        else:
                            if item.startswith('!!') or item.startswith('Error'):
                                self.printer_error_signal.emit(item)
                                logger.error(f"Error From Klipper/Printer: {item}")

                if data["current"]["state"]["text"]:
                    self.status_signal.emit(data["current"]["state"]["text"])

                file_info = {"job": data["current"]["job"], "progress": data["current"]["progress"]}
                if file_info['job']['file']['name'] is not None:
                    self.print_status_signal.emit(file_info)
                else:
                    self.print_status_signal.emit({"job": None, "progress": None})

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
                        self.temperatures_signal.emit(temperatures)
                    except KeyError:
                        pass
        except Exception as e:
            logger.error(f"Error processing WebSocket data: {e}")