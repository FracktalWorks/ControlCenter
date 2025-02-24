from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from ui.settings_screen.network_settings.network_settings import NetworkSettings

class SettingsScreen(QWidget):
    def __init__(self, main_window):
        super(SettingsScreen, self).__init__()
        self.main_window = main_window
        uic.loadUi('src/ui/settings_screen/settings_screen.ui', self)

        # Find buttons by their object names
        self.settingsBackButton = self.findChild(QPushButton, 'settingsBackButton')
        self.pairPhoneButton = self.findChild(QPushButton, 'pairPhoneButton')
        self.networkSettingsButton = self.findChild(QPushButton, 'networkSettingsButton')
        self.displaySettingsButton = self.findChild(QPushButton, 'displaySettingsButton')
        self.OTAButton = self.findChild(QPushButton, 'OTAButton')
        self.versionButton = self.findChild(QPushButton, 'versionButton')
        self.restorePrintSettingsButton = self.findChild(QPushButton, 'restorePrintSettingsButton')
        self.restoreFactoryDefaultsButton = self.findChild(QPushButton, 'restoreFactoryDefaultsButton')
        self.restartButton = self.findChild(QPushButton, 'restartButton')

        # Find the stacked widget
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')

        # Load the NetworkSettings widget and add it to the stacked widget
        self.network_settings = NetworkSettings(self)
        self.stackedWidget.addWidget(self.network_settings)

        # Debug prints to check if buttons are found
        print(f"settingsBackButton: {self.settingsBackButton}")
        print(f"pairPhoneButton: {self.pairPhoneButton}")
        print(f"networkSettingsButton: {self.networkSettingsButton}")
        print(f"displaySettingsButton: {self.displaySettingsButton}")
        print(f"OTAButton: {self.OTAButton}")
        print(f"versionButton: {self.versionButton}")
        print(f"restorePrintSettingsButton: {self.restorePrintSettingsButton}")
        print(f"restoreFactoryDefaultsButton: {self.restoreFactoryDefaultsButton}")
        print(f"restartButton: {self.restartButton}")

        # Check if buttons are found
        if not all([self.settingsBackButton, self.pairPhoneButton, self.networkSettingsButton, self.displaySettingsButton, self.OTAButton, self.versionButton, self.restorePrintSettingsButton, self.restoreFactoryDefaultsButton, self.restartButton]):
            raise ValueError("One or more buttons not found in the UI file")

        # Connect buttons to their respective functions
        self.settingsBackButton.clicked.connect(self.go_back)
        self.pairPhoneButton.clicked.connect(self.pair_phone)
        self.networkSettingsButton.clicked.connect(self.open_network_settings)
        self.displaySettingsButton.clicked.connect(self.open_display_settings)
        self.OTAButton.clicked.connect(self.check_for_updates)
        self.versionButton.clicked.connect(self.show_version)
        self.restorePrintSettingsButton.clicked.connect(self.restore_print_settings)
        self.restoreFactoryDefaultsButton.clicked.connect(self.restore_factory_defaults)
        self.restartButton.clicked.connect(self.restart)

    def go_back(self):
        # Placeholder for go back logic
        self.main_window.switch_screen(self.main_window.menu_screen)

    def pair_phone(self):
        # Placeholder for pair phone logic
        print("Pair Phone button clicked")

    def open_network_settings(self):
        # Logic to open the network settings screen within the settings screen
        print("Network Settings button clicked")
        self.stackedWidget.setCurrentWidget(self.network_settings)

    def open_display_settings(self):
        # Placeholder for open display settings logic
        print("Display Settings button clicked")

    def check_for_updates(self):
        # Placeholder for check for updates logic
        print("Check for Updates button clicked")

    def show_version(self):
        # Placeholder for show version logic
        print("Version button clicked")

    def restore_print_settings(self):
        # Placeholder for restore print settings logic
        print("Restore Print Settings button clicked")

    def restore_factory_defaults(self):
        # Placeholder for restore factory defaults logic
        print("Restore Factory Defaults button clicked")

    def restart(self):
        # Placeholder for restart logic
        print("Restart button clicked")