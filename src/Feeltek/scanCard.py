import threading
import socket
import json
import time
from typing import Optional, Dict, Any
from PyQt5.QtCore import QThread, pyqtSignal
from laserErrorLogging import LaserErrorLogger

class ScancardConnection(QThread):
    status_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.is_running = True
        self.HOST = "localhost"
        self.PORT = 50000

    def run(self):
        while self.is_running:
            self.check_connection()
            time.sleep(5)  # Check every 5 seconds
        
    def stop(self):
        self.is_running = False

    def check_connection(self):
        request = {
            "sid": 0,
            "cmd": "get_working_status",
        }
        try:
            json_string = json.dumps(request)
            with socket.create_connection((self.HOST, self.PORT), timeout=2) as sock:
                sock.sendall(json_string.encode())
                ret = sock.recv(1024)
                if ret:
                    ret_str = ret.decode('GB2312')
                    ret_json = json.loads(ret_str)
                    connection_status = ret_json.get("ret")
                    self.scancard_status_changed.emit(connection_status in ["0", "1", "2", "3"])
                else:
                    self.scancard_status_changed.emit(False)
        except (socket.timeout, socket.error, json.JSONDecodeError):
            self.scancard_status_changed.emit(False)

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
        save_file(self): Saves a file on the Scancard.
        start_preview(self): Starts previewing.
        stop_preview(self): Stops previewing.
        get_markParameters_by_layer(self, layer_id): Gets the marking parameters based on the layer number.
        set_markParameters_by_layer(self, layer_id, params): Sets the marking parameters based on the layer number.
        get_markParameters_by_index(self, index, in_index): Gets the marking parameters based on the index.
        set_markParameters_by_index(self, index, in_index, params): Sets the marking parameters based on the index.
        download_parameters(self): Downloads the marking parameters.
        get_entity_fill_property_by_index(self, index, in_index): Gets the populated parameters based on the index.
        set_entity_fill_property_by_index(self, index, in_index, params): Sets the populated parameters based on the index.
        get_entity_count(self): Gets the number of objects processed.
        translate_entity(self, dx, dy): Translates all objects in the template.
        rotate_entity(self, cx, cy, fAngle): Rotates all objects in the template.
        translate_entity_by_index(self, index, dx, dy): Translates object based on index.
        rotate_entity_by_index(self, index, cx, cy, fAngle): Rotates object based on index.
        trans_by_model(self, dx, dy, dz, axis, fAngle, fScale): Model transformation (translation, rotation, scaling).
        get_name_by_index(self, index): Gets name based on index.
        set_name_by_index(self, index, name): Sets name based on index.
        get_content_by_index(self, index): Gets content based on index.
        set_content_by_index(self, index, content): Sets content based on index.
        get_pos_size_by_index(self, index): Gets object size and position based on index.
        set_pos_size_by_index(self, index, xPos, yPos, zPos, xSize, ySize, zSize): Sets object size and position based on index.
        get_content_by_name(self, name): Gets content based on name.
        set_content_by_name(self, name, content): Sets content based on name.
        delete_by_index(self, index): Deletes objects based on index.
        copy_by_index(self, index): Copies objects based on index.
        mark_by_index(self, index): Marks objects by index.
        read_input(self): Reads input.
        set_output(self, output): Sets output.
    """

    ERROR_DESCRIPTIONS = {
        -1: "Dongle not found",
        0: "Success",
        1: "Failed to open board",
        2: "The USB interface is not a 2.0 interface",
        3: "Failed to open cache area",
        4: "The time in the board is greater than the current computer time",
        5: "Authorization expires",
        6: "Failed to load authorization (the ID.txt authorization file in the License folder in the current directory needs to be updated)",
        7: "Failed to load FPGA driver",
        8: "Failed to set system Parameter",
        9: "Setting calibration failed",
        10: "Setting up stepper motor failed",
        11: "Failed to set up laser",
        12: "Failed to download marking Parameter",
        13: "Marking object does not exist",
        14: "Marking Parameter is invalid",
        15: "Laser status error",
        16: "Scanhead status error",
        17: "Failed to obtain scanhead or laser status",
        18: "Initialization failed before starting marking",
        19: "Failed to start the number sending thread",
        20: "Object content update failed before decomposing data (automatic variable update failed)",
        21: "The object exceeds the marking range",
        22: "Failed to update the content of the data decomposition end object",
        23: "File read error",
        24: "File save error",
        25: "The object does not exist and the move and rotate command cannot be executed",
        26: "The object is not text or barcode, and the content replacement operation cannot be performed",
        27: "Object with specified name not found",
        28: "Marking cannot be started while marking is in progress",
        29: "Invalid scope of work",
        30: "No control card connected",
        31: "Object content update failed",
        32: "File does not exist",
        33: "Index Parameter is out of range",
        34: "Object does not exist",
        35: "The input Parameter pointer is null",
        36: "Failed to modify object name",
        37: "The layer number where the object is located does not exist",
        38: "Preview cannot be started while marking is in progress",
        39: "While marking is in progress, the preview cannot be started repeatedly",
        40: "Preview cannot be stopped while marking",
        41: "No preview object exists",
        42: "Preparing for preview failed",
        43: "Hardware stop signal, external emergency stop",
        44: "Failed to enable the visual positioning module (the dongle does not contain its Function)"
    }

    def __init__(self, parent=None):
        try:
            self.parent = parent
            self.input_file_path = ""  # path to .emd file created
            self.input_file = ""       # name of .emd file created
            self.input_cli = ""
            self.HOST = "localhost"
            self.PORT = 50000
            self.timeout = 5
            self.file = ""
            self.ret_value = 1

            self.req = {}
            self.function = ""
            self.file_path = ""
            self.formatted_response = {}
            self.layer_id = 0

            self.laser_logger = LaserErrorLogger()

            self.connection_thread = ScancardConnection(parent=self)
            self.connection_thread.status_changed.connect(self.handle_status_change)
            self.connection_thread.start()

        except Exception as e:
            print(f"E1: Variable initialization failed. {e}")

    def handle_status_change(self, status: bool):
        if status:
            print("Scancard is connected.")
        else:
            print("Scancard connection lost.")

    def api(self):
        try:
            json_string = json.dumps(self.req)
            with socket.create_connection((self.HOST, self.PORT), timeout=self.timeout) as sock:
                self.log_info(f"{self.function}-> Connecting to {self.HOST}:{self.PORT}...")
                sock.sendall(json_string.encode())
                self.log_info(f"{self.function}-> Sending {self.req} to {self.HOST}:{self.PORT} with timeout of {self.timeout}s")
                ret = sock.recv(1024)
                if ret:
                    self.handle_response(ret)
                else:
                    self.log_error(f"E203 - {self.function} not successful - Request {self.req} TIMED OUT!!")
        except (socket.timeout, socket.error, json.JSONDecodeError) as e:
            self.log_error(f"E200 - {self.function} not successful \n {e}")

    def handle_response(self, response: bytes):
        try:
            ret_decoded = response.decode('GB18030', errors='replace')
            json_end_index = ret_decoded.rfind('}') + 1
            json_content = ret_decoded[:json_end_index]
            response_data = json.loads(json_content)
            formatted_json = json.dumps(response_data, indent=4, ensure_ascii=False)
            self.ret_value = response_data.get("ret")
            self.log_info(f"{self.function}-> Response received from {self.HOST}:{self.PORT} - {formatted_json}")
        except json.JSONDecodeError as e:
            self.log_error(f"E202 - {self.function} not successful \n {e}")

    def log_info(self, message: str):
        self.laser_logger.logger.info(message)
        self.parent.print_to_console({"info": message})

    def log_error(self, message: str):
        self.laser_logger.logger.error(message)
        self.parent.print_to_console({"error": message})

    def create_request(self, cmd: str, data: Optional[Dict[str, Any]] = None):
        self.req = {"sid": 0, "cmd": cmd}
        if data:
            self.req["data"] = data

    def open_file(self, file_path: str):
        self.create_request("open_file", {"path": file_path})
        self.function = "Opening file"
        self.api()

    def close_file(self):
        self.create_request("close_file")
        self.function = "Closing file"
        self.api()

    def save_file(self, file_path: str, cover: bool):
        self.create_request("save_file", {"path": file_path, "cover": cover})
        self.function = "Saving file"
        self.api()

    def get_working_status(self):
        self.create_request("get_working_status")
        self.function = "Getting working status"
        self.api()

    def start_mark(self):
        self.create_request("start_mark")
        self.function = "Starting mark"
        self.api()

    def stop_mark(self):
        self.create_request("stop_mark")
        self.function = "Stopping mark"
        self.api()

    def start_preview(self):
        self.create_request("start_preview")
        self.function = "Starting preview"
        self.api()

    def stop_preview(self):
        self.create_request("stop_preview")
        self.function = "Stopping preview"
        self.api()

    def get_markParameters_by_layer(self, layer_id: int):
        self.create_request("get_markParameters_by_layer", {"layer_id": layer_id})
        self.function = "Getting mark parameters by layer"
        self.api()

    def set_markParameters_by_layer(self, layer_id: int, params: Dict[str, Any]):
        self.create_request("set_markParameters_by_layer", {"layer_id": layer_id, **params})
        self.function = "Setting mark parameters by layer"
        self.api()

    def get_markParameters_by_index(self, index: int, in_index: int):
        self.create_request("get_markParameters_by_index", {"index": index, "in_index": in_index})
        self.function = "Getting mark parameters by index"
        self.api()

    def set_markParameters_by_index(self, index: int, in_index: int, params: Dict[str, Any]):
        self.create_request("set_markParameters_by_index", {"index": index, "in_index": in_index, **params})
        self.function = "Setting mark parameters by index"
        self.api()

    def download_parameters(self):
        self.create_request("download_Parameters")
        self.function = "Downloading parameters"
        self.api()

    def get_entity_fill_property_by_index(self, index: int, in_index: int):
        self.create_request("get_entity_fill_property_by_index", {"index": index, "in_index": in_index})
        self.function = "Getting entity fill property by index"
        self.api()

    def set_entity_fill_property_by_index(self, index: int, in_index: int, params: Dict[str, Any]):
        self.create_request("set_entity_fill_property_by_index", {"index": index, "in_index": in_index, **params})
        self.function = "Setting entity fill property by index"
        self.api()

    def get_entity_count(self):
        self.create_request("get_entity_count")
        self.function = "Getting entity count"
        self.api()

    def translate_entity(self, dx: float, dy: float):
        self.create_request("translate_entity", {"dx": dx, "dy": dy})
        self.function = "Translating entity"
        self.api()

    def rotate_entity(self, cx: float, cy: float, fAngle: float):
        self.create_request("rotate_entity", {"cx": cx, "cy": cy, "fAngle": fAngle})
        self.function = "Rotating entity"
        self.api()

    def translate_entity_by_index(self, index: int, dx: float, dy: float):
        self.create_request("translate_entity_by_index", {"index": index, "dx": dx, "dy": dy})
        self.function = "Translating entity by index"
        self.api()

    def rotate_entity_by_index(self, index: int, cx: float, cy: float, fAngle: float):
        self.create_request("rotate_entity_by_index", {"index": index, "cx": cx, "cy": cy, "fAngle": fAngle})
        self.function = "Rotating entity by index"
        self.api()

    def trans_by_model(self, dx: float, dy: float, dz: float, axis: str, fAngle: float, fScale: float):
        self.create_request("TransByModel", {"dx": dx, "dy": dy, "dz": dz, "axis": axis, "fAngle": fAngle, "fScale": fScale})
        self.function = "Model transformation"
        self.api()

    def get_name_by_index(self, index: int):
        self.create_request("get_name_by_index", {"index": index})
        self.function = "Getting name by index"
        self.api()

    def set_name_by_index(self, index: int, name: str):
        self.create_request("set_name_by_index", {"index": index, "name": name})
        self.function = "Setting name by index"
        self.api()

    def get_content_by_index(self, index: int):
        self.create_request("get_content_by_index", {"index": index})
        self.function = "Getting content by index"
        self.api()

    def set_content_by_index(self, index: int, content: str):
        self.create_request("set_content_by_index", {"index": index, "content": content})
        self.function = "Setting content by index"
        self.api()

    def get_pos_size_by_index(self, index: int):
        self.create_request("get_pos_size_by_index", {"index": index})
        self.function = "Getting position and size by index"
        self.api()

    def set_pos_size_by_index(self, index: int, xPos: float, yPos: float, zPos: float, xSize: float, ySize: float, zSize: float):
        self.create_request("set_pos_size_by_index", {"index": index, "xPos": xPos, "yPos": yPos, "zPos": zPos, "xSize": xSize, "ySize": ySize, "zSize": zSize})
        self.function = "Setting position and size by index"
        self.api()

    def get_content_by_name(self, name: str):
        self.create_request("get_content_by_name", {"name": name})
        self.function = "Getting content by name"
        self.api()

    def set_content_by_name(self, name: str, content: str):
        self.create_request("set_content_by_name", {"name": name, "content": content})
        self.function = "Setting content by name"
        self.api()

    def delete_by_index(self, index: int):
        self.create_request("delete_by_index", {"index": index})
        self.function = "Deleting by index"
        self.api()

    def copy_by_index(self, index: int):
        self.create_request("copy_by_index", {"index": index})
        self.function = "Copying by index"
        self.api()

    def mark_by_index(self, index: int):
        self.create_request("mark_by_index", {"index": index})
        self.function = "Marking by index"
        self.api()

    def read_input(self):
        self.create_request("read_input", {"data": 0xff})
        self.function = "Reading input"
        self.api()

    def set_output(self, output: int):
        self.create_request("write_output", {"output": output})
        self.function = "Setting output"
        self.api()

    def clear_error(self):
        self.create_request("clear_error")
        self.function = "Clearing errors"
        self.api()

    def get_error(self):
        self.create_request("get_error")
        self.function = "Getting error"
        self.api()
        error_description = self.ERROR_DESCRIPTIONS.get(self.ret_value, "Unknown error")
        self.parent.print_to_console({"info": f"Error description: {error_description}"})

    def enable_vision(self, bEnVision: bool):
        self.create_request("enable_vision", {"bEnVision": bEnVision})
        self.function = "Enabling vision"
        self.api()

    def vision_translate(self, dX: float, dY: float):
        self.create_request("vision_translate", {"dX": dX, "dY": dY})
        self.function = "Translating vision"
        self.api()

    def vision_rotate(self, cX: float, cY: float, fAngle: float):
        self.create_request("vision_rotate", {"cX": cX, "cY": cY, "fAngle": fAngle})
        self.function = "Rotating vision"
        self.api()