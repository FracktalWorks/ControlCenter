from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

class MenuScreen(QWidget):
    def __init__(self, main_window):
        super(MenuScreen, self).__init__()
        self.main_window = main_window

        # Setup logger
        self.logger = setup_logger('menu_screen')

        # Load the UI
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Connect signals to slots
        self._connect_buttons()

    def _load_ui(self):
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('src/ui/menu_screen/menu_screen.ui', self)
            self.logger.info("MenuScreen UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load MenuScreen UI file: {e}")

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        # Navigation tool buttons
        self.tool_buttons = {
            "menuPrintButton": {"type": QToolButton, "instance": None},
            "menuControlButton": {"type": QToolButton, "instance": None},
            "menuCalibrateButton": {"type": QToolButton, "instance": None},
            "menuCartButton": {"type": QToolButton, "instance": None},
            "menuSettingsButton": {"type": QToolButton, "instance": None}
        }
        
        # Basic navigation buttons
        self.push_buttons = {
            "menuBackButton": {"type": QPushButton, "instance": None}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.tool_buttons)
        self.all_components.update(self.push_buttons)
        
        # Find all components using the dictionary
        self._find_components()

    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_type = component_info["type"]
            component = self.findChild(component_type, name)
            component_info["instance"] = component
            
            # Store a direct reference for easy access
            setattr(self, name, component)
            
            # Debug output
            if component:
                self.logger.debug(f"Found {component_type.__name__} '{name}'")
            else:
                self.logger.warning(f"Could not find {component_type.__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create mappings of component categories for reporting
        component_groups = {
            "MenuScreen - Tool Buttons": {name: info["instance"] for name, info in self.tool_buttons.items()},
            "MenuScreen - Push Buttons": {name: info["instance"] for name, info in self.push_buttons.items()}
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)
    
    def _connect_buttons(self):
        """Connect buttons to their respective functions with safety checks"""
        # Map buttons to their handler functions
        button_connections = [
            {"dict": self.tool_buttons, "name": "menuPrintButton", "handler": self.open_print},
            {"dict": self.tool_buttons, "name": "menuControlButton", "handler": self.open_control},
            {"dict": self.tool_buttons, "name": "menuCalibrateButton", "handler": self.open_calibrate},
            {"dict": self.tool_buttons, "name": "menuCartButton", "handler": self.open_cart},
            {"dict": self.tool_buttons, "name": "menuSettingsButton", "handler": self.open_settings},
            {"dict": self.push_buttons, "name": "menuBackButton", "handler": self.go_back}
        ]
        
        # Connect each button to its handler with safety check
        for connection in button_connections:
            button_dict = connection["dict"]
            button_name = connection["name"]
            handler = connection["handler"]
            
            button = button_dict.get(button_name, {}).get("instance")
            if button:
                button.clicked.connect(handler)
                self.logger.debug(f"Connected {button_name} to handler")
            else:
                self.logger.warning(f"Could not connect {button_name} - button not found")

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

    def open_cart(self):
        """Placeholder for open cart logic"""
        self.logger.info("Cart button clicked")

    def open_settings(self):
        """Navigate to the settings screen"""
        self.main_window.switch_to_settings_screen()
        self.logger.info("Settings button clicked")

    def go_back(self):
        """Go back to the previous screen"""
        self.main_window.switch_to_home_screen()
        self.logger.info("Back button clicked")