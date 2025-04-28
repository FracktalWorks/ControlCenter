from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements

class BedLeveling(QWidget):
    """
    Bed Leveling widget that guides the user through the bed leveling calibration process
    with a multi-step wizard interface.
    """
    def __init__(self, main_window):
        super(BedLeveling, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibrate_screen/bedLevelingPage/bedLevelingPage.ui', self)
            print("BedLeveling UI loaded successfully")
        except Exception as e:
            print(f"Failed to load BedLeveling UI file: {e}")

        # Find stacked widget and pages
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        
        # Define UI elements by groups
        self.pages = {
            "nozzleHeightStep1Page": self.findChild(QWidget, 'nozzleHeightStep1Page'),
            "quickStep1Page": self.findChild(QWidget, 'quickStep1Page'),
            "quickStep2Page": self.findChild(QWidget, 'quickStep2Page'),
            "quickStep3Page": self.findChild(QWidget, 'quickStep3Page'),
            "quickStep4Page": self.findChild(QWidget, 'quickStep4Page')
        }
        
        self.step1_buttons = {
            "moveZPT1CaliberateButton": self.findChild(QPushButton, 'moveZPT1CaliberateButton'),
            "moveZMT1CaliberateButton": self.findChild(QPushButton, 'moveZMT1CaliberateButton'),
            "nozzleHeightStep1NextButton": self.findChild(QPushButton, 'nozzleHeightStep1NextButton'),
            "nozzleHeightStep1CancelButton": self.findChild(QPushButton, 'nozzleHeightStep1CancelButton')
        }
        
        self.quick_step_buttons = {
            "quickStep1NextButton": self.findChild(QPushButton, 'quickStep1NextButton'),
            "quickStep1CancelButton": self.findChild(QPushButton, 'quickStep1CancelButton'),
            "quickStep2NextButton": self.findChild(QPushButton, 'quickStep2NextButton'),
            "quickStep2CancelButton": self.findChild(QPushButton, 'quickStep2CancelButton'),
            "quickStep3NextButton": self.findChild(QPushButton, 'quickStep3NextButton'),
            "quickStep3CancelButton": self.findChild(QPushButton, 'quickStep3CancelButton'),
            "quickStep4NextButton": self.findChild(QPushButton, 'quickStep4NextButton'),
            "quickStep4CancelButton": self.findChild(QPushButton, 'quickStep4CancelButton')
        }

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions
        self._connect_buttons()

        # Set the default screen to nozzleHeightStep1Page
        self._navigate_to_page("nozzleHeightStep1Page")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        check_ui_elements(self, self.pages, "BedLeveling - Pages")
        check_ui_elements(self, self.step1_buttons, "BedLeveling - Step 1 Buttons")
        check_ui_elements(self, self.quick_step_buttons, "BedLeveling - Quick Step Buttons")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        # Movement control buttons
        if self.step1_buttons["moveZPT1CaliberateButton"]:
            self.step1_buttons["moveZPT1CaliberateButton"].clicked.connect(self.move_z_pt1)

        if self.step1_buttons["moveZMT1CaliberateButton"]:
            self.step1_buttons["moveZMT1CaliberateButton"].clicked.connect(self.move_z_mt1)

        # Navigation buttons - Step 1
        if self.step1_buttons["nozzleHeightStep1NextButton"]:
            self.step1_buttons["nozzleHeightStep1NextButton"].clicked.connect(
                lambda: self._navigate_to_page("quickStep1Page"))

        if self.step1_buttons["nozzleHeightStep1CancelButton"]:
            self.step1_buttons["nozzleHeightStep1CancelButton"].clicked.connect(
                self._return_to_main_calibration)

        # Navigation buttons - Quick Steps
        steps = [
            ("quickStep1NextButton", "quickStep2Page"),
            ("quickStep2NextButton", "quickStep3Page"),
            ("quickStep3NextButton", "quickStep4Page"),
            ("quickStep4NextButton", None)  # None will trigger finish_bed_leveling
        ]
        
        for button_name, next_page in steps:
            button = self.quick_step_buttons.get(button_name)
            if button:
                if next_page:
                    button.clicked.connect(
                        lambda checked=False, page=next_page: self._navigate_to_page(page))
                else:
                    button.clicked.connect(self._finish_bed_leveling)
        
        # Cancel buttons - all steps
        cancel_buttons = [
            "quickStep1CancelButton",
            "quickStep2CancelButton",
            "quickStep3CancelButton",
            "quickStep4CancelButton"
        ]
        
        for button_name in cancel_buttons:
            button = self.quick_step_buttons.get(button_name)
            if button:
                button.clicked.connect(self._return_to_main_calibration)

    def _navigate_to_page(self, page_name):
        """Navigate to a specific page in the stackedWidget"""
        target_page = self.pages.get(page_name)
        if self.stackedWidget and target_page:
            print(f"Navigating to {page_name}")
            self.stackedWidget.setCurrentWidget(target_page)
        else:
            print(f"Error: Cannot navigate to {page_name}")

    def _return_to_main_calibration(self):
        """Cancel bed leveling process and return to main calibration page"""
        print("Bed leveling process canceled")
        if hasattr(self.main_window, 'calibrate_screen'):
            # Use standard navigation logic in CalibrateScreen
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            print("Returning to main calibration page from bed leveling")

    def _finish_bed_leveling(self):
        """Finish bed leveling process and return to main calibration page"""
        print("Bed leveling process finished")
        self._return_to_main_calibration()

    # Motion control methods
    def move_z_pt1(self):
        """Move Z-axis to positive direction for calibration"""
        print("Move Z-axis to PT1 button clicked")
        # Actual implementation would send commands to the printer
        # Example: self.main_window.octoprint_client.move_z(amount=0.1)

    def move_z_mt1(self):
        """Move Z-axis to negative direction for calibration"""
        print("Move Z-axis to MT1 button clicked")
        # Actual implementation would send commands to the printer
        # Example: self.main_window.octoprint_client.move_z(amount=-0.1)