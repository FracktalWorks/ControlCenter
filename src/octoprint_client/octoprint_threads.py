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
