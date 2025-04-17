from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from ui.loading_screen.loading_screen import LoadingScreen
from ui.tab_screen.tab_screen import TabScreen
from config import Config
from models.printer_status import PrinterStatus
from PyQt5.QtCore import QTimer
from Feeltek.scanCard import Scancard  # Import Scancard
from processAutomationController.processAutomationController import ProcessAutomationController
from pi_instruments.pi_intruments import pi_control
from processAutomationController.processAutomationController import ProcessAutomationController

from utils.helpers import run_async

if not Config.DEVELOPMENT_MODE:
    pass


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
            pass
            self.thermal_camera = None
            self.rgb_camera = None


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