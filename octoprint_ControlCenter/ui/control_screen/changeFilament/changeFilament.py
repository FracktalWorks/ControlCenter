from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QComboBox, QProgressBar, QLabel
from utils.helpers import check_ui_elements
from utils import logger
from utils import dialog
from utils.logger import setup_logger

class ChangeFilament(QWidget):
    def __init__(self, main_window, control_screen, home_screen):
        super(ChangeFilament, self).__init__()
        self.main_window = main_window
        self.control_screen = control_screen
        self.home_screen = home_screen
        
        # Setup logger
        self.logger = setup_logger(f"{self.__class__.__name__}")
        self.logger.info("Initializing ChangeFilament widget")
        
        # Load UI
        try:
            uic.loadUi('octoprint_ControlCenter/ui/control_screen/changeFilament/changeFilament.ui', self)
            self.logger.info("ChangeFilament UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load ChangeFilament UI file: {e}", exc_info=True)
            return
        
        # Initialize UI components
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.changeFilamentPage = self.findChild(QWidget, "changeFilamentPage")
        self.changeFilamentProgressPage = self.findChild(QWidget, "changeFilamentProgressPage")
        self.changeFilamentLoadPage = self.findChild(QWidget, "changeFilamentLoadPage")
        self.changeFilamentExtrudePage = self.findChild(QWidget, "changeFilamentExtrudePage")
        self.changeFilamentRetractPage = self.findChild(QWidget, "changeFilamentRetractPage")
        self.changeFilamentBackButton = self.findChild(QPushButton, "changeFilamentBackButton")
        self.changeFilamentBackButton2 = self.findChild(QPushButton, "changeFilamentBackButton2")
        self.changeFilamentBackButton3 = self.findChild(QPushButton, "changeFilamentBackButton3")
        self.changeFilamentLoadButton = self.findChild(QPushButton, "changeFilamentLoadButton")
        self.changeFilamentUnloadButton = self.findChild(QPushButton, "changeFilamentUnloadButton")
        self.toolToggleChangeFilamentButton = self.findChild(QPushButton, "toolToggleChangeFilamentButton")
        self.loadedTillExtruderButton = self.findChild(QPushButton, "loadedTillExtruderButton")
        self.loadDoneButton = self.findChild(QPushButton, "loadDoneButton")
        self.unloadDoneButton = self.findChild(QPushButton, "unloadDoneButton")
        self.changeFilamentComboBox = self.findChild(QComboBox, "changeFilamentComboBox")
        self.changeFilamentProgress = self.findChild(QProgressBar, "changeFilamentProgress")
        self.changeFilamentStatus = self.findChild(QLabel, "changeFilamentStatus")
        
        # Validate UI components
        components = [
            self.stackedWidget,
            self.changeFilamentPage, self.changeFilamentProgressPage, 
            self.changeFilamentLoadPage, self.changeFilamentExtrudePage, 
            self.changeFilamentRetractPage,
            self.changeFilamentBackButton, self.changeFilamentBackButton2, 
            self.changeFilamentBackButton3,
            self.changeFilamentLoadButton, self.changeFilamentUnloadButton, 
            self.toolToggleChangeFilamentButton, self.loadedTillExtruderButton, 
            self.loadDoneButton, self.unloadDoneButton,
            self.changeFilamentComboBox, self.changeFilamentProgress, 
            self.changeFilamentStatus
        ]
        check_ui_elements(self, components, "ChangeFilament")
        
        # Connect signals to slots
        if self.changeFilamentBackButton:
            self.changeFilamentBackButton.clicked.connect(self.control)
        if self.changeFilamentBackButton2:
            self.changeFilamentBackButton2.clicked.connect(self._handle_back_button)
        if self.changeFilamentBackButton3:
            self.changeFilamentBackButton3.clicked.connect(self._handle_back_button)
        if self.changeFilamentLoadButton:
            self.changeFilamentLoadButton.clicked.connect(self.start_loading_filament)
        if self.changeFilamentUnloadButton:
            self.changeFilamentUnloadButton.clicked.connect(self.start_unloading_filament)
        if self.toolToggleChangeFilamentButton:
            self.toolToggleChangeFilamentButton.clicked.connect(self.toggle_tool)
        if self.loadedTillExtruderButton:
            self.loadedTillExtruderButton.clicked.connect(self.filament_loaded_till_extruder)
        if self.loadDoneButton:
            self.loadDoneButton.clicked.connect(self.finish_loading_filament)
        if self.unloadDoneButton:
            self.unloadDoneButton.clicked.connect(self.finish_unloading_filament)
        
        # Set the default screen
        self._show_page('change_filament_screen')

    def _show_page(self, page_name):
        """Show a specific page in the stacked widget."""
        if not self.stackedWidget:
            self.logger.error("Cannot show page - stacked widget is missing")
            return False
        page = getattr(self, page_name, None)
        if page:
            self.stackedWidget.setCurrentWidget(page)
            self.logger.info(f"Showing page: {page_name}")
            return True
        else:
            self.logger.error(f"Cannot show page {page_name} - page not found")
            return False

    def control(self):
        """
        Sets the current page to the control page
        """
        logger.info("MainUiClass.control started")
        try:
            self.stackedWidget.setCurrentWidget(self.control_screen)
            if self.control_screen.toolToggleTemperatureButton.isChecked():
                self.control_screen.toolTempSpinBox.setProperty(
                    "value", float(self.home_screen.tool1TargetTemperature.text())
                )
            else:
                self.control_screen.toolTempSpinBox.setProperty(
                    "value", float(self.home_screen.tool0TargetTemperature.text())
                )
            self.control_screen.bedTempSpinBox.setProperty(
                "value", float(self.home_screen.bedTargetTemperature.text())
            )
        except Exception as e:
            logger.error("Error in MainUiClass.control: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.control: {}".format(e), overlay=True)

    # def loadFilament(self):
    #     logger.info("MainUiClass.loadFilament started")
    #     try:
    #         if self.printerStatusText not in ["Printing","Paused"]:
    #             if self.activeExtruder == 1:
    #                 octopiclient.jog(tool1PurgePosition['X'],tool1PurgePosition["Y"] ,absolute=True, speed=10000)
    #
    #             else:
    #                 octopiclient.jog(tool0PurgePosition['X'],tool0PurgePosition["Y"] ,absolute=True, speed=10000)
    #
    #         if self.changeFilamentComboBox.findText("Loaded Filament") == -1:
    #             octopiclient.setToolTemperature({"tool1": filaments[str(
    #                 self.changeFilamentComboBox.currentText())]}) if self.activeExtruder == 1 else octopiclient.setToolTemperature(
    #                 {"tool0": filaments[str(self.changeFilamentComboBox.currentText())]})
    #         self.stackedWidget.setCurrentWidget(self.changeFilamentProgressPage)
    #         self.changeFilamentStatus.setText("Heating Tool {}, Please Wait...".format(str(self.activeExtruder)))
    #         self.changeFilamentNameOperation.setText("Loading {}".format(str(self.changeFilamentComboBox.currentText())))
    #         # this flag tells the updateTemperature function that runs every second to update the filament change progress bar as well, and to load or unload after heating done
    #         self.changeFilamentHeatingFlag = True
    #         self.loadFlag = True
    #     except Exception as e:
    #         self.loadFlag = False
    #         self.changeFilamentHeatingFlag = False
    #         logger.error("Error in MainUiClass.loadFilament: {}".format(e))
    #         dialog.WarningOk(self, "Error in MainUiClass.loadFilament: {}".format(e), overlay=True)

    # ! To be commented out later:.............................................................................
    def _update_status(self, message):
        """Update the status label with a message"""
        if self.changeFilamentStatus:
            self.changeFilamentStatus.setText(message)
            self.logger.info(f"Status updated: {message}")
        else:
            self.logger.warning("Could not update status - label not found")

    def _handle_back_button(self):
        """Handle back button logic with proper safety checks"""
        if self.stackedWidget:
            # Reset to first page in this widget's stack
            if self.changeFilamentPage:
                self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
            self.logger.debug("Back button: reset to first page")

        # Return to parent screen directly, bypassing history
        if self.parent_screen:
            self.logger.info("Returning directly to parent control screen")
            # Set current screen directly without modifying history
            self.main_window.current_screen = self.parent_screen
            self.main_window.stacked_widget.setCurrentWidget(self.parent_screen)
        else:
            # Fallback to previous screen if parent_screen not set
            self.logger.warning("parent_screen not set, using switch_to_previous_screen")
            self.main_window.switch_to_previous_screen()
        self.logger.info("Back button: returning to parent screen")

    def start_loading_filament(self):
        """Start the filament loading process"""
        self.logger.info("Starting filament loading process")
        self._show_page('changeFilamentLoadPage')
        self._update_status("Insert filament and wait for automatic pull")

        # Here you would add logic to send commands to the printer
        # e.g., self.main_window.octoprint_client.start_loading_filament()

    def start_unloading_filament(self):
        """Start the filament unloading process"""
        self.logger.info("Starting filament unloading process")
        self._show_page('changeFilamentRetractPage')
        self._update_status("Retracting filament...")

        # Here you would add logic to send commands to the printer
        # e.g., self.main_window.octoprint_client.start_unloading_filament()

    def toggle_tool(self):
        """Toggle between extruder tools (dual extruder support)"""
        tool_button = self.toolToggleChangeFilamentButton
        if tool_button and tool_button.isChecked():
            self.logger.info("Toggling to Tool 1")
            # Add logic for Tool 1
        else:
            self.logger.info("Toggling to Tool 0")
            # Add logic for Tool 0

    def filament_loaded_till_extruder(self):
        """Handle the event when filament is loaded till the extruder"""
        self.logger.info("Filament loaded till extruder")
        self._show_page('changeFilamentExtrudePage')
        self._update_status("Extruding filament...")

        # Here you would add logic to send commands to the printer
        # e.g., self.main_window.octoprint_client.extrude_filament()

    def finish_loading_filament(self):
        """Finish the filament loading process"""
        self.logger.info("Filament loading process finished")
        self._update_status("Filament loaded successfully")

        # Return to parent control screen directly instead of using navigation history
        if self.parent_screen:
            self.logger.info("Returning to parent control screen after loading filament")
            self.main_window.switch_screen(self.parent_screen)
        else:
            self.logger.warning("parent_screen not set, using fallback navigation")
            self.main_window.switch_to_previous_screen()

    def finish_unloading_filament(self):
        """Finish the filament unloading process"""
        self.logger.info("Filament unloading process finished")
        self._update_status("Filament unloaded successfully")

        # Reset to the first page
        self._show_page('changeFilamentPage')

        # Return to parent control screen directly instead of using navigation history
        if self.parent_screen:
            self.logger.info("Returning to parent control screen after unloading filament")
            self.main_window.switch_screen(self.parent_screen)
        else:
            self.logger.warning("parent_screen not set, using fallback navigation")
            self.main_window.switch_to_previous_screen()

    def reset_wizard(self):
        """Reset the Change Filament wizard to its initial state."""
        # Reset to the first page
        self._show_page('changeFilamentPage')

        # Clear the status message
        self._update_status("")

        self.logger.info("Change Filament wizard reset to initial state")