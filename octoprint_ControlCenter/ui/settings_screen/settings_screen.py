import os
import importlib.util
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QVBoxLayout, QScrollArea
from PyQt5.QtGui import QFont
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

class SettingsScreen(QWidget):
    def __init__(self, main_window):
        super(SettingsScreen, self).__init__()
        self.main_window = main_window

        # Setup logger
        self.logger = setup_logger('settings_screen')

        # Load the UI with proper error handling
        try:
            uic.loadUi('octoprint_ControlCenter/ui/settings_screen/settings_screen.ui', self)
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

    def load_settings_widgets(self):
        """Load settings widgets from subfolders in the "Settings Screen" folder."""
        if not (self.stackedWidget and self.verticalLayout):
            self.logger.error("Cannot load settings widgets: stackedWidget or verticalLayout is missing")
            return
            
        settings_folder = 'octoprint_ControlCenter/ui/settings_screen'
        try:
            for subfolder in os.listdir(settings_folder):
                subfolder_path = os.path.join(settings_folder, subfolder)
                if os.path.isdir(subfolder_path):
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

            def load_backend(self, py_file, parent):
                spec = importlib.util.spec_from_file_location("module.name", py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Assuming the class name in the .py file is the same as the subfolder name
                class_name = os.path.basename(py_file).split('.')[0].title().replace('_', '')
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

    def restore_factory_defaults(self):
        """Restore the system to factory default settings."""
        self.logger.info("Restoring system to factory default settings.")
        # Add logic to restore factory default settings

    def restart_system(self):
        """Restart the system."""
        self.logger.info("Restarting the system.")
        # Add logic to restart the system