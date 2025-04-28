from PyQt5 import QtGui, QtCore
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.custom_widgets import ClickableLineEdit
from utils.helpers import check_ui_elements
from utils.logger import setup_logger
from utils import styles  # Import styles module

# Initialize logger for NetworkSettings
logger = setup_logger('network_settings')

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
            logger.info("NetworkSettings UI loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load NetworkSettings UI file: {e}")

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

        # Fonts and styles
        font = QtGui.QFont()
        font.setFamily("Gotham")
        font.setPointSize(15)

        # WiFi Password Line Edit
        self.wifiPasswordLineEdit = ClickableLineEdit(self.containers["wifiSettingsPage"]["instance"])
        self.wifiPasswordLineEdit.setGeometry(QtCore.QRect(300, 170, 400, 60))
        self.wifiPasswordLineEdit.setFont(font)
        self.wifiPasswordLineEdit.setStyleSheet(styles.textedit)
        self.wifiPasswordLineEdit.setObjectName("wifiPasswordLineEdit")

        # Static IP Line Edits
        font.setPointSize(11)
        self.staticIPLineEdit = ClickableLineEdit(self.containers["staticIPSettingsPage"]["instance"])
        self.staticIPLineEdit.setGeometry(QtCore.QRect(200, 15, 450, 40))
        self.staticIPLineEdit.setFont(font)
        self.staticIPLineEdit.setStyleSheet(styles.textedit)
        self.staticIPLineEdit.setObjectName("staticIPLineEdit")

        self.staticIPGatewayLineEdit = ClickableLineEdit(self.containers["staticIPSettingsPage"]["instance"])
        self.staticIPGatewayLineEdit.setGeometry(QtCore.QRect(200, 85, 450, 40))
        self.staticIPGatewayLineEdit.setFont(font)
        self.staticIPGatewayLineEdit.setStyleSheet(styles.textedit)
        self.staticIPGatewayLineEdit.setObjectName("staticIPGatewayLineEdit")

        self.staticIPNameServerLineEdit = ClickableLineEdit(self.containers["staticIPSettingsPage"]["instance"])
        self.staticIPNameServerLineEdit.setGeometry(QtCore.QRect(200, 155, 450, 40))
        self.staticIPNameServerLineEdit.setFont(font)
        self.staticIPNameServerLineEdit.setStyleSheet(styles.textedit)
        self.staticIPNameServerLineEdit.setObjectName("staticIPNameServerLineEdit")

    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_info["instance"] = self.findChild(component_info["type"], name)
            
            # Debug output
            if component_info["instance"]:
                logger.debug(f"Found {component_info['type'].__name__} '{name}'")
            else:
                logger.warning(f"Could not find {component_info['type'].__name__} '{name}' in UI")

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
                logger.debug(f"Connected {button_name} to handler")
            else:
                logger.warning(f"Could not connect {button_name} - button not found")

    def _set_default_page(self):
        """Set the default page in stacked widget"""
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance")
        default_page = self.containers.get("networkSettingsPage", {}).get("instance")
        
        if stacked_widget and default_page:
            stacked_widget.setCurrentWidget(default_page)
            logger.info("Set default page to networkSettingsPage")
        else:
            logger.warning("Could not set default page - required widgets missing")

    def save_network_settings(self):
        """Save network settings and return to main network page."""
        logger.info("Save Network Settings button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        network_page = self.containers.get("networkSettingsPage", {}).get("instance")
        
        if stacked_widget and network_page:
            stacked_widget.setCurrentWidget(network_page)
            logger.info("Returned to network settings page after save")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def cancel_network_settings(self):
        """Cancel network settings change and return to main network page."""
        logger.info("Cancel Network Settings button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        network_page = self.containers.get("networkSettingsPage", {}).get("instance")
        
        if stacked_widget and network_page:
            stacked_widget.setCurrentWidget(network_page)
            logger.info("Returned to network settings page after cancel")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def go_back_to_settings_screen(self):
        """Return to the main settings screen."""
        logger.info("Back to settings screen button clicked")
        if hasattr(self.mainSettingsWidget, 'stackedWidget') and hasattr(self.mainSettingsWidget, 'mainSettingsPage'):
            self.mainSettingsWidget.stackedWidget.setCurrentWidget(self.mainSettingsWidget.mainSettingsPage)
            logger.info("Navigated back to main settings screen")
        else:
            logger.error("Cannot navigate back - required widgets not found in mainSettingsWidget")

    def go_back(self):
        """Return to main network settings page from network info page."""
        logger.info("Back to network settings page button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        network_page = self.containers.get("networkSettingsPage", {}).get("instance")
        
        if stacked_widget and network_page:
            stacked_widget.setCurrentWidget(network_page)
            logger.info("Navigated back to network settings page")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def show_network_info(self):
        """Show network information page."""
        logger.info("Network Info button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        info_page = self.containers.get("networkInfoPage", {}).get("instance")
        
        if stacked_widget and info_page:
            stacked_widget.setCurrentWidget(info_page)
            logger.info("Navigated to network info page")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def show_static_ip_settings(self):
        """Show static IP configuration page."""
        logger.info("Static IP Settings button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        static_ip_page = self.containers.get("staticIPSettingsPage", {}).get("instance")
        
        if stacked_widget and static_ip_page:
            stacked_widget.setCurrentWidget(static_ip_page)
            logger.info("Navigated to static IP settings page")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def show_wifi_settings(self):
        """Show WiFi configuration page."""
        logger.info("WiFi Settings button clicked")
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance") 
        wifi_page = self.containers.get("wifiSettingsPage", {}).get("instance")
        
        if stacked_widget and wifi_page:
            stacked_widget.setCurrentWidget(wifi_page)
            logger.info("Navigated to WiFi settings page")
        else:
            logger.error("Cannot navigate - required widgets missing")
