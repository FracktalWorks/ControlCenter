"""Menu screen module for OctoPrint Control Center.

This module provides the main navigation menu interface allowing users to
access different application screens including print, control, calibrate,
filament/nozzle management, and settings.
"""
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton
from utils.helpers import check_ui_elements
from utils.logger import get_logger


class MenuScreen(QWidget):
    """Main navigation menu screen widget.
    
    Provides navigation buttons to access different application screens
    including print management, control panel, calibration, filament/nozzle
    settings, and application settings.
    """
    
    def __init__(self, main_window, minimalUI=False):
        """Initialize the menu screen.
        
        Args:
            main_window: Reference to the main application window.
            minimalUI: Whether to enable minimal UI mode with limited functionality.
        """
        super(MenuScreen, self).__init__()
        self.main_window = main_window
        self.minimalUI = minimalUI

        # Use centralized logger
        self.logger = get_logger(self.__class__.__name__)

        # Load the UI with proper error handling
        try:
            # Use relative path from the current module's directory
            ui_file_path = os.path.join(os.path.dirname(__file__), "menu_screen.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("MenuScreen UI loaded successfully")
        except Exception as e:
            self.logger.exception(f"Failed to load MenuScreen UI file: {e}")
            raise RuntimeError(f"Cannot initialize MenuScreen: UI file loading failed - {e}")
            
        # Initialize UI components
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

        if self.minimalUI:
             # Disable buttons in Menu Screen
            self.menuControlButton.setEnabled(False)
            self.menuPrintButton.setEnabled(False)
            self.menuCalibrateButton.setEnabled(False)
            self.menuFilamentNozzleButton.setEnabled(False)
        else:
            # Enable buttons in Menu Screen
            self.menuControlButton.setEnabled(True)
            self.menuPrintButton.setEnabled(True)
            self.menuCalibrateButton.setEnabled(True)
            self.menuFilamentNozzleButton.setEnabled(True)

    def open_print(self):
        """Navigate to the print location screen."""
        try:
            self.main_window.switch_to_print_location_screen()
            self.logger.info("Print button clicked")
        except Exception as e:
            self.logger.error(f"Error navigating to print screen: {e}")

    def open_control(self):
        """Navigate to the control screen."""
        try:
            self.main_window.switch_to_control_screen()
            self.logger.info("Control button clicked")
        except Exception as e:
            self.logger.error(f"Error navigating to control screen: {e}")

    def open_calibrate(self):
        """Navigate to the calibrate screen."""
        try:
            self.main_window.switch_to_calibrate_screen()
            self.logger.info("Calibrate button clicked")
        except Exception as e:
            self.logger.error(f"Error navigating to calibrate screen: {e}")

    def open_menuFilamentNozzle(self):
        """Navigate to filament and nozzle management screen.
        
        TODO: Implement navigation to filament/nozzle management screen
        when the corresponding screen module is available.
        """
        self.logger.info("FilamentNozzle button clicked")
        # TODO: Add navigation when filament/nozzle screen is implemented
        # self.main_window.switch_to_filament_nozzle_screen()

    def open_settings(self):
        """Navigate to the settings screen."""
        try:
            self.main_window.switch_to_settings_screen()
            self.logger.info("Settings button clicked")
        except Exception as e:
            self.logger.error(f"Error navigating to settings screen: {e}")

    def go_back(self):
        """Go back to the previous screen."""
        try:
            self.main_window.switch_to_home_screen()
            self.logger.info("Back button clicked")
        except Exception as e:
            self.logger.error(f"Error navigating to home screen: {e}")