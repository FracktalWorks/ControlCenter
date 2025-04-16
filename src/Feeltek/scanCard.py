import threading
import socket
import json
import time
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, Future
from PyQt5.QtCore import QMutex

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
            self.input_file = ""       # name of the .emd file created
            self.input_cli = ""
            self.HOST = "localhost"
            self.PORT = 50000
            self.timeout = 5
            self.file = ""
            self.ret_value = 1
            self.current_file = None

            self.req = {}
            self.function = ""
            self.file_path = ""
            self.formatted_response = {}
            self.layer_id = 0

            self.executor = ThreadPoolExecutor(max_workers=1)
            self.mutex = QMutex()

            # Track file queues for multi-layer printing
            self.file_queue = []
            self.current_file_index = -1

        except Exception as e:
            print(f"E1: Variable initialization failed. {e}")

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
        # print({"info": message})
        pass

    def log_error(self, message: str):
        # print({"error": message})
        pass

    def create_request(self, cmd: str, data: Optional[Dict[str, Any]] = None):
        self.req = {"sid": 0, "cmd": cmd}
        if data:
            self.req["data"] = data

    def execute_command(self, cmd: str, data: Optional[Dict[str, Any]] = None, retries=3, retry_delay=1.0) -> Future:
        def task():
            attempts = 0
            while attempts < retries:
                try:
                    json_string = json.dumps({"sid": 0, "cmd": cmd, "data": data} if data else {"sid": 0, "cmd": cmd})
                    with socket.create_connection((self.HOST, self.PORT), timeout=self.timeout) as sock:
                        sock.sendall(json_string.encode())
                        ret = sock.recv(1024)
                        if ret:
                            ret_decoded = ret.decode('GB18030', errors='replace')
                            json_end_index = ret_decoded.rfind('}') + 1
                            json_content = ret_decoded[:json_end_index]
                            response_data = json.loads(json_content)
                            self.log_info(f"Command {cmd} executed successfully")
                            return {"ret_value": response_data.get("ret"), "response": response_data}
                        else:
                            self.log_error(f"No response received for command: {cmd}")
                            attempts += 1
                            if attempts < retries:
                                time.sleep(retry_delay)
                                self.log_info(f"Retrying command {cmd}, attempt {attempts+1}/{retries}")
                            continue
                except (socket.timeout, socket.error) as e:
                    self.log_error(f"Socket error executing command {cmd}: {e}")
                    attempts += 1
                    if attempts < retries:
                        time.sleep(retry_delay)
                        self.log_info(f"Retrying command {cmd}, attempt {attempts+1}/{retries}")
                    continue
                except json.JSONDecodeError as e:
                    self.log_error(f"JSON decode error executing command {cmd}: {e}")
                    attempts += 1
                    if attempts < retries:
                        time.sleep(retry_delay)
                        self.log_info(f"Retrying command {cmd}, attempt {attempts+1}/{retries}")
                    continue
                except Exception as e:
                    self.log_error(f"Unexpected error executing command {cmd}: {e}")
                    break
            
            # If we've reached this point, all retries failed
            self.log_error(f"Command {cmd} failed after {retries} attempts")
            return {"ret_value": -1, "error": "Command failed after retries"}

        self.mutex.lock()
        future = self.executor.submit(task)
        future.add_done_callback(lambda f: self.mutex.unlock())
        return future

    def get_working_status(self):
        status_map = {
            0: "Waiting",
            1: "Marking",
            2: "Previewing",
            3: "Already working"
        }

        def task():
            self.create_request("get_working_status")
            self.function = "Getting working status"
            try:
                json_string = json.dumps(self.req)
                with socket.create_connection((self.HOST, self.PORT), timeout=self.timeout) as sock:
                    self.log_info(f"{self.function}-> Connecting to {self.HOST}:{self.PORT}...")
                    sock.sendall(json_string.encode())
                    self.log_info(f"{self.function}-> Sending {self.req} to {self.HOST}:{self.PORT} with timeout of {self.timeout}s")
                    ret = sock.recv(1024)
                    if ret:
                        ret_decoded = ret.decode('GB18030', errors='replace')
                        json_end_index = ret_decoded.rfind('}') + 1
                        json_content = ret_decoded[:json_end_index]
                        response_data = json.loads(json_content)
                        connection_status = response_data.get("ret")
                        status_text = status_map.get(connection_status, "Unknown")
                        self.log_info(f"{self.function}-> Response received from {self.HOST}:{self.PORT} - {status_text}")
                        return status_text
                    else:
                        self.log_error(f"E203 - {self.function} not successful - Request {self.req} TIMED OUT!!")
                        return "No response received."
            except (socket.timeout, socket.error, json.JSONDecodeError) as e:
                self.log_error(f"E200 - {self.function} not successful \n {e}")
                return f"Connection to {self.HOST}:{self.PORT} failed: {e}"

        self.mutex.lock()
        future = self.executor.submit(task)
        future.add_done_callback(lambda f: self.mutex.unlock())
        return future

    def open_file(self, file_path: str):
        """Open a file on the scancard."""
        self.current_file = file_path
        return self.execute_command("open_file", {"path": file_path})

    def close_file(self):
        """Close the current file."""
        self.current_file = None
        return self.execute_command("close_file")

    def save_file(self, file_path: str, cover: bool):
        """Save a file on the scancard."""
        return self.execute_command("save_file", {"path": file_path, "cover": 1 if cover else 0})

    def start_mark(self):
        """Start the marking process."""
        future = self.execute_command("start_mark")
        return future

    def stop_mark(self):
        """Stop the marking process."""
        future = self.execute_command("stop_mark")
        return future

    def start_preview(self):
        """Start preview mode."""
        return self.execute_command("start_preview")

    def stop_preview(self):
        """Stop preview mode."""
        return self.execute_command("stop_preview")

    def set_file_queue(self, file_paths: List[str]):
        """Set a queue of files to be processed in sequence."""
        self.file_queue = file_paths
        self.current_file_index = -1

    def load_next_file(self) -> Future:
        """Load the next file in the queue."""
        if not self.file_queue or self.current_file_index >= len(self.file_queue) - 1:
            return None

        self.current_file_index += 1
        file_path = self.file_queue[self.current_file_index]
        return self.open_file(file_path)

    def get_current_file_index(self) -> int:
        """Get the current file index in the queue."""
        return self.current_file_index

    def get_file_queue_length(self) -> int:
        """Get the length of the file queue."""
        return len(self.file_queue)

    def get_markParameters_by_layer(self, layer_id: int):
        """Get marking parameters for a layer."""
        return self.execute_command("get_markParameters_by_layer", {"layer_id": layer_id})

    def set_markParameters_by_layer(self, layer_id: int, params: Dict[str, Any]):
        """Set marking parameters for a layer."""
        data = {"layer_id": layer_id, **params}
        return self.execute_command("set_markParameters_by_layer", data)

    def get_markParameters_by_index(self, index: int, in_index: int):
        """Get marking parameters by index."""
        return self.execute_command("get_markParameters_by_index", {"index": index, "in_index": in_index})

    def set_markParameters_by_index(self, index: int, in_index: int, params: Dict[str, Any]):
        """Set marking parameters by index."""
        data = {"index": index, "in_index": in_index, **params}
        return self.execute_command("set_markParameters_by_index", data)

    def download_parameters(self):
        """Download marking parameters."""
        return self.execute_command("download_Parameters")

    def get_entity_fill_property_by_index(self, index: int, in_index: int):
        """Get fill properties by index."""
        return self.execute_command("get_entity_fill_property_by_index", {"index": index, "in_index": in_index})

    def set_entity_fill_property_by_index(self, index: int, in_index: int, params: Dict[str, Any]):
        """Set fill properties by index."""
        data = {"index": index, "in_index": in_index, **params}
        return self.execute_command("set_entity_fill_property_by_index", data)

    def get_entity_count(self):
        """Get the number of entities."""
        return self.execute_command("get_entity_count")

    def translate_entity(self, dx: float, dy: float):
        """Translate all entities."""
        return self.execute_command("translate_entity", {"dx": dx, "dy": dy})

    def rotate_entity(self, cx: float, cy: float, fAngle: float):
        """Rotate all entities."""
        return self.execute_command("rotate_entity", {"cx": cx, "cy": cy, "fAngle": fAngle})

    def translate_entity_by_index(self, index: int, dx: float, dy: float):
        """Translate entity by index."""
        return self.execute_command("translate_entity_by_index", {"index": index, "dx": dx, "dy": dy})

    def rotate_entity_by_index(self, index: int, cx: float, cy: float, fAngle: float):
        """Rotate entity by index."""
        return self.execute_command("rotate_entity_by_index", {"index": index, "cx": cx, "cy": cy, "fAngle": fAngle})

    def trans_by_model(self, dx: float, dy: float, dz: float, axis: str, fAngle: float, fScale: float):
        """Model transformation."""
        return self.execute_command("TransByModel", {"dx": dx, "dy": dy, "dz": dz, "axis": axis, "fAngle": fAngle, "fScale": fScale})

    def get_name_by_index(self, index: int):
        """Get name by index."""
        return self.execute_command("get_name_by_index", {"index": index})

    def set_name_by_index(self, index: int, name: str):
        """Set name by index."""
        return self.execute_command("set_name_by_index", {"index": index, "name": name})

    def get_content_by_index(self, index: int):
        """Get content by index."""
        return self.execute_command("get_content_by_index", {"index": index})

    def set_content_by_index(self, index: int, content: str):
        """Set content by index."""
        return self.execute_command("set_content_by_index", {"index": index, "content": content})

    def get_pos_size_by_index(self, index: int):
        """Get position and size by index."""
        return self.execute_command("get_pos_size_by_index", {"index": index})

    def set_pos_size_by_index(self, index: int, xPos: float, yPos: float, zPos: float, xSize: float, ySize: float, zSize: float):
        """Set position and size by index."""
        return self.execute_command("set_pos_size_by_index", {
            "index": index, 
            "xPos": xPos, 
            "yPos": yPos, 
            "zPos": zPos, 
            "xSize": xSize, 
            "ySize": ySize, 
            "zSize": zSize
        })

    def get_content_by_name(self, name: str):
        """Get content by name."""
        return self.execute_command("get_content_by_name", {"name": name})

    def set_content_by_name(self, name: str, content: str):
        """Set content by name."""
        return self
    def set_content_by_name(self, name: str, content: str):
        """Set content by name."""
        return self.execute_command("set_content_by_name", {"name": name, "content": content})

    def delete_by_index(self, index: int):
        """Delete object by index."""
        return self.execute_command("delete_by_index", {"index": index})

    def copy_by_index(self, index: int):
        """Copy object by index."""
        return self.execute_command("copy_by_index", {"index": index})

    def mark_by_index(self, index: int):
        """Mark object by index."""
        return self.execute_command("mark_by_index", {"index": index})

    def read_input(self):
        """Read input pins."""
        return self.execute_command("read_input", {"data": 0xff})

    def set_output(self, output: int):
        """Set output pins."""
        return self.execute_command("write_output", {"output": output})

    def clear_error(self):
        """Clear current error."""
        return self.execute_command("clear_error")

    def get_error(self):
        """Get current error."""
        future = self.execute_command("get_error")
        future.add_done_callback(lambda f: self.log_info(f"Error description: {self.ERROR_DESCRIPTIONS.get(self.ret_value, 'Unknown error')}"))
        return future

    def enable_vision(self, bEnVision: bool):
        """Enable or disable vision system."""
        return self.execute_command("enable_vision", {"bEnVision": bEnVision})

    def vision_translate(self, dX: float, dY: float):
        """Translate using vision system."""
        return self.execute_command("vision_translate", {"dX": dX, "dY": dY})

    def vision_rotate(self, cX: float, cY: float, fAngle: float):
        """Rotate using vision system."""
        return self.execute_command("vision_rotate", {"cX": cX, "cY": cY, "fAngle": fAngle})

    # Add this helper method to the Scancard class in src/Feeltek/scanCard.py

    def get_max_layer_count(self):
        """
        Gets the maximum number of layers in the current job.
        Uses get_entity_count as a proxy for the total number of layers.
        
        Returns:
            int: The maximum layer count in the current job, or 1 if not determinable
        """
        try:
            future = self.get_entity_count()
            response = future.result()
            
            if response and response.get("ret_value") == 1:
                # Get the count from the response data
                count = response.get("response", {}).get("data", {}).get("count", 1)
                return max(1, count)  # Ensure at least 1 layer
            else:
                return 1  # Default to 1 layer if we can't determine
        except Exception as e:
            print(f"Error getting max layer count: {e}")
            return 1  # Default to 1 layer on error
    
    def validate_layer_entity(self, layer_id, entity_index=1, entity_subindex=1) -> Future:
        """
        Validates that a specific layer and entity exists.
        
        Args:
            layer_id: The layer ID to validate
            entity_index: The entity index to validate
            entity_subindex: The entity subindex to validate
            
        Returns:
            Future with result containing:
                - valid: True if layer and entity exist, False otherwise
                - message: Description of any validation issues
        """
        def task():
            # First check if we can get marking parameters for this layer
            try:
                mark_params_future = self.get_markParameters_by_layer(layer_id)
                mark_params_result = mark_params_future.result()
                
                if not mark_params_result or mark_params_result.get("ret_value") != 1:
                    return {
                        "valid": False, 
                        "message": f"Layer {layer_id} does not exist or cannot be accessed"
                    }
                
                # Next check if we can get fill properties for this entity
                fill_props_future = self.get_entity_fill_property_by_index(entity_index, entity_subindex)
                fill_props_result = fill_props_future.result()
                
                if not fill_props_result or fill_props_result.get("ret_value") != 1:
                    return {
                        "valid": False, 
                        "message": f"Entity at index {entity_index},{entity_subindex} does not exist"
                    }
                
                # Both checks passed
                return {"valid": True, "message": "Layer and entity validated"}
                
            except Exception as e:
                self.log_error(f"Error validating layer {layer_id}, entity {entity_index},{entity_subindex}: {e}")
                return {"valid": False, "message": f"Validation error: {str(e)}"}
        
        self.mutex.lock()
        future = self.executor.submit(task)
        future.add_done_callback(lambda f: self.mutex.unlock())
        return future                

    def process_multiple_files(self, file_paths: List[str], callback=None):
        """Process multiple files in sequence.
        
        Args:
            file_paths: List of file paths to process
            callback: Optional callback function to call after each file is processed
        
        Returns:
            Future object that will be completed when all files are processed
        """
        def task():
            results = []
            for i, file_path in enumerate(file_paths):
                # Close any open file
                close_result = self.close_file().result()
                
                # Open new file
                open_result = self.open_file(file_path).result()
                if open_result.get("ret_value") != 1:
                    results.append({
                        "file": file_path,
                        "success": False,
                        "error": f"Failed to open file: {self.ERROR_DESCRIPTIONS.get(open_result.get('ret_value'), 'Unknown error')}"
                    })
                    continue
                
                # Mark the file
                mark_result = self.start_mark().result()
                if mark_result.get("ret_value") != 1:
                    results.append({
                        "file": file_path,
                        "success": False,
                        "error": f"Failed to mark file: {self.ERROR_DESCRIPTIONS.get(mark_result.get('ret_value'), 'Unknown error')}"
                    })
                    continue
                
                # Wait for marking to complete
                while True:
                    status = self.get_working_status().result()
                    if status == "Waiting":
                        break
                    time.sleep(0.5)
                
                results.append({
                    "file": file_path,
                    "success": True
                })
                
                # Call callback if provided
                if callback:
                    callback(i, len(file_paths), file_path)
            
            return results
        
        return self.executor.submit(task)