"""
This code contains functions to send API requests to the Feeltek scancard and accept its response. It logs the whole 
transaction using a custom logger imported from LaserErrorLogging.py. It also prints to GUI console in parent file. 

Socket communication over TCP is used to communicate with the scancard
"""

import socket
import json
import time
import os


# importing the custom logger created from its module
from laserErrorLogging import LaserErrorLogger

class Scancard:
    """
    A class representing a Scancard.
    Attributes:
        parent: The parent object.
        input_file_path: The path to the .emd file created.
        input_file: The name of the .emd file created.
        input_cli: The input CLI.
        HOST: The host address.
        PORT: The port number.
        timeout: The timeout value.
        file: The file.
        req: The request.
        function: The function name.
        file_path: The file path.
        formatted_response: The formatted response.
        layer_id: The layer ID.
        laser_logger: An instance of the LaserErrorLogger class.
        consoleWidget: The console widget.
    Methods:
        __init__(self, parent=None): Initializes the Scancard object.
        api(self): Sends an API request to localhost:50000 and prints out the response.
        get_working_status(self): Gets the working status of the Scancard.
        set_markparameters_by_index(self): Updates mark parameters by index.
        set_markparameters_by_layer(self): Updates mark parameters by layer.
        get_markparameters_by_index(self): Gets a list of mark parameter values by index.
        get_markparameters_by_layer(self): Gets a list of mark parameter values by layer.
        get_log(self): Gets the log.
        open_file(self): Opens an .emd file on the Scancard.
        close_file(self): Closes a file on the Scancard.
        start_mark(self): Starts marking.
        stop_mark(self): Stops marking.
    """

    def __init__(self, parent=None):
        try:
            # define the parameters to be given as part of the API request
            self.parent = parent
            self.input_file_path = "" # path to .emd file created
            self.input_file = ""      # name of .emd file created
            self.input_cli = ""
            self.HOST = "localhost" 
            self.PORT = 50000
            self.timeout = self.parent.timeout
            self.file = ""
            self.ret_value = 1

            self.req = {}
            self.function = ""
            self. file_path = ""
            self.formatted_response = {}
            self.layer_id = 0 

            # creating an instance of the custom logger
            self.laser_logger = LaserErrorLogger()
            self.consoleWidget = self.parent.consoleWidget

        except Exception as e:
            print(f"E1: Variable initialisation failed. {e}")

    # code for sending api request to localhost:50000 and printing out the response
    def api(self):

        try:
            self.request = self.req
            json_string = json.dumps(self.request)
    
            # create a socket instance
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Logging part
            self.laser_logger.logger.info(f"{self.function}-> Connecting to {self.HOST}:{self.PORT}...")
            self.parent.print_to_console({"info":f"{self.function}-> Connecting to {self.HOST}:{self.PORT}..."})

            # establish socket connection
            sock.connect((self.HOST, self.PORT))

            # Logging part
            self.laser_logger.logger.info(f"{self.function}-> Sending {self.request} to {self.HOST}:{self.PORT} with timeout of {self.timeout}s")
            self.parent.print_to_console({"info":f"{self.function}-> Sending {self.request} to {self.HOST}:{self.PORT} with timeout of {self.timeout}s"})
            
            try:
                # send request
                sock.sendall(json_string.encode())
                sock.settimeout(self.timeout)
        
                try:
                    # try to receive the response
                    ret = sock.recv(1024) 

                    ## cross check this part
                # in case of request timeout
                except socket.timeout:
                    # log the error and set ret message to None
                    self.laser_logger.logger.error(f"E203 - {self.function} not successful - Request {self.request} TIMED OUT!!")
                    self.parent.print_to_console({"error":f"E203 - {self.function} not successful - Request {self.request} TIMED OUT!!"})
                    ret = None  
                    

                 # in the case that a valid response is received from server   
                if ret:
                    try:    
                        # Decode the bytes to a string, replacing problematic characters
                        ret_decoded = ret.decode('GB18030', errors='replace')
        
                        # Find the end of the first valid JSON object
                        json_end_index = ret_decoded.rfind('}') + 1
                        json_content = ret_decoded[:json_end_index]
        
                        # Parse the JSON response
                        response_data = json.loads(json_content)
        
                        # Format the JSON response
                        formatted_json = json.dumps(response_data, indent=4, ensure_ascii=False)

                        # Extract the "ret" value
                        self.ret_value = response_data.get("ret")
        
                        # Print the extracted "ret" value
                        self.parent.print_to_console({"info":f"Extracted 'ret' value:{self.ret_value}"})

                     

                        # log the server response
                        self.laser_logger.logger.info(f"{self.function}-> Response received from {self.HOST}:{self.PORT} - {formatted_json}")
                        self.parent.print_to_console({"info":f"{self.function}-> Response received from {self.HOST}:{self.PORT} - {formatted_json}"})

                        # close the socket
                        sock.close()

                    except Exception as e:
                        # in the case that respomse received is invalid- log the error
                        self.laser_logger.logger.error(f"E202 - {self.function} not successful \n {e}")
                        self.parent.print_to_console({"error":f"E202 - {self.function} not successful \n {e}"})

            except Exception as e:
                #in the case that there was an error while sending the request to server - log the error
                self.laser_logger.logger.error(f"E201 - {self.function} not successful \n {e}")
                self.parent.print_to_console({"error":f"E201 - {self.function} not successful \n {e}"})
        
        except Exception as e:
         # in the case that there was error while creation and connecting the socket to server port - log the error
            self.laser_logger.logger.error(f"E200 - {self.function} not successful \n {e}")
            self.parent.print_to_console({"error":f"E200 - {self.function} not successful \n {e}"})
        

    # function to get working status of scancard    
    def get_working_status(self):
        self.req = {
                 "sid": 0,
                 "cmd": "get_working_status",
             }
        self.function = "getting working status"
        self.api()

    # function to update markparameters by index
    def set_markparameters_by_index(self): 

        # take the updated values of the parameters from parent file   
        self.index = self.parent.index
        self.in_index = self.parent.in_index
        self.markSpeed = self.parent.markSpeed
        self.jumpSpeed = self.parent.jumpSpeed
        self.jumpDelay = self.parent.jumpDelay
        self.laserOnDelay =self.parent.laserOnDelay
        self.PolygonDelay = self.parent.polygonDelay
        self.laserOffDelay = self.parent.laserOffDelay
        self.polygonKillerTime = self.parent.polygonKillerTime
        self.laserFreq = self.parent.laserfreq
        self.current = self.parent.current
        self.firstPulseKillerLength = self.parent.firstPulseKillerLength
        self.pulseWidth = self.parent.pulseWidth
        self.firstPulseWidth = self.parent.firstPulseWidth
        self.incrementStep = self.parent.incrementStep

        # construct the request to be sent to server
        self.req = {
               "sid": 0,
               "cmd": "set_markparameters_by_index",
               "data": {
                   "index": self.index,
                   "in_index": self.in_index,
                   "markSpeed": self.markSpeed,
                   "jumpSpeed": self.jumpSpeed,
                   "jumpDelay": self.jumpDelay,
                   "laserOnDelay": self.laserOnDelay,
                   "polygonDelay": self.PolygonDelay,
                   "laserOffDelay": self.laserOffDelay,
                   "polygonKillerTime": self.polygonKillerTime,
                   "laserFrequency": self.laserFreq,
                   "current": self.current,
                   "firstPulseKillerLength": self.firstPulseKillerLength,
                   "pulseWidth": self.pulseWidth,
                   "firstPulseWidth": self.firstPulseWidth,
                   "incrementStep": self.incrementStep
                   }
               }
        self.function = "setting mark parameters by index"
        self.api()


    # function to update mark parameters by layer
    def set_markparameters_by_layer(self):

        # take the updated values of the parameters from parent file
        self.layer_id = self.layer_id
        self.markSpeed = self.parent.markSpeed
        self.jumpSpeed = self.parent.jumpSpeed
        self.jumpDelay = self.parent.jumpDelay
        self.laserOnDelay =self.parent.laserOnDelay
        self.PolygonDelay = self.parent.polygonDelay
        self.laserOffDelay = self.parent.laserOffDelay
        self.polygonKillerTime = self.parent.polygonKillerTime
        self.laserFreq = self.parent.laserfreq
        self.current = self.parent.current
        self.firstPulseKillerLength = self.parent.firstPulseKillerLength
        self.pulseWidth = self.parent.pulseWidth
        self.firstPulseWidth = self.parent.firstPulseWidth
        self.incrementStep = self.parent.incrementStep

        # construct the request to be sent to server
        self.req = {
               "sid": 0,
               "cmd": "set_markparameters_by_layer",
               "data": {
                   "layer": self.layer_id,
                   "markSpeed": self.markSpeed,
                   "jumpSpeed": self.jumpSpeed,
                   "jumpDelay": self.jumpDelay,
                   "laserOnDelay": self.laserOnDelay,
                   "polygonDelay": self.PolygonDelay,
                   "laserOffDelay": self.laserOffDelay,
                   "polygonKillerTime": self.polygonKillerTime,
                   "laserFrequency": self.laserFreq,
                   "current": self.current,
                   "firstPulseKillerLength": self.firstPulseKillerLength,
                   "pulseWidth": self.pulseWidth,
                   "firstPulseWidth": self.firstPulseWidth,
                   "incrementStep": self.incrementStep
                   }
               }
        self.function = "setting mark parameters by layer"
        self.api()

    # function to get list of mark parameter values by index
    def get_markparameters_by_index(self):   
        self.req = {
                 "sid": 0,
                 "cmd": "get_markparameters_by_index",
                 "data": {
                     "index":0,
                     "in_index": -1
                 }
             }
        self.function = "getting mark parameters by index"
        self.api()

    # function to get list of markparameters values by layer
    def get_markparameters_by_layer(self):   
        self.req = {
                 "sid": 0,
                 "cmd": "get_markparameters_by_layer",
                 "data": {
                     "layer_id":0
                 }
             }
        self.function = "getting mark parameters by layer"
        self.api()

    # NOT USED - IGNORE
    def get_log(self):
        self.laser_logger.flush_logs()


    # function to open an .emd file on scancard   
    def open_file(self, file):
        self.req = {
            "sid":0,
            "cmd":"open_file",
            "data": {
                "path": file
            }
        }
        self.function = "Opening file"
        self.api()
        self.laser_logger.logger.info(f"File {file} opened...")
        self.parent.print_to_console({"info": f"File {file} opened..."})
        

    # function to close a file on scancard
    def close_file(self):
        self.req = {
            "sid":0,
            "cmd":"close_file"
        }
        self.function = "Closing file"
        self.api()

    # function to start marking
    def start_mark(self):
        self.req = {
            "sid":0,
            "cmd":"start_mark"
        }
        self.function = "Start marking"
        self.api()
        
    # function to stop marking    
    def stop_mark(self):
        self.req = {
            "sid":0,
            "cmd":"stop_mark"
        }
        self.function = "Stop marking"
        self.api()

    # function to download parameters onto scancard - needs to be done after each time the parameters aare updated
    def download_parameters(self):
        self.req = {
            "sid":0,
            "cmd":"download_parameters"
        }
        self.function = "Downloading Parameters"
        self.api()


    # automation loop for printing one layer - INCOMPLETE
    def one_layer_automation(self):

        # take layer number to be printed
        self.layer_number = ""
        self.laser_logger.logger.info(f"Scancard process started for layer {self.layer_number}")
        self.parent.print_to_console({"info":f"Scancard process started for layer {self.layer_number}"})

        # open file
        if self.parent.layer_count == 1:
            self.open_file(self.file)

        else:
            filename = self.file[:-4] + str(self.parent.layer_count) + ".emd"
            self.parent.print_to_console({"info":f"Opening file {filename}"})
            self.open_file(filename)
        # time.sleep(1)

        # update mark parameters
        self.set_markparameters_by_layer()
        time.sleep(1)

        # download parameters onto scancard
        self.download_parameters()
        time.sleep(1)

        # start marking
        self.start_mark()
        time.sleep(1)

        # define a flag to track marking process
        self.marking = True

        # log the progress
        self.laser_logger.logger.info(f"Marking process for Layer {self.layer_number} started...")
        self.parent.print_to_console({"info":f"Marking process for Layer {self.layer_number} started..."})
        
        self.ret_value = 1
        # while it is marking
        while (self.ret_value!=0):
            time.sleep(1)

            # check the status of scancard - if 0 it means that scancard is waiting for next command
            self.get_working_status()
            status = self.ret_value
            print(f"status={status}")
           

        # log the completion of marking process
        self.laser_logger.logger.info(f"Marking process for Layer {self.layer_number} over")
        self.parent.print_to_console({"info":f"Marking process for Layer {self.layer_number} over"})
        
        self.stop_mark()

    def update_layer_id(self):
        # logic to update layer id
        self.layer_id = 1

    def check_scancard_connection(self):
        pass

    # function to save file from parent as a global variable inside this file; also checks the file extension of input file 
    def get_file(self, file):
        try:
            self.file = file
            if ".emd" not in self.file:
                raise e
        except Exception as e:
            self.laser_logger.logger.error("E204: Invalid file format given - file is not a .emd file")
            self.parent.print_to_console({"error":"E204: Invalid file format given - file is not a .emd file"})



    def get_directory(self, dirName):
    # Loop through all files in the selected directory
        layer_count = 0
        for filename in os.listdir(dirName):
            try:
                
            
                
                
                file_path = os.path.join(dirName, filename)
                # Check if it's a file (not a subdirectory)
                if os.path.isfile(file_path):
                    self.laser_logger.logger.info(f"Processing file {file_path}...")
                    self.parent.print_to_console({"info": f"Processing file {file_path}..."})
                
                    # Call get_file or any relevant method to process each file

                    if "emd" in filename:
                        layer_count += 1

                        if "1." in filename:
                            self.get_file(file_path)
                            self.laser_logger.logger.info(f"Loaded file {file_path}...")
                            self.parent.print_to_console({"info": f"Loaded file {file_path}..."})

                    else:
                        self.laser_logger.logger.error(f"Invalid file format: {file_path}...")
                        self.parent.print_to_console({"error": f"Invalid file format: {file_path}..."})

            except Exception as e:
                self.laser_logger.logger.error(f"Error: {e}...")
                self.parent.print_to_console({"error": f"Error: {e}"})

        self.parent.count = layer_count
        self.laser_logger.logger.info(f"Total number of layers: {layer_count}")
        self.parent.print_to_console({"info": f"Total number of layers: {layer_count}"})

        # update layer numbers in gui
        self.parent.update_layer_numbers()

                


