import os
import importlib.util
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QVBoxLayout, QScrollArea
from PyQt5.QtGui import QFont
from utils import dialog
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils.dialog import WarningYesNo, WarningOk

# Import sub-UI classes
from ui.settings_screen.software_update.software_update import SoftwareUpdate
from ui.settings_screen.network_settings.network_settings import NetworkSettings

logger = get_logger(__name__)

class SettingsScreen(QWidget):
    def __init__(self, main_window, minimalUI=False):
        super(SettingsScreen, self).__init__()
        self.main_window = main_window
        self.minimalUI = minimalUI
        self.octoprint_client = main_window.octoprint_client

        # Use the centralized logger
        self.logger = get_logger(self.__class__.__name__)

        # Load the UI with proper error handling
        try:
            # Use relative path from the current module's directory
            ui_file_path = os.path.join(os.path.dirname(__file__), "settings_screen.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("Settings screen UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load settings screen UI file: {e}")
            return

        # Initialize UI components using findChild
        # Container widgets
        self.stackedWidget = self.findChild(QStackedWidget, "mainSettingsStackedWidget")
        self.mainSettingsPage = self.findChild(QWidget, "mainSettingsPage")
        self.scrollArea = self.findChild(QScrollArea, "scrollArea")

        # Button widgets for navigation and actions
        self.backButton = self.findChild(QPushButton, "settingsBackButton")
        self.networkSettingsButton = self.findChild(QPushButton, "networkSettingsButton")
        self.softwareUpdateButton = self.findChild(QPushButton, "softwareUpdateButton")
        self.restorePrintSettingsButton = self.findChild(QPushButton, "restorePrintSettingsButton")
        self.restoreFactoryDefaultsButton = self.findChild(QPushButton, "restoreFactoryDefaultsButton")
        self.restartButton = self.findChild(QPushButton, "restartButton")

        # Special widget handling for scroll area
        if self.scrollArea:
            self.scrollAreaWidgetContents = self.scrollArea.findChild(QWidget, 'scrollAreaWidgetContents')
            if self.scrollAreaWidgetContents:
                self.verticalLayout = self.scrollAreaWidgetContents.findChild(QVBoxLayout, 'verticalLayout')
                self.logger.debug("Found scrollAreaWidgetContents and verticalLayout")
            else:
                self.logger.warning("Failed to find scrollAreaWidgetContents")
                self.scrollAreaWidgetContents = None
                self.verticalLayout = None
        else:
            self.scrollAreaWidgetContents = None
            self.verticalLayout = None

        # Validate UI components using simplified check_ui_elements function
        check_ui_elements(self, [
            self.stackedWidget,
            self.mainSettingsPage,
            self.scrollArea,
            self.backButton,
            self.networkSettingsButton,
            self.softwareUpdateButton,
            self.restorePrintSettingsButton,
            self.restoreFactoryDefaultsButton,
            self.restartButton,
            self.scrollAreaWidgetContents,
            self.verticalLayout
        ], "Settings Screen")

        # Connect buttons to their respective functions directly
        self.backButton.clicked.connect(lambda: self.main_window.switch_to_menu_screen())
        self.networkSettingsButton.clicked.connect(self.navigate_to_network_settings)
        self.softwareUpdateButton.clicked.connect(self.navigate_to_software_update)
        self.restorePrintSettingsButton.clicked.connect(self.restore_print_settings)
        self.restoreFactoryDefaultsButton.clicked.connect(self.restore_factory_defaults)
        self.restartButton.clicked.connect(self.restart_system)

        # Initialize all sub-screens
        self.screens = {}
        self._initialize_sub_screens()

        # Special layout handling for certain buttons
        if self.verticalLayout:
            # Add back button at the top
            if self.backButton:
                self.verticalLayout.insertWidget(0, self.backButton)
                self.logger.debug("Added back button to the top of the vertical layout")

            # Add restart button at the bottom
            if self.restartButton:
                self.verticalLayout.addWidget(self.restartButton)
                self.logger.debug("Added restart button to the bottom of the vertical layout")

        # Set the default page in stacked widget
        if self.stackedWidget and self.mainSettingsPage:
            self.stackedWidget.setCurrentWidget(self.mainSettingsPage)
            self.logger.debug("Set default page to mainSettingsPage")
        else:
            self.logger.warning("Could not set default page - required widgets missing")


    def showEvent(self, event):
        """Reset to mainSettingsPage whenever this widget is shown from main window navigation."""
        super().showEvent(event)
        try:
            if self.stackedWidget and self.mainSettingsPage:
                self.stackedWidget.setCurrentWidget(self.mainSettingsPage)
                self.logger.debug("Reset stacked widget to mainSettingsPage on show")
        except Exception as e:
            self.logger.error(f"Error resetting to mainSettingsPage: {e}")

    def tellAndReboot(self, msg="Rebooting...", overlay=True):
        if dialog.WarningOk(self, msg, overlay=overlay):
            os.system('sudo reboot now')
            return True
        return False

    def askAndReboot(self, msg="Are you sure you want to reboot?", overlay=True):
        if dialog.WarningYesNo(self, msg, overlay=overlay):
            os.system('sudo reboot now')
            return True
        return False

    def restore_print_settings(self):
        """Restore the print settings to their default values."""
        self.logger.info("Restoring print settings to default values.")
        # Add logic to restore print settings

        try:
            if dialog.WarningYesNo(self,
                                   "Are you sure you want to restore default print settings?\nWarning: Doing so will erase offsets and bed leveling info",
                                   overlay=True):
                os.system('sudo cp -f firmware/COMMON_FILAMENT_SENSOR.cfg /home/pi/COMMON_FILAMENT_SENSOR.cfg')
                os.system('sudo cp -f firmware/COMMON_GCODE_MACROS.cfg /home/pi/COMMON_GCODE_MACROS.cfg')
                os.system('sudo cp -f firmware/COMMON_IDEX.cfg /home/pi/COMMON_IDEX.cfg')
                os.system('sudo cp -f firmware/COMMON_MOTHERBOARD.cfg /home/pi/COMMON_MOTHERBOARD.cfg')
                os.system(
                    'sudo cp -f firmware/PRINTERS_TWINDRAGON_600x300.cfg /home/pi/PRINTERS_TWINDRAGON_600x300.cfg')
                os.system(
                    'sudo cp -f firmware/PRINTERS_TWINDRAGON_600x600.cfg /home/pi/PRINTERS_TWINDRAGON_600x600.cfg')
                os.system('sudo cp -f firmware/TOOLHEADS_TD-01_TOOLHEAD0.cfg /home/pi/TOOLHEADS_TD-01_TOOLHEAD0.cfg')
                os.system('sudo cp -f firmware/TOOLHEADS_TD-01_TOOLHEAD1.cfg /home/pi/TOOLHEADS_TD-01_TOOLHEAD1.cfg')
                os.system('sudo cp -f firmware/variables.cfg /home/pi/variables.cfg')
                # TODO: check printer variant setting and modify printer.cfg accordingly
                self.octoprint_client.gcode(command='M502')
                self.octoprint_client.gcode(command='M500')
                self.octoprint_client.gcode(command='FIRMWARE_RESTART')
                self.octoprint_client.gcode(command='RESTART')
        except Exception as e:
            self.logger.error("Error in SettingsScreen.restorePrintDefaults: {}".format(e))
            dialog.WarningOk(self, "Error in SettingsScreen.restorePrintDefaults: {}".format(e), overlay=True)

    def restore_factory_defaults(self):
        """Restore the system to factory default settings."""
        self.logger.info("Restoring system to factory default settings.")
        # Add logic to restore factory default settings

        try:
            if dialog.WarningYesNo(self,
                                   "Are you sure you want to restore machine state to factory defaults?\nWarning: Doing so will also reset printer profiles, WiFi & Ethernet config.",
                                   overlay=True):
                os.system('sudo cp -f config/dhcpcd.conf /etc/dhcpcd.conf')
                os.system('sudo cp -f config/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf')
                os.system('sudo rm -rf /home/pi/.octoprint/users.yaml')
                os.system('sudo cp -f config/users.yaml /home/pi/.octoprint/users.yaml')
                os.system('sudo rm -rf /home/pi/.octoprint/printerProfiles/*')
                os.system('sudo rm -rf /home/pi/.octoprint/scripts/gcode')
                os.system('sudo rm -rf /home/pi/.octoprint/print_restore.json')
                os.system('sudo cp -f config/config.yaml /home/pi/.octoprint/config.yaml')
                self.tellAndReboot("Settings restored. Rebooting...")
        except Exception as e:
            self.logger.error("Error in SettingsScreen.restoreFactoryDefaults: {}".format(e))
            dialog.WarningOk(self, "Error in SettingsScreen.restoreFactoryDefaults: {}".format(e), overlay=True)

    def restart_system(self):
        """Restart the system."""
        self.logger.info("Restarting the system.")
        # Add logic to restart the system
        try:
            if WarningYesNo(self, "Are you sure you want to restart the system?", overlay=True):
                self.logger.info("User confirmed reboot")
                os.system("sudo reboot")

            else:
                self.logger.info("User cancelled reboot")
        except Exception as e:
            self.logger.error(f"Error during restart: {e}")
            WarningOk(self, f"Error during restart: {e}", overlay=True)

    def _initialize_sub_screens(self):
        """Initialize all settings sub-screens"""
        try:
            # Create instances of each sub-screen
            self.screens["network_settings"] = NetworkSettings(self, self)
            self.screens["software_update"] = SoftwareUpdate(self, self)

            # Add each screen to the stacked widget
            for name, screen in self.screens.items():
                self.stackedWidget.addWidget(screen)
                self.logger.info(f"Added {name} screen to settings stacked widget")
        except Exception as e:
            self.logger.exception(f"Error initializing sub-screens: {e}")

    def navigate_to_network_settings(self):
        """Open the Network Settings screen."""
        self.logger.info("Navigating to Network Settings screen")
        network_settings_screen = self.screens.get("network_settings")
        if network_settings_screen:
            self.stackedWidget.setCurrentWidget(network_settings_screen)
            self.logger.info("Navigated to network_settings")

    def navigate_to_software_update(self):
        """Open the Software Update screen and display version info."""
        self.logger.info("Navigating to Software Update screen")
        software_update_screen = self.screens.get("software_update")
        if software_update_screen:
            if hasattr(software_update_screen, "displayVersionInfo"):
                software_update_screen.displayVersionInfo()
            self.stackedWidget.setCurrentWidget(software_update_screen)
            self.logger.info("Navigated to software_update")
