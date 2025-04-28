from PyQt5 import QtCore
import time
import subprocess
from utils import logger
from octoprint_client.octoprintAPI import octoprintAPI
import websocket
import json
import requests
import random
import uuid
import threading
from utils.helpers import run_async
from utils import dialog

class ThreadSanityCheck(QtCore.QThread):
    """
    Thread to check if OctoPrint is online and responding.
    This runs during startup to ensure connectivity before enabling UI features.
    """
    # Define signals for connection status
    loaded_signal = QtCore.pyqtSignal()
    startup_error_signal = QtCore.pyqtSignal()

    def __init__(self, ip=None, api_key=None, virtual=False):
        """Initialize the sanity check thread"""
        super(ThreadSanityCheck, self).__init__()
        self.ip = ip
        self.api_key = api_key
        self.MKSPort = None
        self.virtual = virtual
        self.shutdown_flag = False
        logger.info("Initialized ThreadSanityCheck")

    def run(self):
        """Run the sanity check to verify OctoPrint connectivity"""
        global octopiclient
        from octoprint_client import octoprint_singleton
        
        self.shutdown_flag = False
        # Get the first value of uptime (runtime check)
        uptime = 0
        
        logger.info("Running OctoPrint connectivity check")
        # Keep trying until OctoPrint connects or timeout
        while True:
            try:
                # If we've been trying for more than 60 seconds, give up
                if uptime > 60:
                    self.shutdown_flag = True
                    logger.error("OctoPrint connection timeout after 60 seconds")
                    self.startup_error_signal.emit()
                    break
                    
                # Try to create an OctoPrint API client
                octoprint_singleton.initialize(self.ip, self.api_key)
                
                # If we're not in virtual mode, try to connect to the printer
                if not self.virtual:
                    try:
                        # First try to connect to the Klipper printer
                        octoprint_singleton.get_client().connectPrinter(port="/tmp/printer", baudrate=115200)
                        logger.info("Connected to Klipper printer on /tmp/printer")
                    except Exception as e:
                        # If that fails, try to connect in virtual mode
                        logger.warning(f"Failed to connect to Klipper printer: {e}")
                        octoprint_singleton.get_client().connectPrinter(port="VIRTUAL", baudrate=115200)
                        logger.info("Connected to printer in VIRTUAL mode")
                
                # If we got here, connection was successful
                break
                
            except Exception as e:
                # Wait 1 second before trying again
                time.sleep(1)
                uptime += 1
                logger.warning(f"OctoPrint connection attempt failed: {e}")
                
        # If we didn't set the shutdown flag, we were successful
        if not self.shutdown_flag:
            logger.info("OctoPrint connectivity check successful")
            self.loaded_signal.emit()

class ThreadFileUpload(QtCore.QThread):
    """Thread to handle file uploads to OctoPrint without blocking UI"""
    
    upload_complete_signal = QtCore.pyqtSignal(bool, str)
    
    def __init__(self, file, print_after_upload=False):
        """Initialize the file upload thread"""
        super(ThreadFileUpload, self).__init__()
        self.file = file
        self.print_after_upload = print_after_upload
        logger.info(f"Initialized ThreadFileUpload for {file}")

    def run(self):
        """Run the file upload process"""
        from octoprint_client import octoprint_singleton
        
        logger.info(f"Starting file upload: {self.file}")
        try:
            # Check if there's a thumbnail image to upload
            if self.file.lower().endswith('.gcode'):
                thumbnail_file = self.file.replace(".gcode", ".png")
                try:
                    import os
                    if os.path.exists(thumbnail_file):
                        logger.info(f"Uploading thumbnail: {thumbnail_file}")
                        octoprint_singleton.get_client().uploadImage(thumbnail_file)
                except Exception as e:
                    logger.error(f"Failed to upload thumbnail: {e}")
            
            # Upload the gcode file
            if self.print_after_upload:
                logger.info(f"Uploading and printing file: {self.file}")
                octoprint_singleton.get_client().uploadGcode(file=self.file, select=True, prnt=True)
            else:
                logger.info(f"Uploading file: {self.file}")
                octoprint_singleton.get_client().uploadGcode(file=self.file, select=False, prnt=False)
                
            self.upload_complete_signal.emit(True, self.file)
            logger.info("File upload completed successfully")
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            self.upload_complete_signal.emit(False, str(e))

class ThreadRestartNetworking(QtCore.QThread):
    """Thread to restart network interfaces without blocking the UI"""
    
    WLAN = "wlan0"
    ETH = "eth0"
    
    # Signal emitted with the new IP address, or None if failed
    signal = QtCore.pyqtSignal(object)

    def __init__(self, interface):
        """Initialize the network restart thread"""
        super(ThreadRestartNetworking, self).__init__()
        self.interface = interface
        logger.info(f"Initialized ThreadRestartNetworking for {interface}")
        
    def run(self):
        """Run the network restart process"""
        logger.info(f"Restarting network interface: {self.interface}")
        self.restart_interface()
        
        # Try up to 3 times to get an IP address
        attempt = 0
        while attempt < 3:
            ip = self.get_ip()
            if ip:
                logger.info(f"Network interface {self.interface} restarted with IP: {ip}")
                self.signal.emit(ip)
                break
            else:
                attempt += 1
                time.sleep(5)
                logger.warning(f"No IP address for {self.interface}, attempt {attempt}/3")
        
        # If we tried 3 times and failed, emit None
        if attempt >= 3:
            logger.error(f"Failed to get IP address for {self.interface} after 3 attempts")
            self.signal.emit(None)

    def restart_interface(self):
        """Restart the network interface"""
        try:
            if self.interface == self.WLAN:
                # For WiFi, use wpa_cli to reconfigure
                subprocess.call(["wpa_cli", "-i", self.interface, "reconfigure"], shell=False)
                logger.info("WiFi interface reconfigured")
            elif self.interface == self.ETH:
                # For Ethernet, cycle the interface
                subprocess.call(["ifconfig", self.interface, "down"], shell=False)
                time.sleep(1)
                subprocess.call(["ifconfig", self.interface, "up"], shell=False)
                logger.info("Ethernet interface cycled")
            
            # Give the interface time to come up
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"Failed to restart interface {self.interface}: {e}")
            
    def get_ip(self):
        """Get the IP address for this interface"""
        try:
            # Run ifconfig and grep for the interface and its inet addr
            cmd = f"ifconfig {self.interface} | grep 'inet '"
            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
            
            # Extract IP address using a simple split method
            # This assumes the output format is consistent (it is on Raspberry Pi)
            if 'inet ' in result:
                ip = result.split('inet ')[1].split(' ')[0]
                return ip
            return None
        except Exception as e:
            logger.error(f"Failed to get IP for {self.interface}: {e}")
            return None

class QtWebsocket(QtCore.QThread):
    """
    https://pypi.python.org/pypi/websocket-client
    https://wiki.python.org/moin/PyQt/Threading,_Signals_and_Slots
    """

    z_home_offset_signal = QtCore.pyqtSignal(str)
    temperatures_signal = QtCore.pyqtSignal(dict)
    status_signal = QtCore.pyqtSignal(str)
    print_status_signal = QtCore.pyqtSignal('PyQt_PyObject')
    update_started_signal = QtCore.pyqtSignal(dict)
    update_log_signal = QtCore.pyqtSignal(dict)
    update_log_result_signal = QtCore.pyqtSignal(dict)
    update_failed_signal = QtCore.pyqtSignal(dict)
    connected_signal = QtCore.pyqtSignal()
    filament_sensor_triggered_signal = QtCore.pyqtSignal(str)
    firmware_updater_signal = QtCore.pyqtSignal(dict)
    set_z_tool_offset_signal = QtCore.pyqtSignal(str, bool)
    tool_offset_signal = QtCore.pyqtSignal(str)
    active_extruder_signal = QtCore.pyqtSignal(str)
    z_probe_offset_signal = QtCore.pyqtSignal(str)
    z_probing_failed_signal = QtCore.pyqtSignal()
    printer_error_signal = QtCore.pyqtSignal(str)

    def __init__(self, ip, apiKey):
        logger.info("QtWebsocket started")
        super(QtWebsocket, self).__init__()
        self.ws = None
        self.heartbeat_timer = None
        self.ip = ip
        self.apiKey = apiKey
        try:
            url = "ws://{}/sockjs/{:0>3d}/{}/websocket".format(
                ip,  # host + port + prefix, but no protocol
                random.randrange(0, stop=999),  # server_id
                uuid.uuid4()  # session_id
            )

            self.ws = websocket.WebSocketApp(url,
                                             on_message=self.on_message,
                                             on_error=self.on_error,
                                             on_close=self.on_close,
                                             on_open=self.on_open)
        except Exception as e:
            logger.error("Error in QtWebsocket: {}".format(e))

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
        logger.info("QtWebsocket.reestablish_connection started")
        try:
            self.__init__(self.ip, self.apiKey)
            self.start()
        except Exception as e:
            logger.error("Error in QtWebsocket.reestablish_connection: {}".format(e))

    def send(self, data):
        logger.info("QtWebsocket.send started")
        try:
            payload = '["' + json.dumps(data).replace('"', '\\"') + '"]'
            self.ws.send(payload)
        except Exception as e:
            logger.error("Error in QtWebsocket.send: {}".format(e))
            dialog.WarningOk(self, "Error in QtWebsocket.send: {}".format(e), overlay=True)

    def authenticate(self):
        logger.info("QtWebsocket.authenticate started")
        try:
            url = 'http://' + self.ip + '/api/login'
            headers = {'content-type': 'application/json', 'X-Api-Key': self.apiKey}
            payload = {"passive": True}
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            data = response.json()

            auth_message = {"auth": "{name}:{session}".format(**data)}

            self.send(auth_message)
        except Exception as e:
            logger.error("Error in QtWebsocket.authenticate: {}".format(e))

    def on_message(self, ws, message):
        message_type = message[0]
        if message_type == "h":
            self.reset_heartbeat_timer()
            return
        elif message_type == "o":
            return
        elif message_type == "c":
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
        self.authenticate()

    def on_close(self, ws):
        pass

    def on_error(self, ws, error):
        logger.error("Error in QtWebsocket: {}".format(error))

    @run_async
    def process(self, data):
        try:
            if "event" in data:
                if data["event"]["type"] == "Connected":
                    self.connected_signal.emit()
                    print("connected")
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
                        if 'Filament Runout or clogged' in item:
                            self.filament_sensor_triggered_signal.emit(item[item.index('T') + 1:].split(' ', 1)[0])

                        if 'Primary FS Status' in item:
                            self.filament_sensor_triggered_signal.emit(item)

                        if 'M206' in item:
                            self.z_home_offset_signal.emit(item[item.index('Z') + 1:].split(' ', 1)[0])

                        if 'Count' in item:
                            self.set_z_tool_offset_signal.emit(item[item.index('z') + 2:].split(',', 1)[0],
                                      False)
                        if 'M218' in item:
                            self.tool_offset_signal.emit(item[item.index('M218'):])
                        if 'Active Extruder' in item:
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
                               break
                        else:
                           if item.startswith('!!') or item.startswith('Error'):
                               self.printer_error_signal.emit(item)
                               logger.error("Error From Klipper/Printer: {}".format(item))

                if data["current"]["state"]["text"]:
                    self.status_signal.emit(data["current"]["state"]["text"])

                fileInfo = {"job": data["current"]["job"], "progress": data["current"]["progress"]}
                if fileInfo['job']['file']['name'] is not None:
                    self.print_status_signal.emit(fileInfo)
                else:
                    self.print_status_signal.emit(None)

                def temp(data, tool, temp):
                    try:
                        if tool in data["current"]["temps"][0]:
                            return data["current"]["temps"][0][tool][temp]
                    except:
                        pass
                    return 0

                if data["current"]["temps"] and len(data["current"]["temps"]) > 0:
                    try:
                        temperatures = {'tool0Actual': temp(data, "tool0", "actual"),
                                        'tool0Target': temp(data, "tool0", "target"),
                                        'tool1Actual': temp(data, "tool1", "actual"),
                                        'tool1Target': temp(data, "tool1", "target"),
                                        'bedActual': temp(data, "bed", "actual"),
                                        'bedTarget': temp(data, "bed", "target")}
                        self.temperatures_signal.emit(temperatures)
                    except KeyError:
                        pass
        except Exception as e:
            logger.error("Error in QtWebsocket.process: {}".format(e))