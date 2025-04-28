import os
import importlib.util
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QVBoxLayout, QScrollArea
from PyQt5.QtGui import QFont
from utils.helpers import check_ui_elements

class SettingsScreen(QWidget):
    def __init__(self, main_window):
        """
        Initialize the SettingsScreen widget.

        Args:
            main_window (QMainWindow): The main window of the application.
        """
        super(SettingsScreen, self).__init__()
        self.main_window = main_window
        
        # Load the UI
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Connect buttons to their respective functions
        self._connect_buttons()

        # Scan the "Settings Screen" folder for subfolders containing .ui files
        self._load_settings_widgets()

        # Set the default page to mainSettingsPage
        self._set_default_page()

    def _load_ui(self):
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('src/ui/settings_screen/settings_screen.ui', self)
            print("Settings screen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load settings screen UI file: {e}")

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        # Container widgets
        self.container_widgets = {
            "mainSettingsStackedWidget": {"type": QStackedWidget, "instance": None},
            "mainSettingsPage": {"type": QWidget, "instance": None},
            "scrollArea": {"type": QScrollArea, "instance": None}
        }
        
        # Button widgets for navigation and actions
        self.action_buttons = {
            "settingsBackButton": {"type": QPushButton, "instance": None},
            "restorePrintSettingsButton": {"type": QPushButton, "instance": None},
            "restoreFactoryDefaultsButton": {"type": QPushButton, "instance": None},
            "restartButton": {"type": QPushButton, "instance": None}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.container_widgets)
        self.all_components.update(self.action_buttons)
        
        # Find all components using the dictionary
        self._find_components()
        
        # Store references to essential widgets for convenience
        self.stackedWidget = self.container_widgets["mainSettingsStackedWidget"]["instance"]
        self.mainSettingsPage = self.container_widgets["mainSettingsPage"]["instance"]
        self.scrollArea = self.container_widgets["scrollArea"]["instance"]
        
        # Find the layout and scroll area contents which need special handling
        if self.scrollArea:
            self.scrollAreaWidgetContents = self.scrollArea.findChild(QWidget, 'scrollAreaWidgetContents')
            if self.scrollAreaWidgetContents:
                self.verticalLayout = self.scrollAreaWidgetContents.findChild(QVBoxLayout, 'verticalLayout')
                print("Found scrollAreaWidgetContents and verticalLayout")
            else:
                print("Failed to find scrollAreaWidgetContents")
                self.scrollAreaWidgetContents = None
                self.verticalLayout = None
        else:
            self.scrollAreaWidgetContents = None
            self.verticalLayout = None

    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_type = component_info["type"]
            component = self.findChild(component_type, name)
            component_info["instance"] = component
            
            # Debug output
            if component:
                print(f"Found {component_type.__name__} '{name}'")
            else:
                print(f"WARNING: Could not find {component_type.__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create mappings of component categories for reporting
        component_groups = {
            "SettingsScreen - Containers": {name: info["instance"] for name, info in self.container_widgets.items()},
            "SettingsScreen - Action Buttons": {name: info["instance"] for name, info in self.action_buttons.items()}
        }
        
        # Additional widgets that were found through special means
        additional_widgets = {
            "scrollAreaWidgetContents": self.scrollAreaWidgetContents,
            "verticalLayout": self.verticalLayout
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)
        
        # Check additional widgets
        check_ui_elements(self, additional_widgets, "SettingsScreen - Special Widgets")

    def _connect_buttons(self):
        """Connect buttons to their respective functions with safety checks"""
        # Map buttons to their handler functions
        button_handlers = {
            "settingsBackButton": self.go_back,
            "restorePrintSettingsButton": self.restore_print_settings,
            "restoreFactoryDefaultsButton": self.restore_factory_defaults,
            "restartButton": self.restart_system
        }
        
        # Connect each button to its handler
        for button_name, handler in button_handlers.items():
            button = self.action_buttons.get(button_name, {}).get("instance")
            if button:
                button.clicked.connect(handler)
                print(f"Connected {button_name} to handler")
            else:
                print(f"WARNING: Could not connect {button_name} - button not found")
        
        # Special layout handling for certain buttons
        if self.verticalLayout:
            # Add back button at the top
            back_button = self.action_buttons.get("settingsBackButton", {}).get("instance")
            if back_button:
                self.verticalLayout.insertWidget(0, back_button)
                print("Added back button to the top of the vertical layout")
                
            # Add restart button at the bottom
            restart_button = self.action_buttons.get("restartButton", {}).get("instance")
            if restart_button:
                self.verticalLayout.addWidget(restart_button)
                print("Added restart button to the bottom of the vertical layout")

    def _set_default_page(self):
        """Set the default page in stacked widget"""
        if self.stackedWidget and self.mainSettingsPage:
            self.stackedWidget.setCurrentWidget(self.mainSettingsPage)
            print("Set default page to mainSettingsPage")
        else:
            print("WARNING: Could not set default page - required widgets missing")

    def go_back(self):
        """Switch back to the main menu screen."""
        print("Back button clicked, returning to menu screen")
        self.main_window.switch_screen(self.main_window.menu_screen)

    def _load_settings_widgets(self):
        """Load settings widgets from subfolders in the "Settings Screen" folder."""
        if not (self.stackedWidget and self.verticalLayout):
            print("Cannot load settings widgets: stackedWidget or verticalLayout is missing")
            return
            
        settings_folder = 'src/ui/settings_screen'
        try:
            for subfolder in os.listdir(settings_folder):
                subfolder_path = os.path.join(settings_folder, subfolder)
                if os.path.isdir(subfolder_path):
                    ui_file = os.path.join(subfolder_path, f'{subfolder}.ui')
                    py_file = os.path.join(subfolder_path, f'{subfolder}.py')
                    if os.path.exists(ui_file) and os.path.exists(py_file):
                        print(f"Loading widget: {subfolder}")
                        try:
                            # Create a button for the subfolder
                            button = self._create_settings_button(
                                subfolder.replace('_', ' ').title(),
                                lambda _, sf=subfolder: self.load_widget(sf)
                            )
                            self.verticalLayout.addWidget(button)

                            # Load the widget and add it to the stacked widget
                            widget_instance = self._create_widget_instance(ui_file, py_file)
                            page = QWidget()
                            layout = QVBoxLayout(page)
                            layout.setContentsMargins(0, 0, 0, 0)
                            layout.setSpacing(0)
                            layout.addWidget(widget_instance)
                            self.stackedWidget.addWidget(page)
                            print(f"Added widget: {widget_instance.objectName()}")
                        except Exception as e:
                            print(f"Error loading widget {subfolder}: {e}")
        except Exception as e:
            print(f"Error loading settings widgets: {e}")

        # Ensure the mainSettingsPage is set as the default page after loading all widgets
        self._set_default_page()

    def _create_settings_button(self, text, handler):
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
        print(f"Switching to widget: {widget_name}")
        if not self.stackedWidget:
            print("ERROR: Cannot switch widgets - stacked widget is missing")
            return
            
        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if widget.findChild(QWidget, widget_name):
                self.stackedWidget.setCurrentWidget(widget)
                print(f"Switched to widget: {widget_name}")
                break

    def _create_widget_instance(self, ui_file, py_file):
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
                    print(f"Error creating widget instance: {e}")
                    print(f"Expected class name: {class_name}")

        return DynamicWidget(self)

    def restore_print_settings(self):
        """Restore the print settings to their default values."""
        print("Restoring print settings to default values.")
        # Add logic to restore print settings

    def restore_factory_defaults(self):
        """Restore the system to factory default settings."""
        print("Restoring system to factory default settings.")
        # Add logic to restore factory default settings

    def restart_system(self):
        """Restart the system."""
        print("Restarting the system.")
        # Add logic to restart the system