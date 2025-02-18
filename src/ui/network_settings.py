from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton

class NetworkSettings(QWidget):
    def __init__(self):
        super(NetworkSettings, self).__init__()
        uic.loadUi('src/ui/ui_files/network_settings.ui', self)

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

        # Debug prints to check if buttons are found
        print(f"staticIPSettingsCancelButton: {self.staticIPSettingsCancelButton}")
        print(f"staticIPGatewayKeyboardButton: {self.staticIPGatewayKeyboardButton}")
        print(f"staticIPKeyboardButton: {self.staticIPKeyboardButton}")
        print(f"staticIPNameServerKeyboardButton: {self.staticIPNameServerKeyboardButton}")
        print(f"deleteStaticIPSettingsButton: {self.deleteStaticIPSettingsButton}")
        print(f"staticIPSettingsDoneButton: {self.staticIPSettingsDoneButton}")
        print(f"wifiSettingsCancelButton: {self.wifiSettingsCancelButton}")
        print(f"wifiSettingsDoneButton: {self.wifiSettingsDoneButton}")
        print(f"wifiSettingsSSIDKeyboardButton: {self.wifiSettingsSSIDKeyboardButton}")
        print(f"networkInfoButton: {self.networkInfoButton}")
        print(f"configureStaticIPButton: {self.configureStaticIPButton}")
        print(f"networkSettingsBackButton: {self.networkSettingsBackButton}")
        print(f"configureWifiButton: {self.configureWifiButton}")
        print(f"networkInfoBackButton: {self.networkInfoBackButton}")

        # Check if buttons are found
        if not all([self.staticIPSettingsCancelButton, self.staticIPGatewayKeyboardButton, self.staticIPKeyboardButton, self.staticIPNameServerKeyboardButton, self.deleteStaticIPSettingsButton, self.staticIPSettingsDoneButton, self.wifiSettingsCancelButton, self.wifiSettingsDoneButton, self.wifiSettingsSSIDKeyboardButton, self.networkInfoButton, self.configureStaticIPButton, self.networkSettingsBackButton, self.configureWifiButton, self.networkInfoBackButton]):
            raise ValueError("One or more buttons not found in the UI file")

        # Connect buttons to their respective functions
        self.staticIPSettingsCancelButton.clicked.connect(self.cancel_network_settings)
        self.staticIPSettingsDoneButton.clicked.connect(self.save_network_settings)
        self.wifiSettingsCancelButton.clicked.connect(self.cancel_network_settings)
        self.wifiSettingsDoneButton.clicked.connect(self.save_network_settings)
        self.networkSettingsBackButton.clicked.connect(self.go_back)
        self.networkInfoBackButton.clicked.connect(self.go_back)

    def save_network_settings(self):
        # Placeholder for save network settings logic
        print("Save Network Settings button clicked")

    def cancel_network_settings(self):
        # Placeholder for cancel network settings logic
        print("Cancel Network Settings button clicked")

    def go_back(self):
        # Placeholder for go back logic
        print("Back button clicked")