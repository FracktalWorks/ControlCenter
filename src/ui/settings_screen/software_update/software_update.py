from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QListWidget, QTextEdit

class SoftwareUpdate(QWidget):
    def __init__(self, parent, settings_screen):
        super(SoftwareUpdate, self).__init__(parent)
        self.mainSettingsWidget = settings_screen  # Reference to the main settings widget

        # Load the .ui file
        try:
            uic.loadUi('src/ui/settings_screen/software_update/software_update.ui', self)
            print("UI file loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

        # Find buttons by their object names
        self.softwareUpdateBackButton = self.findChild(QPushButton, 'softwareUpdateBackButton')
        self.performUpdateButton = self.findChild(QPushButton, 'performUpdateButton')

        # Find other UI elements
        self.updateListWidget = self.findChild(QListWidget, 'updateListWidget')
        self.logTextEdit = self.findChild(QTextEdit, 'logTextEdit')

        # Find stacked widget and pages
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        self.softwareUpdateProgressPage = self.findChild(QWidget, 'softwareUpdateProgressPage')
        self.OTAUpdatePage = self.findChild(QWidget, 'OTAUpdatePage')

        # Check if all elements are found
        if not all([
            self.softwareUpdateBackButton, self.performUpdateButton, self.updateListWidget,
            self.logTextEdit, self.stackedWidget, self.softwareUpdateProgressPage, self.OTAUpdatePage
        ]):
            raise ValueError("One or more UI elements not found in the UI file")

        # Connect buttons to their respective functions
        self.softwareUpdateBackButton.clicked.connect(self.go_back_to_settings_screen)
        self.performUpdateButton.clicked.connect(self.update_software)

        # Set the default screen to OTAUpdatePage
        self.stackedWidget.setCurrentWidget(self.OTAUpdatePage)

    def go_back_to_settings_screen(self):
        """Return to the settings screen."""
        print("Back to settings screen button clicked")
        self.mainSettingsWidget.stackedWidget.setCurrentWidget(self.mainSettingsWidget.mainSettingsPage)

    def update_software(self):
        """Update the software."""
        print("Updating software.")
        self.stackedWidget.setCurrentWidget(self.softwareUpdateProgressPage)
        self.logTextEdit.append("Software update in progress...")
        # Add logic to perform the software update
