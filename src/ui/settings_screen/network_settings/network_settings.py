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
        try:
            uic.loadUi('src/ui/settings_screen/network_settings/network_settings.ui', self)
            logger.info("NetworkSettings UI loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load NetworkSettings UI file: {e}")
        
        # Initialize UI components
        # Navigation buttons
        self.networkSettingsBackButton = self.findChild(QPushButton, "networkSettingsBackButton")
        self.networkInfoBackButton = self.findChild(QPushButton, "networkInfoBackButton")
        self.staticIPSettingsCancelButton = self.findChild(QPushButton, "staticIPSettingsCancelButton")
        self.wifiSettingsCancelButton = self.findChild(QPushButton, "wifiSettingsCancelButton")
        
        # Action buttons
        self.networkInfoButton = self.findChild(QPushButton, "networkInfoButton")
        self.configureStaticIPButton = self.findChild(QPushButton, "configureStaticIPButton")
        self.configureWifiButton = self.findChild(QPushButton, "configureWifiButton")
        self.staticIPSettingsDoneButton = self.findChild(QPushButton, "staticIPSettingsDoneButton")
        self.wifiSettingsDoneButton = self.findChild(QPushButton, "wifiSettingsDoneButton")
        self.deleteStaticIPSettingsButton = self.findChild(QPushButton, "deleteStaticIPSettingsButton")
        
        # Keyboard buttons
        self.staticIPKeyboardButton = self.findChild(QPushButton, "staticIPKeyboardButton")
        self.staticIPGatewayKeyboardButton = self.findChild(QPushButton, "staticIPGatewayKeyboardButton")
        self.staticIPNameServerKeyboardButton = self.findChild(QPushButton, "staticIPNameServerKeyboardButton")
        self.wifiSettingsSSIDKeyboardButton = self.findChild(QPushButton, "wifiSettingsSSIDKeyboardButton")
        
        # UI containers and pages
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.networkSettingsPage = self.findChild(QWidget, "networkSettingsPage")
        self.networkInfoPage = self.findChild(QWidget, "networkInfoPage")
        self.staticIPSettingsPage = self.findChild(QWidget, "staticIPSettingsPage")
        self.wifiSettingsPage = self.findChild(QWidget, "wifiSettingsPage")
        
        # Validate UI components using simplified check_ui_elements
        # Convert all UI components into a single list for validation
        ui_components = [
            self.networkSettingsBackButton, self.networkInfoBackButton,
            self.staticIPSettingsCancelButton, self.wifiSettingsCancelButton,
            self.networkInfoButton, self.configureStaticIPButton,
            self.configureWifiButton, self.staticIPSettingsDoneButton,
            self.wifiSettingsDoneButton, self.deleteStaticIPSettingsButton,
            self.staticIPKeyboardButton, self.staticIPGatewayKeyboardButton,
            self.staticIPNameServerKeyboardButton, self.wifiSettingsSSIDKeyboardButton,
            self.stackedWidget, self.networkSettingsPage, self.networkInfoPage,
            self.staticIPSettingsPage, self.wifiSettingsPage
        ]
        
        # Validate all components at once
        check_ui_elements(self, ui_components, "NetworkSettings UI Components")
        
        # Create ClickableLineEdit components
        # Fonts and styles
        font = QtGui.QFont()
        font.setFamily("Gotham")
        font.setPointSize(15)

        # WiFi Password Line Edit
        self.wifiPasswordLineEdit = ClickableLineEdit(self.wifiSettingsPage)
        self.wifiPasswordLineEdit.setGeometry(QtCore.QRect(300, 170, 400, 60))
        self.wifiPasswordLineEdit.setFont(font)
        self.wifiPasswordLineEdit.setStyleSheet(styles.textedit)
        self.wifiPasswordLineEdit.setObjectName("wifiPasswordLineEdit")

        # Static IP Line Edits
        font.setPointSize(11)
        self.staticIPLineEdit = ClickableLineEdit(self.staticIPSettingsPage)
        self.staticIPLineEdit.setGeometry(QtCore.QRect(200, 15, 450, 40))
        self.staticIPLineEdit.setFont(font)
        self.staticIPLineEdit.setStyleSheet(styles.textedit)
        self.staticIPLineEdit.setObjectName("staticIPLineEdit")

        self.staticIPGatewayLineEdit = ClickableLineEdit(self.staticIPSettingsPage)
        self.staticIPGatewayLineEdit.setGeometry(QtCore.QRect(200, 85, 450, 40))
        self.staticIPGatewayLineEdit.setFont(font)
        self.staticIPGatewayLineEdit.setStyleSheet(styles.textedit)
        self.staticIPGatewayLineEdit.setObjectName("staticIPGatewayLineEdit")

        self.staticIPNameServerLineEdit = ClickableLineEdit(self.staticIPSettingsPage)
        self.staticIPNameServerLineEdit.setGeometry(QtCore.QRect(200, 155, 450, 40))
        self.staticIPNameServerLineEdit.setFont(font)
        self.staticIPNameServerLineEdit.setStyleSheet(styles.textedit)
        self.staticIPNameServerLineEdit.setObjectName("staticIPNameServerLineEdit")
        
        # Connect buttons to their respective functions
        # Navigation buttons
        if self.networkSettingsBackButton:
            self.networkSettingsBackButton.clicked.connect(self.go_back_to_settings_screen)
        
        if self.networkInfoBackButton:
            self.networkInfoBackButton.clicked.connect(self.go_back)
        
        if self.staticIPSettingsCancelButton:
            self.staticIPSettingsCancelButton.clicked.connect(self.cancel_network_settings)
        
        if self.wifiSettingsCancelButton:
            self.wifiSettingsCancelButton.clicked.connect(self.cancel_network_settings)
        
        # Action buttons
        if self.networkInfoButton:
            self.networkInfoButton.clicked.connect(self.show_network_info)
        
        if self.configureStaticIPButton:
            self.configureStaticIPButton.clicked.connect(self.show_static_ip_settings)
        
        if self.configureWifiButton:
            self.configureWifiButton.clicked.connect(self.show_wifi_settings)
        
        if self.staticIPSettingsDoneButton:
            self.staticIPSettingsDoneButton.clicked.connect(self.save_network_settings)
        
        if self.wifiSettingsDoneButton:
            self.wifiSettingsDoneButton.clicked.connect(self.save_network_settings)
        
        # Set the default page in stacked widget
        if self.stackedWidget and self.networkSettingsPage:
            self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
            logger.info("Set default page to networkSettingsPage")
        else:
            logger.warning("Could not set default page - required widgets missing")

    def save_network_settings(self):
        """Save network settings and return to main network page."""
        logger.info("Save Network Settings button clicked")
        if self.stackedWidget and self.networkSettingsPage:
            self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
            logger.info("Returned to network settings page after save")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def cancel_network_settings(self):
        """Cancel network settings change and return to main network page."""
        logger.info("Cancel Network Settings button clicked")
        if self.stackedWidget and self.networkSettingsPage:
            self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
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
        if self.stackedWidget and self.networkSettingsPage:
            self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
            logger.info("Navigated back to network settings page")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def show_network_info(self):
        """Show network information page."""
        logger.info("Network Info button clicked")
        if self.stackedWidget and self.networkInfoPage:
            self.stackedWidget.setCurrentWidget(self.networkInfoPage)
            logger.info("Navigated to network info page")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def show_static_ip_settings(self):
        """Show static IP configuration page."""
        logger.info("Static IP Settings button clicked")
        if self.stackedWidget and self.staticIPSettingsPage:
            self.stackedWidget.setCurrentWidget(self.staticIPSettingsPage)
            logger.info("Navigated to static IP settings page")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def show_wifi_settings(self):
        """Show WiFi configuration page."""
        logger.info("WiFi Settings button clicked")
        if self.stackedWidget and self.wifiSettingsPage:
            self.stackedWidget.setCurrentWidget(self.wifiSettingsPage)
            logger.info("Navigated to WiFi settings page")
        else:
            logger.error("Cannot navigate - required widgets missing")
