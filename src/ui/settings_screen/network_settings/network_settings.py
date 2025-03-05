from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget

class NetworkSettings(QWidget):
    def __init__(self, parent, settings_screen):
        super(NetworkSettings, self).__init__(parent)
        self.mainSettingsWidget = settings_screen  # Reference to the main settings widget
        uic.loadUi('src/ui/settings_screen/network_settings/network_settings.ui', self)

        # Find buttons by their object names
        self.staticIPSettingsCancelButton = self.findChild(QPushButton, 'staticIPSettingsCancelButton')
        self.staticIPGatewayKeyboardButton = self.findChild(QPushButton, 'staticIPGatewayKeyboardButton')
        self.staticIPKeyboardButton = self.findChild(QPushButton, 'staticIPKeyboardButton')
        self.staticIPNameServerKeyboardButton = self.findChild(QPushButton, 'staticIPNameServerKeyboardButton')
        self.deleteStaticIPSettingsButton = self.findChild(QPushButton, 'deleteStaticIPSettingsButton')
        self.staticIPSettingsDoneButton = self.findChild(QPushButton, 'staticIPSettingsDoneButton')
        self.wifiSettingsCancelButton = self.findChild(QPushButton, 'wifiSettingsCancelButton')
        self.wifiSettingsDoneButton = self.findChild(QPushButton, 'wifiSettingsDoneButton')
        self.wifiSettingsSSIDKeyboardButton = self.findChild(QPushButton, 'wifiSettingsSSIDKeyboardButton')
        self.networkInfoButton = self.findChild(QPushButton, 'networkInfoButton')
        self.configureStaticIPButton = self.findChild(QPushButton, 'configureStaticIPButton')
        self.networkSettingsBackButton = self.findChild(QPushButton, 'networkSettingsBackButton')
        self.configureWifiButton = self.findChild(QPushButton, 'configureWifiButton')
        self.networkInfoBackButton = self.findChild(QPushButton, 'networkInfoBackButton')

        # Find pages by their object names
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        self.networkSettingsPage = self.findChild(QWidget, 'networkSettingsPage')
        self.staticIPSettingsPage = self.findChild(QWidget, 'staticIPSettingsPage')
        self.wifiSettingsPage = self.findChild(QWidget, 'wifiSettingsPage')
        self.networkInfoPage = self.findChild(QWidget, 'networkInfoPage')

        # Check if buttons and pages are found
        if not all([self.staticIPSettingsCancelButton, self.staticIPGatewayKeyboardButton, self.staticIPKeyboardButton, self.staticIPNameServerKeyboardButton, self.deleteStaticIPSettingsButton, self.staticIPSettingsDoneButton, self.wifiSettingsCancelButton, self.wifiSettingsDoneButton, self.wifiSettingsSSIDKeyboardButton, self.networkInfoButton, self.configureStaticIPButton, self.networkSettingsBackButton, self.configureWifiButton, self.networkInfoBackButton, self.stackedWidget, self.networkSettingsPage, self.staticIPSettingsPage, self.wifiSettingsPage, self.networkInfoPage]):
            raise ValueError("One or more buttons or pages not found in the UI file")

        # Connect buttons to their respective functions
        self.staticIPSettingsCancelButton.clicked.connect(self.cancel_network_settings)
        self.staticIPSettingsDoneButton.clicked.connect(self.save_network_settings)
        self.wifiSettingsCancelButton.clicked.connect(self.cancel_network_settings)
        self.wifiSettingsDoneButton.clicked.connect(self.save_network_settings)
        self.networkSettingsBackButton.clicked.connect(self.go_back_to_settings_screen)
        self.networkInfoBackButton.clicked.connect(self.go_back)
        self.networkInfoButton.clicked.connect(self.show_network_info)
        self.configureStaticIPButton.clicked.connect(self.show_static_ip_settings)
        self.configureWifiButton.clicked.connect(self.show_wifi_settings)

        # Set the default screen to networkSettingsPage
        self.stackedWidget.setCurrentWidget(self.networkSettingsPage)

    def save_network_settings(self):
        # Placeholder for save network settings logic
        print("Save Network Settings button clicked")

    def cancel_network_settings(self):
        # Placeholder for cancel network settings logic
        print("Cancel Network Settings button clicked")
        self.stackedWidget.setCurrentWidget(self.networkSettingsPage)

    def go_back_to_settings_screen(self):
        # Logic to go back to the settings screen
        print("Back to settings screen button clicked")
        self.mainSettingsWidget.stackedWidget.setCurrentWidget(self.mainSettingsWidget.mainSettingsPage)

    def go_back(self):
        # Logic to go back to the network settings page
        print("Back to network settings page button clicked")
        self.stackedWidget.setCurrentWidget(self.networkSettingsPage)

    def show_network_info(self):
        # Logic to switch to the networkInfoPage
        print("Network Info button clicked")
        self.stackedWidget.setCurrentWidget(self.networkInfoPage)

    def show_static_ip_settings(self):
        # Logic to switch to the staticIPSettingsPage
        print("Static IP Settings button clicked")
        self.stackedWidget.setCurrentWidget(self.staticIPSettingsPage)

    def show_wifi_settings(self):
        # Logic to switch to the wifiSettingsPage
        print("WiFi Settings button clicked")
        self.stackedWidget.setCurrentWidget(self.wifiSettingsPage)
