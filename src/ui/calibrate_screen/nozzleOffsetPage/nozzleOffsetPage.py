from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QDoubleSpinBox, QLabel
from utils.helpers import check_ui_elements

class NozzleOffsetPage(QWidget):
    """
    Nozzle Offset configuration page that allows users to adjust and set the
    offset values for the printer's nozzle.
    """
    def __init__(self, main_window):
        super(NozzleOffsetPage, self).__init__()
        self.main_window = main_window
        self.current_nozzle_offset = 0.0

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibrate_screen/nozzleOffsetPage/nozzleOffsetPage.ui', self)
            print("NozzleOffsetPage UI loaded successfully")
        except Exception as e:
            print(f"Failed to load NozzleOffsetPage UI file: {e}")

        # Define UI elements by groups
        self.buttons = {
            "nozzleOffsetBackButton": self.findChild(QPushButton, 'nozzleOffsetBackButton'),
            "nozzleOffsetSetButton": self.findChild(QPushButton, 'nozzleOffsetSetButton')
        }
        
        self.input_controls = {
            "nozzleOffsetDoubleSpinBox": self.findChild(QDoubleSpinBox, 'nozzleOffsetDoubleSpinBox'),
            "currentNozzleOffsetLabel": self.findChild(QLabel, 'currentNozzleOffset_2')
        }

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions
        self._connect_buttons()

        # Initialize the current nozzle offset display
        self._update_current_nozzle_offset_label()

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        check_ui_elements(self, self.buttons, "NozzleOffsetPage - Buttons")
        check_ui_elements(self, self.input_controls, "NozzleOffsetPage - Input Controls")

    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        if self.buttons["nozzleOffsetBackButton"]:
            self.buttons["nozzleOffsetBackButton"].clicked.connect(self._return_to_main_calibration)
        
        if self.buttons["nozzleOffsetSetButton"]:
            self.buttons["nozzleOffsetSetButton"].clicked.connect(self._set_nozzle_offset)
            
    def _return_to_main_calibration(self):
        """Return to the main calibration page when back button is pressed"""
        if hasattr(self.main_window, 'calibrate_screen'):
            # Use the standard navigation logic in CalibrateScreen
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            print("Returning to main calibration page from nozzle offset page")

    def _set_nozzle_offset(self):
        """Set the nozzle offset based on the value in the spin box."""
        if self.input_controls["nozzleOffsetDoubleSpinBox"]:
            self.current_nozzle_offset = self.input_controls["nozzleOffsetDoubleSpinBox"].value()
            print(f"Setting nozzle offset to: {self.current_nozzle_offset} mm")
            self._update_current_nozzle_offset_label()
            # Actual implementation would send commands to the printer
            # Example: self.main_window.octoprint_client.set_nozzle_offset(self.current_nozzle_offset)

    def _update_current_nozzle_offset_label(self):
        """Update the label to display the current nozzle offset."""
        if self.input_controls["currentNozzleOffsetLabel"]:
            self.input_controls["currentNozzleOffsetLabel"].setText(f"{self.current_nozzle_offset:.2f} mm")