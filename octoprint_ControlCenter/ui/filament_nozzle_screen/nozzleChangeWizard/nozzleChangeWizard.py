import os
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel
from PyQt5 import uic
from utils.helpers import check_ui_elements
from utils.logger import get_logger

logger = get_logger(__name__)

class NozzleChangeWizard(QWidget):
    def __init__(self, main_window):
        super(NozzleChangeWizard, self).__init__()
        self.main_window = main_window
        self.octoprint_client = main_window.octoprint_client
        self.logger = get_logger(self.__class__.__name__)
        
        # Wizard state
        self.current_tool = None
        self.wizard_step = 0
        
        # Load the UI
        try:
            ui_file_path = os.path.join(os.path.dirname(__file__), "nozzleChangeWizard.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("NozzleChangeWizard UI loaded successfully")
        except Exception as e:
            self.logger.exception(f"Failed to load NozzleChangeWizard UI file: {e}")

        # Initialize UI components
        self.nozzle_change_stacked_widget = self.findChild(QStackedWidget, "nozzleChangeStackedWidget")
        self.step1_page = self.findChild(QWidget, "step1Page")
        
        self.instruction_label = self.findChild(QLabel, "instructionLabel")
        self.detail_label = self.findChild(QLabel, "detailLabel")
        self.cancel_button = self.findChild(QPushButton, "cancelButton")
        self.next_button = self.findChild(QPushButton, "nextButton")

        # Validate UI components
        check_ui_elements(self, [
            self.nozzle_change_stacked_widget, self.step1_page,
            self.instruction_label, self.detail_label,
            self.cancel_button, self.next_button
        ], "NozzleChangeWizard")

        # Connect buttons
        self.cancel_button.clicked.connect(self.cancel_wizard)
        self.next_button.clicked.connect(self.next_step)

    def setup(self, params):
        """Setup the wizard with specific tool parameters"""
        try:
            self.current_tool = params.get("tool", "tool0")
            self.wizard_step = 0
            
            self.logger.info(f"Setting up nozzle change wizard for {self.current_tool}")
            
            # Update UI for the specific tool
            self.instruction_label.setText(f"Nozzle Change - {self.current_tool.upper()}")
            self.detail_label.setText(f"This wizard will guide you through changing the nozzle for {self.current_tool.upper()}.\nPlease ensure the printer is ready and the hotend is cool before proceeding.")
            
            # Reset to first step
            self.nozzle_change_stacked_widget.setCurrentWidget(self.step1_page)
            
        except Exception as e:
            self.logger.error(f"Error setting up nozzle change wizard: {e}")

    def cancel_wizard(self):
        """Cancel the wizard and return to main screen"""
        self.logger.info("Nozzle change wizard cancelled")
        try:
            # Get parent screen (ChangeFilamentNozzleScreen)
            self.main_window.filament_nozzle_screen.material_nozzle_stacked_widget.setCurrentWidget(
                self.main_window.filament_nozzle_screen.main_material_nozzle_page
            )  # Go back to main material/nozzle page       
        except Exception as e:
            self.logger.error(f"Error cancelling wizard: {e}")

    def next_step(self):
        """Proceed to the next step in the wizard"""
        try:
            self.wizard_step += 1
            self.logger.info(f"Advancing to wizard step {self.wizard_step}")
            
            # TODO: Implement wizard steps
            # For now, just show a completion message
            if self.wizard_step == 1:
                self.instruction_label.setText("Nozzle Change Complete")
                self.detail_label.setText(f"Nozzle change for {self.current_tool.upper()} has been completed successfully.")
                self.next_button.setText("Finish")
            elif self.wizard_step == 2:
                self.cancel_wizard()  # Return to main screen
                
        except Exception as e:
            self.logger.error(f"Error advancing wizard step: {e}")

    def showEvent(self, event):
        """Reset to changeFilamentPage whenever this widget is shown."""
        super().showEvent(event)
        try:
            self.nozzle_change_stacked_widget.setCurrentWidget(self.step1_page)
            self.logger.debug("Reset stacked widget to step1_page on show")
        except Exception as e:
            self.logger.error(f"Error resetting to step1_page: {e}")
