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
        if not self.softwareUpdateBackButton:
            print("softwareUpdateBackButton not found")
        else:
            print("softwareUpdateBackButton found")
            
        self.performUpdateButton = self.findChild(QPushButton, 'performUpdateButton')
        if not self.performUpdateButton:
            print("performUpdateButton not found")
        else:
            print("performUpdateButton found")

        # Find other UI elements
            
        self.logTextEdit = self.findChild(QTextEdit, 'logTextEdit')
        if not self.logTextEdit:
            print("logTextEdit not found")
        else:
            print("logTextEdit found")

        # Find stacked widget and pages
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        if not self.stackedWidget:
            print("stackedWidget not found")
        else:
            print("stackedWidget found")
            
        self.softwareUpdateProgressPage = self.findChild(QWidget, 'softwareUpdateProgressPage')
        if not self.softwareUpdateProgressPage:
            print("softwareUpdateProgressPage not found")
        else:
            print("softwareUpdateProgressPage found")
            
        self.OTAUpdatePage = self.findChild(QWidget, 'OTAUpdatePage')
        if not self.OTAUpdatePage:
            print("OTAUpdatePage not found") 
        else:
            print("OTAUpdatePage found")
    
        self.updateListWidget = self.findChild(QListWidget, 'updateListWidget') 
        if not self.updateListWidget:
            print("updateListWidget not found")
        else:
            print("updateListWidget found")

        # Check each element individually to identify which ones are missing
        missing_elements = []
        if not self.softwareUpdateBackButton:
            missing_elements.append("softwareUpdateBackButton")
        if not self.performUpdateButton:
            missing_elements.append("performUpdateButton")
        if not self.updateListWidget:
            missing_elements.append("updateListWidget")
        if not self.logTextEdit:
            missing_elements.append("logTextEdit")
        if not self.stackedWidget:
            missing_elements.append("stackedWidget")
        if not self.softwareUpdateProgressPage:
            missing_elements.append("softwareUpdateProgressPage")
        if not self.OTAUpdatePage:
            missing_elements.append("OTAUpdatePage")
        
        # # If there are missing elements, raise an error with the list of missing elements
        # if missing_elements:
        #     raise ValueError(f"Missing UI elements: {', '.join(missing_elements)}")

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
