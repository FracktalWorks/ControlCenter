import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton
from utils.helpers import check_ui_elements
from utils.logger import get_logger

logger = get_logger(__name__)

class MenuScreen(QWidget):
    def __init__(self, main_window):
        super(MenuScreen, self).__init__()
        self.main_window = main_window

        # Use centralized logger
        self.logger = get_logger(self.__class__.__name__)

        # Load the UI with proper error handling
        try:
            # Use relative path from the current module's directory
            ui_file_path = os.path.join(os.path.dirname(__file__), "menu_screen.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("MenuScreen UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load MenuScreen UI file: {e}")
            
        # Initialize UI components directly
        # Navigation tool buttons
        self.menuPrintButton = self.findChild(QToolButton, "menuPrintButton")
        self.menuControlButton = self.findChild(QToolButton, "menuControlButton")
        self.menuCalibrateButton = self.findChild(QToolButton, "menuCalibrateButton")
        self.menuFilamentNozzleButton = self.findChild(QToolButton, "menuFilamentNozzleButton")
        self.menuSettingsButton = self.findChild(QToolButton, "menuSettingsButton")
        
        # Basic navigation buttons
        self.menuBackButton = self.findChild(QPushButton, "menuBackButton")
        
        # Validate UI components with the simplified check_ui_elements function
        all_ui_elements = [
            self.menuPrintButton,
            self.menuControlButton, 
            self.menuCalibrateButton,
            self.menuFilamentNozzleButton,
            self.menuSettingsButton,
            self.menuBackButton
        ]
        check_ui_elements(self, all_ui_elements, "MenuScreen")
        
        # Connect buttons to their respective methods directly
        if self.menuPrintButton:
            self.menuPrintButton.clicked.connect(self.open_print)
            self.logger.debug("Connected menuPrintButton to handler")
            
        if self.menuControlButton:
            self.menuControlButton.clicked.connect(self.open_control)
            self.logger.debug("Connected menuControlButton to handler")
            
        if self.menuCalibrateButton:
            self.menuCalibrateButton.clicked.connect(self.open_calibrate)
            self.logger.debug("Connected menuCalibrateButton to handler")
            
        if self.menuFilamentNozzleButton:
            self.menuFilamentNozzleButton.clicked.connect(self.open_menuFilamentNozzle)
            self.logger.debug("Connected menuFilamentNozzleButton to handler")
            
        if self.menuSettingsButton:
            self.menuSettingsButton.clicked.connect(self.open_settings)
            self.logger.debug("Connected menuSettingsButton to handler")
            
        if self.menuBackButton:
            self.menuBackButton.clicked.connect(self.go_back)
            self.logger.debug("Connected menuBackButton to handler")

    def open_print(self):
        """Navigate to the print location screen"""
        self.main_window.switch_to_print_location_screen()
        self.logger.info("Print button clicked")

    def open_control(self):
        """Navigate to the control screen"""
        self.main_window.switch_to_control_screen()
        self.logger.info("Control button clicked")

    def open_calibrate(self):
        """Navigate to the calibrate screen"""
        self.main_window.switch_to_calibrate_screen()
        self.logger.info("Calibrate button clicked")

    def open_menuFilamentNozzle(self):
        """Placeholder for open menuFilamentNozzle logic"""
        self.logger.info("FilamentNozzle button clicked")

    def open_settings(self):
        """Navigate to the settings screen"""
        self.main_window.switch_to_settings_screen()
        self.logger.info("Settings button clicked")

    def go_back(self):
        """Go back to the previous screen"""
        self.main_window.switch_to_home_screen()
        self.logger.info("Back button clicked")