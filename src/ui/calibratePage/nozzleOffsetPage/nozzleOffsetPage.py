from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QDoubleSpinBox, QLabel

class NozzleOffsetPage(QWidget):
    def __init__(self, main_window):
        super(NozzleOffsetPage, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibratePage/nozzleOffsetPage/nozzleOffsetPage.ui', self)
            print("UI file loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

        # Find buttons by their object names
        self.nozzleOffsetBackButton = self.findChild(QPushButton, 'nozzleOffsetBackButton')
        self.nozzleOffsetSetButton = self.findChild(QPushButton, 'nozzleOffsetSetButton')

        # Find other UI elements
        self.nozzleOffsetDoubleSpinBox = self.findChild(QDoubleSpinBox, 'nozzleOffsetDoubleSpinBox')
        #self.currentNozzleOffsetLabel = self.findChild(QLabel, 'currentNozzleOffset_2')

        # Check if all elements are found
        if not all([self.nozzleOffsetBackButton, self.nozzleOffsetSetButton, self.nozzleOffsetDoubleSpinBox, self.currentNozzleOffsetLabel]):
            raise ValueError("One or more UI elements not found in the UI file")

        # Connect buttons to their respective functions
        self.nozzleOffsetBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        self.nozzleOffsetSetButton.clicked.connect(self.set_nozzle_offset)

        # Initialize the current nozzle offset
        self.current_nozzle_offset = 0.0
        self.update_current_nozzle_offset_label()

    def set_nozzle_offset(self):
        """Set the nozzle offset based on the value in the spin box."""
        self.current_nozzle_offset = self.nozzleOffsetDoubleSpinBox.value()
        print(f"Nozzle Offset set to: {self.current_nozzle_offset} mm")
        self.update_current_nozzle_offset_label()

    def update_current_nozzle_offset_label(self):
        """Update the label to display the current nozzle offset."""
        self.currentNozzleOffsetLabel.setText(f"{self.current_nozzle_offset:.2f} mm")