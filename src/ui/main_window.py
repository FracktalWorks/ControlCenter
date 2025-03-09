from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from ui.loading_screen.loading_screen import LoadingScreen
from ui.tab_screen.tab_screen import TabScreen
from config import Config
from models.printer_status import PrinterStatus

from thermalCamera.thermal_camera import ThermalCamera
if not Config.DEVELOPMENT_MODE:
    from moonraker_client.moonraker_client import MoonrakerAPI


import ui.resources.resource_rc  # Ensure resources are loaded
import traceback

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.printer_status = PrinterStatus() # Create an instance of the PrinterStatus model

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)
        
        self.thermal_camera = ThermalCamera()
        self.thermal_camera.frame_ready.connect(self.update_frame)
        self.thermal_camera.start()

        # Initialize MoonrakerAPI if not in development mode
        if not Config.DEVELOPMENT_MODE:
            self.moonraker_api = MoonrakerAPI('http://your-moonraker-url')
        else:
            self.moonraker_api = None



        # Load sub UIs based on configuration
        self.load_loading_screen()
        self.load_tab_screen()
        self.switch_screen(self.loading_screen)

        # Adjust the size of the main window to fit its contents
        self.adjustSize()

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

    def update_frame(self, frame, temps):
        if frame is not None and temps is not None:
            self.printer_status.updateTemperatures(frame, temps)   
            print(temps)         



