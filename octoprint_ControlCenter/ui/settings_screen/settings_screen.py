import os
import importlib.util
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QVBoxLayout, QScrollArea
from PyQt5.QtGui import QFont
from utils import dialog
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils.dialog import WarningYesNo, WarningOk

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
            self.restorePrintSettingsButton,
            self.restoreFactoryDefaultsButton,
            self.restartButton,
            self.scrollAreaWidgetContents,
            self.verticalLayout
        ], "Settings Screen")

        # Connect buttons to their respective functions directly
        if self.backButton:
            self.backButton.clicked.connect(self.go_back)
            self.logger.debug("Connected settingsBackButton to handler")

        if self.restorePrintSettingsButton:
            self.restorePrintSettingsButton.clicked.connect(self.restore_print_settings)
            self.logger.debug("Connected restorePrintSettingsButton to handler")

        if self.restoreFactoryDefaultsButton:
            self.restoreFactoryDefaultsButton.clicked.connect(self.restore_factory_defaults)
            self.logger.debug("Connected restoreFactoryDefaultsButton to handler")

        if self.restartButton:
            self.restartButton.clicked.connect(self.restart_system)
            self.logger.debug("Connected restartButton to handler")

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

        # Load settings widgets from subfolders
        self.load_settings_widgets()

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

    def load_settings_widgets(self):
        """Load settings widgets from subfolders in the "Settings Screen" folder."""
        if not (self.stackedWidget and self.verticalLayout):
            self.logger.error("Cannot load settings widgets: stackedWidget or verticalLayout is missing")
            return

        # Use relative path from current module directory
        settings_folder = os.path.dirname(__file__)
        try:
            for subfolder in os.listdir(settings_folder):
                subfolder_path = os.path.join(settings_folder, subfolder)
                if os.path.isdir(subfolder_path):
                    # Skip software update widget if in minimal UI mode
                    if self.minimalUI and subfolder.lower() in ['software_update', 'softwareupdate', 'software update']:
                        self.logger.info(f"Skipping widget {subfolder} due to minimal UI mode")
                        continue
                        
                    ui_file = os.path.join(subfolder_path, f'{subfolder}.ui')
                    py_file = os.path.join(subfolder_path, f'{subfolder}.py')
                    if os.path.exists(ui_file) and os.path.exists(py_file):
                        self.logger.info(f"Loading widget: {subfolder}")
                        try:
                            # Create a button for the subfolder
                            button = self.create_settings_button(
                                subfolder.replace('_', ' ').title(),
                                lambda _, sf=subfolder: self.load_widget(sf)
                            )
                            self.verticalLayout.addWidget(button)

                            # Load the widget and add it to the stacked widget
                            widget_instance = self.create_widget_instance(ui_file, py_file)
                            page = QWidget()
                            layout = QVBoxLayout(page)
                            layout.setContentsMargins(0, 0, 0, 0)
                            layout.setSpacing(0)
                            layout.addWidget(widget_instance)
                            self.stackedWidget.addWidget(page)
                            self.logger.info(f"Added widget: {widget_instance.objectName()}")
                        except Exception as e:
                            self.logger.error(f"Error loading widget {subfolder}: {e}")
        except Exception as e:
            self.logger.error(f"Error loading settings widgets: {e}")

    def create_settings_button(self, text, handler):
        """Create a styled settings button with the given text and handler"""
        button = QPushButton(text)
        button.setMinimumHeight(100)
        button.setFont(QFont("Gotham Light", 16))
        button.setStyleSheet("""
            QPushButton {
                border: 1px solid rgb(87, 87, 87);
                background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0.188, stop:0 rgba(180, 180, 180, 255), stop:1 rgba(255, 255, 255, 255));
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #dadbde, stop: 1 #f6f7fa);
            }
            QPushButton:flat {
                border: none; /* no border for a flat push button */
            }
            QPushButton:default {
                border-color: navy; /* make the default button prominent */
            }
        """)
        button.clicked.connect(handler)
        return button

    def load_widget(self, widget_name):
        """
        Switch to the specified widget in the stacked widget.

        Args:
            widget_name (str): The name of the widget to switch to.
        """
        self.logger.info(f"Switching to widget: {widget_name}")
        if not self.stackedWidget:
            self.logger.error("Cannot switch widgets - stacked widget is missing")
            return

        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if widget.findChild(QWidget, widget_name):
                self.stackedWidget.setCurrentWidget(widget)
                self.logger.info(f"Switched to widget: {widget_name}")
                break

    def create_widget_instance(self, ui_file, py_file):
        """
        Create an instance of a widget from the specified .ui and .py files.

        Args:
            ui_file (str): The path to the .ui file.
            py_file (str): The path to the .py file.

        Returns:
            QWidget: An instance of the dynamically loaded widget.
        """

        class DynamicWidget(QWidget):
            def __init__(self, parent):
                super(DynamicWidget, self).__init__(parent)
                uic.loadUi(ui_file, self)
                self.setObjectName(os.path.basename(ui_file).split('.')[0])
                self.load_backend(py_file, parent)
                print("PARENT NAME: ", parent)

            def load_backend(self, py_file, parent):
                spec = importlib.util.spec_from_file_location("module.name", py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Assuming the class name in the .py file is the same as the subfolder name
                class_name = os.path.basename(py_file).split('.')[0].title().replace('_', '')
                print("Class name: ", class_name)
                print("py_file: ", py_file)

                try:
                    backend_class = getattr(module, class_name)
                    backend_instance = backend_class(self, parent)
                    self.backend = backend_instance
                except AttributeError as e:
                    parent.logger.error(f"Error creating widget instance: {e}")
                    parent.logger.error(f"Expected class name: {class_name}")

        return DynamicWidget(self)

    def go_back(self):
        """Switch back to the main menu screen."""
        self.logger.info("Back button clicked, returning to menu screen")
        self.main_window.switch_screen(self.main_window.menu_screen)

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
