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
        
        # Define UI elements by category
        self.ui_elements = {
            "containers": {
                "stackedWidget": {"type": QStackedWidget, "instance": None}
            },
            "pages": {
                "idexConfigStep1Page": {"type": QWidget, "instance": None},
                "idexConfigStep2Page": {"type": QWidget, "instance": None},
                "idexConfigStep3Page": {"type": QWidget, "instance": None},
                "idexConfigStep4Page": {"type": QWidget, "instance": None},
                "idexConfigStep5Page": {"type": QWidget, "instance": None}
            },
            "navigation_buttons": {
                "idexConfigStep1NextButton": {"type": QPushButton, "instance": None},
                "idexConfigStep1CancelButton": {"type": QPushButton, "instance": None},
                "idexConfigStep2NextButton": {"type": QPushButton, "instance": None},
                "idexConfigStep2CancelButton": {"type": QPushButton, "instance": None},
                "idexConfigStep3NextButton": {"type": QPushButton, "instance": None},
                "idexConfigStep3CancelButton": {"type": QPushButton, "instance": None},
                "idexConfigStep4NextButton": {"type": QPushButton, "instance": None},
                "idexConfigStep4CancelButton": {"type": QPushButton, "instance": None},
                "idexConfigStep5NextButton": {"type": QPushButton, "instance": None},
                "idexConfigStep5CancelButton": {"type": QPushButton, "instance": None}
            }
        }

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibrate_screen/idexLevelCalibration/idexLevelCalibration.ui', self)
            print("IdexLevelCalibration UI loaded successfully")
        except Exception as e:
            print(f"Failed to load IdexLevelCalibration UI file: {e}")

        # Initialize UI elements
        self._initialize_ui_elements()

        # Connect buttons to their respective functions
        self._connect_buttons()

        # Set the default screen
        self._navigate_to_step(1)

    def _initialize_ui_elements(self):
        """Initialize UI elements from the loaded UI file"""
        # Initialize containers
        for element_name, element_info in self.ui_elements["containers"].items():
            element_info["instance"] = self.findChild(element_info["type"], element_name)

        # Initialize pages
        for element_name, element_info in self.ui_elements["pages"].items():
            element_info["instance"] = self.findChild(element_info["type"], element_name)

        # Initialize navigation buttons
        for element_name, element_info in self.ui_elements["navigation_buttons"].items():
            element_info["instance"] = self.findChild(element_info["type"], element_name)

        # Create a simple lookup dictionary for page numbers
        self.pages = {
            f"step{i}": self.ui_elements["pages"][f"idexConfigStep{i}Page"]["instance"]
            for i in range(1, 6)
        }
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
    
    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Check containers
        for category, elements in self.ui_elements.items():
            missing_elements = {name: info for name, info in elements.items() if info["instance"] is None}
            if missing_elements:
                print(f"Missing UI elements in {category}: {', '.join(missing_elements.keys())}")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        # Connect Next buttons for steps 1-4
        for step in range(1, 5):
            next_btn = self.ui_elements["navigation_buttons"][f"idexConfigStep{step}NextButton"]["instance"]
            if next_btn:
                next_btn.clicked.connect(lambda checked=False, s=step+1: self._navigate_to_step(s))
        
        # Connect Step 5 Next button to finish method
        final_next_btn = self.ui_elements["navigation_buttons"]["idexConfigStep5NextButton"]["instance"]
        if final_next_btn:
            final_next_btn.clicked.connect(self._finish_calibration)
        
        # Connect all Cancel buttons
        for step in range(1, 6):
            cancel_btn = self.ui_elements["navigation_buttons"][f"idexConfigStep{step}CancelButton"]["instance"]
            if cancel_btn:
                cancel_btn.clicked.connect(self._cancel_calibration)

    def _navigate_to_step(self, step_number):
        """Navigate to a specific step in the calibration process"""
        target_page = self.pages.get(f"step{step_number}")
        stacked_widget = self.ui_elements["containers"]["stackedWidget"]["instance"]
        
        if stacked_widget and target_page:
            print(f"Navigating to IDEX Calibration Step {step_number}")
            stacked_widget.setCurrentWidget(target_page)
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