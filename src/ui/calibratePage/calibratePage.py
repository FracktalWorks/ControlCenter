from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton
from PyQt5 import uic
from utils.helpers import check_ui_elements

class CalibratePage(QWidget):
    def __init__(self, main_window):
        super(CalibratePage, self).__init__()
        self.main_window = main_window
        
        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibratePage/calibratePage.ui', self)
            print("CalibratePage UI loaded successfully")
        except Exception as e:
            print(f"Failed to load CalibratePage UI file: {e}")

        # Initialize buttons by finding them in the UI
        self.calibration_wizard_button = self.findChild(QToolButton, "calibrationWizardButton")
        self.test_prints_button = self.findChild(QToolButton, "testPrintsButton")
        self.input_shaper_calibrate_button = self.findChild(QToolButton, "inputShaperCalibrateButton")
        self.nozzle_offset_button = self.findChild(QToolButton, "nozzleOffsetButton")
        self.tool_offset_z_button = self.findChild(QToolButton, "toolOffsetZButton")
        self.tool_offset_xy_button = self.findChild(QToolButton, "toolOffsetXYButton")
        self.idex_calibration_wizard_button = self.findChild(QToolButton, "idexCalibrationWizardButton")
        self.back_button = self.findChild(QPushButton, "calibrateBackButton")

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions - with safety checks
        self._connect_buttons()
    
    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Group widgets for better reporting
        calibration_buttons = {
            "calibrationWizardButton": self.calibration_wizard_button,
            "testPrintsButton": self.test_prints_button,
            "inputShaperCalibrateButton": self.input_shaper_calibrate_button,
            "nozzleOffsetButton": self.nozzle_offset_button,
            "toolOffsetZButton": self.tool_offset_z_button,
            "toolOffsetXYButton": self.tool_offset_xy_button,
            "idexCalibrationWizardButton": self.idex_calibration_wizard_button,
            "calibrateBackButton": self.back_button
        }
        
        # Use the helper function to check and report missing widgets
        check_ui_elements(self, calibration_buttons, "CalibratePage")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        if self.calibration_wizard_button:
            self.calibration_wizard_button.clicked.connect(self.open_bed_leveling)
        
        if self.test_prints_button:
            self.test_prints_button.clicked.connect(self.main_window.switch_to_test_prints)
        
        if self.input_shaper_calibrate_button:
            self.input_shaper_calibrate_button.clicked.connect(self.main_window.switch_to_input_shaper_calibration)
        
        if self.nozzle_offset_button:
            self.nozzle_offset_button.clicked.connect(self.main_window.switch_to_nozzle_offset)
        
        if self.tool_offset_z_button:
            self.tool_offset_z_button.clicked.connect(self.main_window.switch_to_tool_offset_z)
        
        if self.tool_offset_xy_button:
            self.tool_offset_xy_button.clicked.connect(self.main_window.switch_to_tool_offset_xy)
        
        if self.idex_calibration_wizard_button:
            self.idex_calibration_wizard_button.clicked.connect(self.main_window.switch_to_idex_calibration_wizard)
        
        if self.back_button:
            self.back_button.clicked.connect(self.main_window.switch_to_previous_screen)
    
    def open_bed_leveling(self):
        # The calibration wizard is actually the bed leveling wizard in the original code
        self.main_window.switch_to_bed_leveling()
        print("Bed leveling (calibration wizard) button clicked")