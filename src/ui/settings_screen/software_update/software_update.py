from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton

class SoftwareUpdate(QWidget):
    def __init__(self, parent, settings_screen):
        super(SoftwareUpdate, self).__init__(parent)
        self.mainSettingsWidget = settings_screen  # Reference to the main settings widget
        uic.loadUi('src/ui/settings_screen/software_update/software_update.ui', self)

        # Find buttons by their object names
        self.softwareUpdateBackButton = self.findChild(QPushButton, 'softwareUpdateBackButton')
        self.performUpdateButton = self.findChild(QPushButton, 'performUpdateButton')

        # Check if buttons are found
        if not all([self.softwareUpdateBackButton, self.performUpdateButton]):
            raise ValueError("One or more buttons not found in the UI file")

        # Connect buttons to their respective functions
        self.softwareUpdateBackButton.clicked.connect(self.go_back_to_settings_screen)
        self.performUpdateButton.clicked.connect(self.update_software)

    def go_back_to_settings_screen(self):
        """
        Return to the settings screen.
        """
        print("Back to settings screen button clicked")
        self.mainSettingsWidget.stackedWidget.setCurrentWidget(self.mainSettingsWidget.mainSettingsPage)

    def update_software(self):
        """
        Update the software.
        """
        print("Updating software.")
        # Add logic to update software
