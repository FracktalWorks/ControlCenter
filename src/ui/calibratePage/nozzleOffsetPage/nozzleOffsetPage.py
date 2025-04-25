from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QDoubleSpinBox, QLabel
from utils.helpers import check_ui_elements

class NozzleOffsetPage(QWidget):
    def __init__(self, main_window):
        super(NozzleOffsetPage, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibratePage/nozzleOffsetPage/nozzleOffsetPage.ui', self)
            print("NozzleOffsetPage UI loaded successfully")
        except Exception as e:
            print(f"Failed to load NozzleOffsetPage UI file: {e}")

        # Find buttons by their object names
        self.nozzleOffsetBackButton = self.findChild(QPushButton, 'nozzleOffsetBackButton')
        self.nozzleOffsetSetButton = self.findChild(QPushButton, 'nozzleOffsetSetButton')

        # Find other UI elements
        self.nozzleOffsetDoubleSpinBox = self.findChild(QDoubleSpinBox, 'nozzleOffsetDoubleSpinBox')
        self.currentNozzleOffsetLabel = self.findChild(QLabel, 'currentNozzleOffset_2')

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions - with safety checks
        self._connect_buttons()

        # Initialize the current nozzle offset
        self.current_nozzle_offset = 0.0
        self.update_current_nozzle_offset_label()

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Group widgets for better reporting
        buttons = {
            "nozzleOffsetBackButton": self.nozzleOffsetBackButton,
            "nozzleOffsetSetButton": self.nozzleOffsetSetButton
        }
        check_ui_elements(self, buttons, "NozzleOffsetPage - Buttons")
        
        other_elements = {
            "nozzleOffsetDoubleSpinBox": self.nozzleOffsetDoubleSpinBox,
            "currentNozzleOffsetLabel": self.currentNozzleOffsetLabel
        }
        check_ui_elements(self, other_elements, "NozzleOffsetPage - Other Elements")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        if self.nozzleOffsetBackButton:
            self.nozzleOffsetBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        
        if self.nozzleOffsetSetButton:
            self.nozzleOffsetSetButton.clicked.connect(self.set_nozzle_offset)

    def set_nozzle_offset(self):
        """Set the nozzle offset based on the value in the spin box."""
        if self.nozzleOffsetDoubleSpinBox:
            self.current_nozzle_offset = self.nozzleOffsetDoubleSpinBox.value()
            print(f"Nozzle Offset set to: {self.current_nozzle_offset} mm")
            self.update_current_nozzle_offset_label()
        else:
            print("Nozzle offset spin box not found")

    def update_current_nozzle_offset_label(self):
        """Update the label to display the current nozzle offset."""
        if self.currentNozzleOffsetLabel:
            self.currentNozzleOffsetLabel.setText(f"{self.current_nozzle_offset:.2f} mm")
        else:
            print("Current nozzle offset label not found")