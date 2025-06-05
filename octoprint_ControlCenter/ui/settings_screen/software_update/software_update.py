from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QListWidget, QTextEdit
from utils.helpers import check_ui_elements

class SoftwareUpdate(QWidget):
    """
    Software Update widget that allows users to check for and perform
    software updates on the printer's firmware and system.
    """
    def __init__(self, parent, settings_screen):
        super(SoftwareUpdate, self).__init__(parent)
        self.mainSettingsWidget = settings_screen  # Reference to the main settings widget
        
        # Load the UI
        try:
            uic.loadUi('octoprint_ControlCenter/ui/settings_screen/software_update/software_update.ui', self)
            print("SoftwareUpdate UI loaded successfully")
        except Exception as e:
            print(f"Failed to load SoftwareUpdate UI file: {e}")
        
        # Initialize UI components
        # Navigation buttons
        self.softwareUpdateBackButton = self.findChild(QPushButton, "softwareUpdateBackButton")
        
        # Action buttons
        self.performUpdateButton = self.findChild(QPushButton, "performUpdateButton")
        
        # UI containers and pages
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.OTAUpdatePage = self.findChild(QWidget, "OTAUpdatePage")
        self.softwareUpdateProgressPage = self.findChild(QWidget, "softwareUpdateProgressPage")
        
        # UI content elements
        self.updateListWidget = self.findChild(QListWidget, "updateListWidget")
        self.logTextEdit = self.findChild(QTextEdit, "logTextEdit")
        
        # Check if UI elements exist and report missing ones
        # Use a simple list of UI elements instead of a dictionary
        check_ui_elements(self, [
            self.softwareUpdateBackButton,
            self.performUpdateButton,
            self.stackedWidget,
            self.OTAUpdatePage,
            self.softwareUpdateProgressPage,
            self.updateListWidget,
            self.logTextEdit
        ], "SoftwareUpdate")
        
        # Connect buttons to their respective functions with safety checks
        if self.softwareUpdateBackButton:
            self.softwareUpdateBackButton.clicked.connect(self.go_back_to_settings_screen)
            print("Connected back button to go_back_to_settings_screen")
        else:
            print("WARNING: Could not connect back button - button not found")
            
        if self.performUpdateButton:
            self.performUpdateButton.clicked.connect(self.update_software)
            print("Connected update button to update_software")
        else:
            print("WARNING: Could not connect update button - button not found")
        
        # Set the default page in stacked widget
        if self.stackedWidget and self.OTAUpdatePage:
            self.stackedWidget.setCurrentWidget(self.OTAUpdatePage)
            print("Set default page to OTAUpdatePage")
        else:
            print("WARNING: Could not set default page - required widgets missing")

    def go_back_to_settings_screen(self):
        """Return to the settings screen."""
        print("Back to settings screen button clicked")
        if hasattr(self.mainSettingsWidget, 'stackedWidget') and hasattr(self.mainSettingsWidget, 'mainSettingsPage'):
            self.mainSettingsWidget.stackedWidget.setCurrentWidget(self.mainSettingsWidget.mainSettingsPage)
            print("Navigated back to settings screen")
        else:
            print("ERROR: Cannot navigate back - required widgets not found in mainSettingsWidget")

    def update_software(self):
        """Update the software."""
        print("Updating software...")
        
        if self.stackedWidget and self.softwareUpdateProgressPage:
            self.stackedWidget.setCurrentWidget(self.softwareUpdateProgressPage)
            print("Switched to software update progress page")
            
            if self.logTextEdit:
                self.logTextEdit.append("Software update in progress...")
                print("Added log message to text edit")
            else:
                print("WARNING: Could not add log message - logTextEdit not found")
        else:
            print("ERROR: Cannot update software - required widgets missing")
            
        # Actual implementation would include code to:
        # 1. Check for network connectivity
        # 2. Download updates
        # 3. Verify downloaded packages
        # 4. Apply updates
        # 5. Restart system if necessary
