from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements

class NetworkSettings(QWidget):
    """
    Network Settings widget that allows users to configure network connections
    including WiFi and Static IP settings.
    """
    def __init__(self, parent, settings_screen):
        super(NetworkSettings, self).__init__(parent)
        self.mainSettingsWidget = settings_screen  # Reference to the main settings widget
        
        # Load the UI
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Connect buttons to their respective functions
        self._connect_buttons()
        
        # Set the default screen to network settings page
        self._set_default_page()

    def _load_ui(self):
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('src/ui/settings_screen/network_settings/network_settings.ui', self)
            print("NetworkSettings UI loaded successfully")
        except Exception as e:
            print(f"Failed to load NetworkSettings UI file: {e}")

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        # Navigation buttons
        self.navigation_buttons = {
            "networkSettingsBackButton": {"type": QPushButton, "instance": None},
            "networkInfoBackButton": {"type": QPushButton, "instance": None},
            "staticIPSettingsCancelButton": {"type": QPushButton, "instance": None},
            "wifiSettingsCancelButton": {"type": QPushButton, "instance": None}
        }
        
        # Action buttons
        self.action_buttons = {
            "networkInfoButton": {"type": QPushButton, "instance": None},
            "configureStaticIPButton": {"type": QPushButton, "instance": None},
            "configureWifiButton": {"type": QPushButton, "instance": None},
            "staticIPSettingsDoneButton": {"type": QPushButton, "instance": None},
            "wifiSettingsDoneButton": {"type": QPushButton, "instance": None},
            "deleteStaticIPSettingsButton": {"type": QPushButton, "instance": None}
        }
        
        # Keyboard buttons
        self.keyboard_buttons = {
            "staticIPKeyboardButton": {"type": QPushButton, "instance": None},
            "staticIPGatewayKeyboardButton": {"type": QPushButton, "instance": None},
            "staticIPNameServerKeyboardButton": {"type": QPushButton, "instance": None},
            "wifiSettingsSSIDKeyboardButton": {"type": QPushButton, "instance": None}
        }
        
        # UI containers and pages
        self.containers = {
            "stackedWidget": {"type": QStackedWidget, "instance": None},
            "networkSettingsPage": {"type": QWidget, "instance": None},
            "networkInfoPage": {"type": QWidget, "instance": None},
            "staticIPSettingsPage": {"type": QWidget, "instance": None},
            "wifiSettingsPage": {"type": QWidget, "instance": None}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.navigation_buttons)
        self.all_components.update(self.action_buttons)
        self.all_components.update(self.keyboard_buttons)
        self.all_components.update(self.containers)
        
        # Find all components using the dictionary
        self._find_components()

    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_info["instance"] = self.findChild(component_info["type"], name)
            
            # Debug output
            if component_info["instance"]:
                print(f"Found {component_info['type'].__name__} '{name}'")
            else:
                print(f"WARNING: Could not find {component_info['type'].__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create mappings of component categories for reporting
        component_groups = {
            "NetworkSettings - Navigation Buttons": {name: info["instance"] for name, info in self.navigation_buttons.items()},
            "NetworkSettings - Action Buttons": {name: info["instance"] for name, info in self.action_buttons.items()},
            "NetworkSettings - Keyboard Buttons": {name: info["instance"] for name, info in self.keyboard_buttons.items()},
            "NetworkSettings - Containers": {name: info["instance"] for name, info in self.containers.items()}
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)

    def _connect_buttons(self):
        """Connect buttons to their respective functions with safety checks"""
        # Button to handler mapping
        button_mappings = {
            # Navigation buttons
            "networkSettingsBackButton": self.go_back_to_settings_screen,
            "networkInfoBackButton": self.go_back,
            "staticIPSettingsCancelButton": self.cancel_network_settings,
            "wifiSettingsCancelButton": self.cancel_network_settings,
            
            # Action buttons
            "networkInfoButton": self.show_network_info,
            "configureStaticIPButton": self.show_static_ip_settings,
            "configureWifiButton": self.show_wifi_settings,
            "staticIPSettingsDoneButton": self.save_network_settings,
            "wifiSettingsDoneButton": self.save_network_settings
        }
        
        # Connect each button to its handler
        for button_name, handler in button_mappings.items():
            # First check in navigation buttons
            button = None
            
            if button_name in self.navigation_buttons:
                button = self.navigation_buttons[button_name]["instance"]
            elif button_name in self.action_buttons:
                button = self.action_buttons[button_name]["instance"]
            elif button_name in self.keyboard_buttons:
                button = self.keyboard_buttons[button_name]["instance"]
            
            if button:
                button.clicked.connect(handler)
                print(f"Connected {button_name} to handler")
            else:
                print(f"WARNING: Could not connect {button_name} - button not found")

    def _set_default_page(self):
        """Set the default page in stacked widget"""
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance")
        default_page = self.containers.get("networkSettingsPage", {}).get("instance")
        
        if stacked_widget and default_page:
            stacked_widget.setCurrentWidget(default_page)
            print("Set default page to networkSettingsPage")
        else:
            print("WARNING: Could not set default page - required widgets missing")

    def save_network_settings(self):
        """Save network settings and return to main network page."""
        print("Save Network Settings button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        network_page = self.containers.get("networkSettingsPage", {}).get("instance")
        
        if stacked_widget and network_page:
            stacked_widget.setCurrentWidget(network_page)
            print("Returned to network settings page after save")
        else:
            print("ERROR: Cannot navigate - required widgets missing")

    def cancel_network_settings(self):
        """Cancel network settings change and return to main network page."""
        print("Cancel Network Settings button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        network_page = self.containers.get("networkSettingsPage", {}).get("instance")
        
        if stacked_widget and network_page:
            stacked_widget.setCurrentWidget(network_page)
            print("Returned to network settings page after cancel")
        else:
            print("ERROR: Cannot navigate - required widgets missing")

    def go_back_to_settings_screen(self):
        """Return to the main settings screen."""
        print("Back to settings screen button clicked")
        if hasattr(self.mainSettingsWidget, 'stackedWidget') and hasattr(self.mainSettingsWidget, 'mainSettingsPage'):
            self.mainSettingsWidget.stackedWidget.setCurrentWidget(self.mainSettingsWidget.mainSettingsPage)
            print("Navigated back to main settings screen")
        else:
            print("ERROR: Cannot navigate back - required widgets not found in mainSettingsWidget")

    def go_back(self):
        """Return to main network settings page from network info page."""
        print("Back to network settings page button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        network_page = self.containers.get("networkSettingsPage", {}).get("instance")
        
        if stacked_widget and network_page:
            stacked_widget.setCurrentWidget(network_page)
            print("Navigated back to network settings page")
        else:
            print("ERROR: Cannot navigate - required widgets missing")

    def show_network_info(self):
        """Show network information page."""
        print("Network Info button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        info_page = self.containers.get("networkInfoPage", {}).get("instance")
        
        if stacked_widget and info_page:
            stacked_widget.setCurrentWidget(info_page)
            print("Navigated to network info page")
        else:
            print("ERROR: Cannot navigate - required widgets missing")

    def show_static_ip_settings(self):
        """Show static IP configuration page."""
        print("Static IP Settings button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        static_ip_page = self.containers.get("staticIPSettingsPage", {}).get("instance")
        
        if stacked_widget and static_ip_page:
            stacked_widget.setCurrentWidget(static_ip_page)
            print("Navigated to static IP settings page")
        else:
            print("ERROR: Cannot navigate - required widgets missing")

    def show_wifi_settings(self):
        """Show WiFi configuration page."""
        print("WiFi Settings button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        wifi_page = self.containers.get("wifiSettingsPage", {}).get("instance")
        
        if stacked_widget and wifi_page:
            stacked_widget.setCurrentWidget(wifi_page)
            print("Navigated to WiFi settings page")
        else:
            print("ERROR: Cannot navigate - required widgets missing")
