from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QListWidget, QTextEdit
from utils.helpers import check_ui_elements
from utils import dialog
from utils import logger

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
            uic.loadUi('/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/settings_screen/software_update/software_update.ui', self)
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
            self.performUpdateButton.clicked.connect(
                lambda: self.mainSettingsWidget.main_window.octoprint_client.performSoftwareUpdate()
            )
        else:
            print("WARNING: Could not connect update button - button not found")
        
        # Set the default page in stacked widget
        if self.stackedWidget and self.OTAUpdatePage:
            self.stackedWidget.setCurrentWidget(self.OTAUpdatePage)
            print("Set default page to OTAUpdatePage")
        else:
            print("WARNING: Could not set default page - required widgets missing")

        # ! LOCAL SIGNAL AND SLOT CONNECTIONS:
        self.mainSettingsWidget.main_window.octoprint_client.update_started_signal.connect(self.softwareUpdateProgress)
        self.mainSettingsWidget.main_window.octoprint_client.update_log_signal.connect(self.softwareUpdateProgressLog)
        self.mainSettingsWidget.main_window.octoprint_client.update_log_result_signal.connect(self.softwareUpdateResult)
        self.mainSettingsWidget.main_window.octoprint_client.update_failed_signal.connect(self.updateFailed)

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

    def softwareUpdateProgress(self, data):
        logger.info("MainUiClass.softwareUpdateProgress started")
        try:
            self.stackedWidget.setCurrentWidget(self.softwareUpdateProgressPage)
            self.logTextEdit.setTextColor(QtCore.Qt.red)
            self.logTextEdit.append("---------------------------------------------------------------\n"
                                    "Updating " + data["name"] + " to " + data["version"] + "\n"
                                    "---------------------------------------------------------------")
        except Exception as e:
            logger.error("Error in MainUiClass.softwareUpdateProgress: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.softwareUpdateProgress: {}".format(e), overlay=True)

    def softwareUpdateProgressLog(self,data):
        logger.info("MainUiClass.softwareUpdateProgressLog started")
        try:
             self.logTextEdit.setTextColor(QtCore.Qt.white)
             for line in data:
                self.logTextEdit.append(line["line"])
        
        except Exception as e:
            logger.error("Error in MainUiClass.softwareUpdateProgressLog: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.softwareUpdateProgressLog: {}".format(e), overlay=True)

    def updateFailed(self, data):
        logger.info("MainUiClass.updateFailed started")
        try:
            self.stackedWidget.setCurrentWidget(self.settingsPage)
            messageText = (data["name"] + " failed to update\n")
            if dialog.WarningOkCancel(self, messageText, overlay=True):
                pass
        except Exception as e:
            logger.error("Error in MainUiClass.updateFailed: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.updateFailed: {}".format(e), overlay=True)

    def softwareUpdateResult(self, data):
        logger.info("MainUiClass.softwareUpdateResult started")
        try:
            messageText = ""
            for item in data:
                messageText += item + ": " + data[item][0] + ".\n"
            messageText += "Restart required"
            self.askAndReboot(messageText)
        except Exception as e:
            logger.error("Error in MainUiClass.softwareUpdateResult: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.softwareUpdateResult: {}".format(e), overlay=True)

    def displayVersionInfo(self):
        """
        Displays the version information for octoprint plugins
        """
        logger.info("MainUiClass.displayVersionInfo started")
        try:
            self.updateListWidget.clear()
            updateAvailable = False
            self.performUpdateButton.setDisabled(True)

            # Firmware version on the MKS https://github.com/FracktalWorks/OctoPrint-JuliaFirmwareUpdater
            # self.updateListWidget.addItem(self.getFirmwareVersion())

            data = self.mainSettingsWidget.main_window.octoprint_client.getSoftwareUpdateInfo()
            if data:
                for item in data["information"]:
                    # print(item)
                    plugin = data["information"][item]
                    info = u'\u2713' if not plugin["updateAvailable"] else u"\u2717"    # icon
                    info += plugin["displayName"] + "  " + plugin["displayVersion"] + "\n"
                    info += "   Available: "
                    if "information" in plugin and "remote" in plugin["information"] and plugin["information"]["remote"]["value"] is not None:
                        info += plugin["information"]["remote"]["value"]
                    else:
                        info += "Unknown"
                    self.updateListWidget.addItem(info)

                    if plugin["updateAvailable"]:
                        updateAvailable = True

                    # if not updatable:
                    #     self.updateListWidget.addItem(u'\u2713' + data["information"][item]["displayName"] +
                    #                                   "  " + data["information"][item]["displayVersion"] + "\n"
                    #                                   + "   Available: " +
                    #                                   )
                    # else:
                    #     updateAvailable = True
                    #     self.updateListWidget.addItem(u"\u2717" + data["information"][item]["displayName"] +
                    #                                   "  " + data["information"][item]["displayVersion"] + "\n"
                    #                                   + "   Available: " +
                    #                                   data["information"][item]["information"]["remote"]["value"])
            if updateAvailable:
                self.performUpdateButton.setDisabled(False)
            self.stackedWidget.setCurrentWidget(self.OTAUpdatePage)
        except Exception as e:
            logger.error("Error in MainUiClass.displayVersionInfo: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.displayVersionInfo: {}".format(e), overlay=True)