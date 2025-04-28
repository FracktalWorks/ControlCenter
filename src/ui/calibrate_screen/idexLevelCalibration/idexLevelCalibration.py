from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements

class IdexLevelCalibration(QWidget):
    """
    IDEX (Independent Dual Extruder) Level Calibration widget that guides the user
    through a multi-step calibration process for aligning the dual extruders.
    """
    def __init__(self, main_window):
        super(IdexLevelCalibration, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibrate_screen/idexLevelCalibration/idexLevelCalibration.ui', self)
            print("IdexLevelCalibration UI loaded successfully")
        except Exception as e:
            print(f"Failed to load IdexLevelCalibration UI file: {e}")

        # Find stacked widget and pages
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        
        # Define pages dictionary
        self.pages = {
            "step1": self.findChild(QWidget, 'idexConfigStep1Page'),
            "step2": self.findChild(QWidget, 'idexConfigStep2Page'),
            "step3": self.findChild(QWidget, 'idexConfigStep3Page'),
            "step4": self.findChild(QWidget, 'idexConfigStep4Page'),
            "step5": self.findChild(QWidget, 'idexConfigStep5Page')
        }
        
        # Define buttons by step
        self.navigation_buttons = {}
        
        # Step buttons for steps 1-5
        for step in range(1, 6):
            self.navigation_buttons[f"step{step}_next"] = self.findChild(
                QPushButton, f'idexConfigStep{step}NextButton')
            self.navigation_buttons[f"step{step}_cancel"] = self.findChild(
                QPushButton, f'idexConfigStep{step}CancelButton')
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions
        self._connect_buttons()

        # Set the default screen
        self._navigate_to_step(1)

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        check_ui_elements(self, self.pages, "IdexLevelCalibration - Pages")
        
        # Check button groups by step
        for step in range(1, 6):
            step_buttons = {
                f"idexConfigStep{step}NextButton": self.navigation_buttons[f"step{step}_next"],
                f"idexConfigStep{step}CancelButton": self.navigation_buttons[f"step{step}_cancel"]
            }
            check_ui_elements(self, step_buttons, f"IdexLevelCalibration - Step {step} Buttons")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        # Connect Next buttons for steps 1-4
        for step in range(1, 5):
            next_btn = self.navigation_buttons.get(f"step{step}_next")
            if next_btn:
                next_btn.clicked.connect(lambda checked=False, s=step+1: self._navigate_to_step(s))
        
        # Connect Step 5 Next button to finish method
        final_next_btn = self.navigation_buttons.get("step5_next")
        if final_next_btn:
            final_next_btn.clicked.connect(self._finish_calibration)
        
        # Connect all Cancel buttons
        for step in range(1, 6):
            cancel_btn = self.navigation_buttons.get(f"step{step}_cancel")
            if cancel_btn:
                cancel_btn.clicked.connect(self._cancel_calibration)

    def _navigate_to_step(self, step_number):
        """Navigate to a specific step in the calibration process"""
        target_page = self.pages.get(f"step{step_number}")
        if self.stackedWidget and target_page:
            print(f"Navigating to IDEX Calibration Step {step_number}")
            self.stackedWidget.setCurrentWidget(target_page)
        else:
            print(f"Error: Cannot navigate to IDEX Calibration Step {step_number}")

    def _cancel_calibration(self):
        """Cancel the IDEX calibration process and return to main calibration page"""
        print("IDEX Calibration process canceled")
        self._return_to_main_calibration()
    
    def _finish_calibration(self):
        """Finish the IDEX calibration process and return to main calibration page"""
        print("IDEX Calibration process finished")
        self._return_to_main_calibration()
    
    def _return_to_main_calibration(self):
        """Common method to return to the main calibration screen"""
        if hasattr(self.main_window, 'calibrate_screen'):
            # Use standard navigation logic in CalibrateScreen
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            print("Returning to main calibration page from IDEX calibration")