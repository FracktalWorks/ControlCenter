from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from ui.loading_screen.loading_screen import LoadingScreen
from ui.tab_screen.tab_screen import TabScreen
from config import Config
from models.printer_status import PrinterStatus
from PyQt5.QtCore import QTimer
from temperatureController.chamberTemperatureController import ChamberTemperatureController
from Feeltek.scanCard import Scancard
from processAutomationController.processAutomationController import ProcessAutomationController
from layerManager.layerQueueManager import LayerQueueManager
from multiLayerPrintController import MultiLayerPrintController
from layerManager.printStateManager import PrintStateManager
from utils.helpers import run_async

if not Config.DEVELOPMENT_MODE:
    from temperatureController.heaterBoard import HeaterBoard
    from thermalCamera.thermal_camera import ThermalCamera
    from rgbCamera.rgbCamera import RGBCamera
    from moonrakerClient.moonrakerClient import MoonrakerAPI

import ui.resources.resource_rc
import traceback

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.printer_status = PrinterStatus()
        self.process_automation_controller = ProcessAutomationController(self)

        

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)
        
        if not Config.DEVELOPMENT_MODE:
            self.thermal_camera = ThermalCamera(roi=(2, 13, 59, 64))
            self.thermal_camera.thermal_camera_frame_ready.connect(self.update_frame)
            self.thermal_camera.max_temp_signal.connect(self.update_max_temp)
            self.thermal_camera.start()

            self.rgb_camera = RGBCamera()
            self.rgb_camera.rgb_camera_frame_ready.connect(self.update_rgb_frame)
            self.rgb_camera.start()
        else:
            self.thermal_camera = None
            self.rgb_camera = None

        if not Config.DEVELOPMENT_MODE:
            self.chamber_temp_controller = ChamberTemperatureController(self.printer_status)
        else:
            self.chamber_temp_controller = None

        if not Config.DEVELOPMENT_MODE:
            self.moonraker_api = MoonrakerAPI('http://10.20.1.135')
        else:
            self.moonraker_api = MockMoonrakerAPI()

        self.scancard = Scancard(self) if not Config.DEVELOPMENT_MODE else MockScancard(self)

        self.scancard_timer = QTimer(self)
        self.scancard_timer.timeout.connect(self.handle_scancard_status_change)
        self.scancard_timer.start(5000)

        self.load_loading_screen()
        self.load_tab_screen()
        self.switch_screen(self.loading_screen)

        self.adjustSize()

        self.process_automation_controller.progress_update_signal.connect(self.update_progress_bar)

        # Initialize multi-layer printing components
        self.layer_queue_manager = LayerQueueManager()
        self.print_state_manager = PrintStateManager()
        self.multi_layer_controller = MultiLayerPrintController(self)

    def update_progress_bar(self, value):
        self.home_screen.printProgressBar.setValue(value)
        self.control_screen.recoaterProgressBar.setValue(value)

    def load_loading_screen(self):
        self.loading_screen = LoadingScreen(self)
        self.stacked_widget.addWidget(self.loading_screen)
 
    def load_tab_screen(self):
        self.tab_screen = TabScreen(self)
        self.stacked_widget.addWidget(self.tab_screen)

    def switch_screen(self, widget):
        print(f"Switching to screen: {widget}")
        self.stacked_widget.setCurrentWidget(widget)
        self.adjustSize()

    def switch_to_tab_screen(self):
        self.switch_screen(self.tab_screen)

    def update_frame(self, frame, chamberTemperatures):
        if frame is not None and chamberTemperatures is not None:
            converted_temps = {key: float(value) for key, value in chamberTemperatures.items()}
            self.printer_status.updateTemperatures(frame, converted_temps)

    def update_max_temp(self, max_temp):
        self.printer_status.updateMaxTemp(max_temp)

    def update_rgb_frame(self, frame):
        if frame is not None:
            self.printer_status.updateRGBFrame(frame)

    def start_scancard_mark(self):
        self.scancard.start_mark()

    def stop_scancard_mark(self):
        self.scancard.stop_mark()
        
    @run_async
    def handle_scancard_status_change(self):
        future = self.scancard.get_working_status()
        future.add_done_callback(self.update_scancard_status)

    def update_scancard_status(self, future):
        try:
            status = future.result()
            self.printer_status.updateScancardStatus(status)
            self.control_screen.scanCardStatusLabel.setText("Status: " + self.printer_status.scancard_status)
        except Exception as e:
            print(f"Failed to update Scancard status: {e}")

    def open_scancard_file(self, file_path: str):
        close_future = self.scancard.close_file()
        close_future.add_done_callback(lambda f: self._handle_close_file_result_and_open(f, file_path))

    def _handle_close_file_result_and_open(self, future, file_path: str):
        try:
            result = future.result()
            if result is None:
                raise ValueError("No result returned from close_file command")
            meaning = self._get_scancard_return_meaning(result.get("ret_value"))
            print(f"Close file result: {result} - {meaning}")
        except Exception as e:
            print(f"Failed to close Scancard file: {e}")
        finally:
            print("Executing finally block")
            self._open_scancard_file(file_path)

    def _open_scancard_file(self, file_path: str):
        print(f"Opening Scancard file: {file_path}")
        future = self.scancard.open_file(file_path)
        future.add_done_callback(lambda f: self._handle_open_file_result(f, file_path))

    def _handle_open_file_result(self, future, file_path: str):
        try:
            result = future.result()
            if result is None:
                raise ValueError("No result returned from open_file command")
            meaning = self._get_scancard_return_meaning(result.get("ret_value"))
            print(f"Open file result: {result} - {meaning}")
            self.update_file_info_label(file_path)
        except Exception as e:
            print(f"Failed to open Scancard file: {e}")

    def _get_scancard_return_meaning(self, ret_value):
        meanings = {
            1: "Execution successful",
            0: "Not executed",
            -1: "Failed to open",
            -2: "File does not exist"
        }
        return meanings.get(ret_value, "Unknown return value")

    def update_file_info_label(self, file_path: str):
        self.home_screen.fileInfoLabel.setText(file_path)
        
    def resume_print_from_saved_state(self, state_file):
        """Resume a print from a saved state file."""
        if self.multi_layer_controller.load_print_state(state_file):
            self.multi_layer_controller.resume_multi_layer_print()
        else:
            print("Failed to load print state")


class MockMoonrakerAPI:
    def __init__(self):
        print("MockMoonrakerAPI initialized")

    def send_gcode(self, cmd):
        print(f"MockMoonrakerAPI.send_gcode called with cmd: {cmd}")

    def query_status(self):
        print("MockMoonrakerAPI.query_status called")
        return {"status": "mock_status"}

    def query_temperatures(self):
        print("MockMoonrakerAPI.query_temperatures called")
        return {"temperatures": "mock_temperatures"}


class MockScancard:
    def __init__(self, main_window):
        print("MockScancard initialized")

    def start_mark(self):
        print("MockScancard.start_mark called")
        return MockFuture()

    def stop_mark(self):
        print("MockScancard.stop_mark called")
        return MockFuture()

    def get_working_status(self):
        print("MockScancard.get_working_status called")
        return MockFuture()

    def open_file(self, file_path):
        print(f"MockScancard.open_file called with file_path: {file_path}")
        return MockFuture()

    def close_file(self):
        print("MockScancard.close_file called")
        return MockFuture()


class MockFuture:
    def add_done_callback(self, callback):
        print("MockFuture.add_done_callback called")
        callback(self)

    def result(self):
        print("MockFuture.result called")
        return {"ret_value": 1}  # Simulated response