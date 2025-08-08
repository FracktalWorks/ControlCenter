import time

import requests
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QMessageBox, QSizePolicy
from ui.home_screen.home_screen import HomeScreen
from ui.loading_screen.loading_screen import LoadingScreen
from ui.menu_screen.menu_screen import MenuScreen
from ui.settings_screen.settings_screen import SettingsScreen
from ui.control_screen.control_screen import ControlScreen
from ui.print_from_location.print_from_location import PrintFromLocation
from ui.calibrate_screen.calibrate_screen import CalibrateScreen
from utils.logger import get_logger
import os
import subprocess
import ui.resources.resource_rc  # Ensure resources are loaded
import config
from utils.styles import printer_status_red, printer_status_green, printer_status_amber, printer_status_blue
# Import the specific dialog functions needed, not just the dialog module
from utils.dialog import WarningOk, WarningYesNo
import glob
from utils import dialog
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class MainWindow(QMainWindow):
    def __init__(self, controller=None, printer_model=None):
        super(MainWindow, self).__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing MainWindow")

        # Flag to indicate if we're in minimal UI mode due to startup error
        self.minimalUI = False
        self.printer_model = printer_model
        self.controller = controller

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.central_widget.setLayout(self.layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stacked_widget.setStyleSheet("background-color: rgb(40, 40, 40);")
        self.layout.addWidget(self.stacked_widget)

        # Screen navigation history for back button functionality
        self.screen_history = []
        self.current_screen = None

        # Next screen for wizard-style multi-step flows
        self.next_screen = None
        self.dialogShown = False
        self.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)  # Use config values for screen resolution
        

        self.loading_screen = LoadingScreen(self)
        self.stacked_widget.addWidget(self.loading_screen)
        self.show()
        self.logger.info("MainWindow initialized successfully, showing loading screen")



    def loadUI(self, minimalUI=False):
            """ Load the user interface screens based on the connection status.
            If minimal is True, load only the essential screens for minimal UI mode.
            """
            self.logger.info("Loading UI with minimal mode set to {}".format(minimalUI))
            self.minimalUI = minimalUI

            if minimalUI:
                self.logger.info("Showing minimal UI due to startup error")
                try:
                    self.octoprint_client = None
                    self.home_screen = HomeScreen(self,minimalUI=True)
                    self.stacked_widget.addWidget(self.home_screen)
                    self.logger.debug("Home screen loaded successfully")
                    self.menu_screen = MenuScreen(self,minimalUI=True)
                    self.stacked_widget.addWidget(self.menu_screen)
                    self.logger.debug("Menu screen loaded successfully")
                    self.settings_screen = SettingsScreen(self,minimalUI=True)
                    self.stacked_widget.addWidget(self.settings_screen)
                    self.logger.debug("Settings screen loaded successfully")
                    self.adjustSize()
                    self.logger.info("MainWindow initialized successfully")
                except Exception as e:
                    self.logger.exception("Error during MainWindow initialization")
                    WarningOk(self,
                            f"Application Error\n\nAn error occurred while initializing the application: {str(e)}\n\nPlease check the logs for more details.",
                            overlay=True)
                WarningOk(
                    self,
                    "Server Connection Error\n\nThe printer server is not reachable. Only basic features are available.\n\n"
                    "Please check your network connection and printer status.",
                    overlay=True
                )
                self.switch_to_home_screen()
            else:
                self.logger.info("Loading full UI - OctoPrint connection successful")
                try:
                    # Load all screens
                    self.octoprint_client = self.controller.octoprint_client
                    self.home_screen = HomeScreen(self, minimalUI=False)
                    self.stacked_widget.addWidget(self.home_screen)
                    self.logger.debug("Home screen loaded successfully")

                    self.menu_screen = MenuScreen(self, minimalUI=False)
                    self.stacked_widget.addWidget(self.menu_screen)
                    self.logger.debug("Menu screen loaded successfully")

                    self.settings_screen = SettingsScreen(self, minimalUI=False)
                    self.stacked_widget.addWidget(self.settings_screen)
                    self.logger.debug("Settings screen loaded successfully")

                    self.control_screen = ControlScreen(self)
                    self.stacked_widget.addWidget(self.control_screen)
                    self.logger.debug("Control screen loaded successfully")

                    self.print_location_screen = PrintFromLocation(self)
                    self.stacked_widget.addWidget(self.print_location_screen)
                    self.logger.debug("Print location screen loaded successfully")

                    self.calibrate_screen = CalibrateScreen(self)
                    self.stacked_widget.addWidget(self.calibrate_screen)
                    self.logger.debug("Calibrate screen loaded successfully")

                    # Adjust the size of the main window to fit its contents
                    self.adjustSize()
                    self.logger.info("MainWindow initialized successfully")
                except Exception as e:
                    self.logger.exception("Error during MainWindow initialization")
                    WarningOk(self,
                            f"Application Error\n\nAn error occurred while initializing the application: {str(e)}\n\nPlease check the logs for more details.",
                            overlay=True)
                self.switch_to_home_screen()
    

    # Screen Navigation Methods
    def switch_screen(self, widget):
        """Switch to the given screen and update navigation history."""
        self.logger.debug(f"Switching to screen: {widget.__class__.__name__}")
        self.logger.debug(
            f"Current screen before switch: {self.current_screen.__class__.__name__ if self.current_screen else None}")

        # Check if we're navigating between a main screen and its subscreens
        is_subscreen_navigation = False

        # Check if current screen has subscreens and the widget is one of those subscreens
        if self.current_screen and hasattr(self.current_screen, 'screens'):
            is_subscreen_navigation = any(widget == subscreen for subscreen in self.current_screen.screens.values())

        # Check if widget has subscreens and the current_screen is one of those subscreens
        if widget and hasattr(widget, 'screens') and self.current_screen:
            is_subscreen_navigation = is_subscreen_navigation or any(
                self.current_screen == subscreen for subscreen in widget.screens.values())

        # Only update history if not navigating between a screen and its subscreens
        if self.current_screen is not None and not is_subscreen_navigation:
            self.screen_history.append(self.current_screen)
            self.logger.debug(f"Added {self.current_screen.__class__.__name__} to history")

        self.current_screen = widget
        self.stacked_widget.setCurrentWidget(widget)

        self.logger.debug(f"History now contains: {[screen.__class__.__name__ for screen in self.screen_history]}")

    def switch_to_previous_screen(self):
        """Go back to the previous screen in history."""
        self.logger.debug("Switching to previous screen")
        if self.screen_history:
            previous_screen = self.screen_history.pop()
            self.current_screen = previous_screen
            self.stacked_widget.setCurrentWidget(previous_screen)
            self.logger.debug(f"Switched to previous screen: {previous_screen.__class__.__name__}")
        else:
            # Default to home screen if no history exists
            self.logger.debug("No screen history, defaulting to home screen")
            self.switch_to_home_screen()

        # Ensure the stacked widget's current page is updated for multi-step wizards
        if hasattr(self.current_screen, 'stackedWidget') and self.current_screen.stackedWidget:
            self.current_screen.stackedWidget.setCurrentIndex(0)

    def switch_to_next_screen(self):
        """Used in multi-step flows like wizards to go to the next screen."""
        self.logger.debug("Attempting to switch to next screen")
        if self.next_screen:
            self.switch_screen(self.next_screen)
            self.next_screen = None
            self.logger.debug("Switched to next screen")
        else:
            # If no next screen is defined, do nothing or go to a default
            self.logger.warning("No next screen defined")

    # Direct navigation methods for main screens
    def switch_to_home_screen(self):
        self.logger.debug("Switching to home screen")
        self.switch_screen(self.home_screen)

    def switch_to_menu_screen(self):
        self.logger.debug("Switching to menu screen")
        self.switch_screen(self.menu_screen)

    def switch_to_settings_screen(self):
        self.logger.debug("Switching to settings screen")
        self.switch_screen(self.settings_screen)

    def switch_to_control_screen(self):
        """
        Sets the current page to the control page
        """
        self.logger.debug("Switching to control screen")
        try:
            self.switch_screen(self.control_screen)
            if self.control_screen.toolToggleTemperatureButton.isChecked():
                self.control_screen.toolTempSpinBox.setProperty(
                    "value", float(self.printer_model.temperatures.get("tool1", 0))
                )
            else:
                self.control_screen.toolTempSpinBox.setProperty(
                    "value", float(self.printer_model.temperatures.get("tool0", 0))
                )
            self.control_screen.bedTempSpinBox.setProperty(
                "value", float(self.printer_model.temperatures.get("bed", 0))
            )
        except Exception as e:
            self.logger.error("Error in MainWaindow.control: {}".format(e))
            dialog.WarningOk(self, "Error in MainWaindow.control: {}".format(e), overlay=True)

    def switch_to_print_location_screen(self):
        self.logger.debug("Switching to print location screen")
        self.switch_screen(self.print_location_screen)

    def switch_to_calibrate_screen(self):
        self.logger.debug("Switching to calibration screen")
        self.switch_screen(self.calibrate_screen)

