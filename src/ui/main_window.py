from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from ui.loading_screen.loading_screen import LoadingScreen
from ui.tab_screen.tab_screen import TabScreen
from config import Config
from models.printer_status import PrinterStatus
from PyQt5.QtCore import QTimer
from temperatureController.chamberTemperatureController import ChamberTemperatureController  # Ensure this import is present
from Feeltek.scanCard import Scancard  # Import Scancard
from processAutomationController.processAutomationController import ProcessAutomationController
from utils.helpers import run_async

if not Config.DEVELOPMENT_MODE:
    from temperatureController.heaterBoard import HeaterBoard
    from thermalCamera.thermal_camera import ThermalCamera
    from rgbCamera.rgbCamera import RGBCamera
    from moonrakerClient.moonrakerClient import MoonrakerAPI

import ui.resources.resource_rc  # Ensure resources are loaded
import traceback

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.printer_status = PrinterStatus()  # Create an instance of the PrinterStatus model
        self.process_automation_controller = ProcessAutomationController(self)  # Initialize ProcessAutomationController

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)
        
        if not Config.DEVELOPMENT_MODE:
            self.thermal_camera = ThermalCamera(roi=(2, 13, 59, 64))
            self.thermal_camera.thermal_camera_frame_ready.connect(self.update_frame)
            self.thermal_camera.max_temp_signal.connect(self.update_max_temp)  # Connect max_temp_signal to update_max_temp
            self.thermal_camera.start()

            self.rgb_camera = RGBCamera()
            self.rgb_camera.rgb_camera_frame_ready.connect(self.update_rgb_frame)
            self.rgb_camera.start()
        else:
            self.thermal_camera = None
            self.rgb_camera = None

        # Initialize HeaterBoard and ChamberTemperatureController if not in development mode
        if not Config.DEVELOPMENT_MODE:
            self.chamber_temp_controller = ChamberTemperatureController(self.printer_status)
        else:
            self.chamber_temp_controller = None

        # Initialize MoonrakerAPI if not in development mode
        if not Config.DEVELOPMENT_MODE:
            self.moonraker_api = MoonrakerAPI('http://10.20.1.121')
        else:
            self.moonraker_api = MockMoonrakerAPI()

        # Initialize Scancard
        self.scancard = Scancard(self)

        # Set up a QTimer to periodically check the Scancard status
        self.scancard_timer = QTimer(self)
        self.scancard_timer.timeout.connect(self.handle_scancard_status_change)
        self.scancard_timer.start(500)  # Check status every 2000 ms (2 seconds

        # Load sub UIs based on configuration
        self.load_loading_screen()
        self.load_tab_screen()
        self.switch_screen(self.loading_screen)

        # Adjust the size of the main window to fit its contents
        self.adjustSize()

        self.process_automation_controller.progress_update_signal.connect(self.update_progress_bar)

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
        self.adjustSize()  # Adjust size after switching screens

    def switch_to_tab_screen(self):
        self.switch_screen(self.tab_screen)

    def update_frame(self, frame, chamberTemperatures):
        if frame is not None and chamberTemperatures is not None:
            # Convert temps values to regular float
            converted_temps = {key: float(value) for key, value in chamberTemperatures.items()}
            self.printer_status.updateTemperatures(frame, converted_temps)

    def update_max_temp(self, max_temp):
        self.printer_status.updateMaxTemp(max_temp)

    def update_rgb_frame(self, frame):
        if frame is not None:
            self.printer_status.updateRGBFrame(frame)

    # Add methods to interact with Scancard
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
            # print(f"Scancard status: {self.printer_status.scancard_status}")
        except Exception as e:
            print(f"Failed to update Scancard status: {e}")

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


