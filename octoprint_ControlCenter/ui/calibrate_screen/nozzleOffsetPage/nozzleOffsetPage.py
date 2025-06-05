from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QDoubleSpinBox, QLabel
from PyQt5.QtGui import QPalette, QColor
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

class NozzleOffsetPage(QWidget):
    """
    Nozzle Offset configuration page that allows users to adjust and set the
    offset values for the printer's nozzle.
    """
    def __init__(self, main_window):
        super(NozzleOffsetPage, self).__init__()
        self.main_window = main_window
        self.current_nozzle_offset = 0.0
        
        # Set up logger for this class
        self.logger = setup_logger('NozzleOffsetPage')
        self.logger.info("Initializing NozzleOffsetPage")

        # Load the UI
        try:
            uic.loadUi('octoprint_ControlCenter/ui/calibrate_screen/nozzleOffsetPage/nozzleOffsetPage.ui', self)
            self.logger.info("NozzleOffsetPage UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load NozzleOffsetPage UI file: {e}", exc_info=True)

        # Initialize UI components
        self.nozzleOffsetBackButton = self.findChild(QPushButton, "nozzleOffsetBackButton")
        self.nozzleOffsetSetButton = self.findChild(QPushButton, "nozzleOffsetSetButton")
        self.nozzleOffsetDoubleSpinBox = self.findChild(QDoubleSpinBox, "nozzleOffsetDoubleSpinBox")
        self.currentNozzleOffsetLabel = self.findChild(QLabel, "currentNozzleOffset_2")

        # Validate UI elements
        check_ui_elements(self, [
            self.nozzleOffsetBackButton, self.nozzleOffsetSetButton,
            self.nozzleOffsetDoubleSpinBox, self.currentNozzleOffsetLabel
        ], "Nozzle Offset Page")

        # Connect buttons to their respective methods
        if self.nozzleOffsetBackButton:
            self.nozzleOffsetBackButton.clicked.connect(self._return_to_main_calibration)
        if self.nozzleOffsetSetButton:
            self.nozzleOffsetSetButton.clicked.connect(self._set_nozzle_offset)

        # Initialize the current nozzle offset display
        if self.currentNozzleOffsetLabel:
            self.currentNozzleOffsetLabel.setText(f"{self.current_nozzle_offset:.2f} mm")
            
        # Configure spinbox if it exists
        if self.nozzleOffsetDoubleSpinBox:
            self._configure_spinbox(self.nozzleOffsetDoubleSpinBox)

    def _return_to_main_calibration(self):
        """Return to the main calibration page when back button is pressed"""
        self.logger.info("Returning to main calibration page")
        if hasattr(self.main_window, 'calibrate_screen'):
            # Use the standard navigation logic in CalibrateScreen
            if hasattr(self.main_window.calibrate_screen, 'calibration_stacked_widget') and \
               hasattr(self.main_window.calibrate_screen, 'main_calibrate_page'):
                self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                    self.main_window.calibrate_screen.main_calibrate_page)
                self.logger.debug("Successfully switched to main calibration page")
            else:
                self.logger.error("Cannot return to main calibration - required widgets not found")
        else:
            self.logger.error("Cannot return to main calibration - main_window.calibrate_screen not found")

    def _set_nozzle_offset(self):
        """Set the nozzle offset based on the value in the spin box."""
        if self.nozzleOffsetDoubleSpinBox:
            self.current_nozzle_offset = self.nozzleOffsetDoubleSpinBox.value()
            self.logger.info(f"Setting nozzle offset to: {self.current_nozzle_offset} mm")
            
            # Update the display label
            if self.currentNozzleOffsetLabel:
                self.currentNozzleOffsetLabel.setText(f"{self.current_nozzle_offset:.2f} mm")
            
            # Actual implementation would send commands to the printer
            # Example: self.main_window.octoprint_client.set_nozzle_offset(self.current_nozzle_offset)
        else:
            self.logger.error("Cannot set nozzle offset - spin box not found")

    def _configure_spinbox(self, spinbox):
        """Configure the nozzle offset spinbox to be readonly, disabled, and styled."""
        if spinbox and spinbox.lineEdit():
            spinbox.lineEdit().setReadOnly(True)
            spinbox.lineEdit().setDisabled(True)
            palette = QPalette()
            palette.setColor(QPalette.Highlight, QColor(40, 40, 40))
            spinbox.lineEdit().setPalette(palette)
            self.logger.debug("Spinbox configured with custom styling")
        else:
            self.logger.warning("Cannot configure spinbox - invalid reference")