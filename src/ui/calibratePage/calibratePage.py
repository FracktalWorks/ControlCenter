from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi

class CalibratePage(QWidget):
    def __init__(self, parent=None):
        super(CalibratePage, self).__init__(parent)
        loadUi("ui/calibratePage/calibratePage.ui", self)

        # Example: Connect buttons to navigate to specific calibration screens
        self.bed_leveling_button.clicked.connect(parent.switch_to_bed_leveling)
        self.nozzle_offset_button.clicked.connect(parent.switch_to_nozzle_offset)
        self.tool_offset_button.clicked.connect(parent.switch_to_tool_offset)
        self.test_print_button.clicked.connect(parent.switch_to_test_print)

    #Replace bed_leveling_button, nozzle_offset_button, tool_offset_button, 
    #and test_print_button with the actual object names of the buttons in your .ui file.