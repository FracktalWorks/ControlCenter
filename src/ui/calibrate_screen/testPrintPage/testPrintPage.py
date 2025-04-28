from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements

class TestPrintPage(QWidget):
    """
    Test Print Page that provides various calibration print options for
    testing printer settings and alignment.
    """
    def __init__(self, main_window):
        super(TestPrintPage, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibrate_screen/testPrintPage/testPrintPage.ui', self)
            print("TestPrintPage UI loaded successfully")
        except Exception as e:
            print(f"Failed to load TestPrintPage UI file: {e}")

        # Find stacked widget and pages
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        
        # Define UI elements by groups
        self.pages = {
            "testPrintPage1": self.findChild(QWidget, 'testPrintPage1'),
            "testPrintPage2": self.findChild(QWidget, 'testPrintPage2')
        }
        
        # Navigation buttons
        self.nav_buttons = {
            "testPrintsNextButton": self.findChild(QPushButton, 'testPrintsNextButton'),
            "testPrintsBackButton": self.findChild(QPushButton, 'testPrintsBackButton'),
            "testPrintsCancelButton": self.findChild(QPushButton, 'testPrintsCancelButton')
        }
        
        # Print action buttons
        self.print_buttons = {
            "singleNozzlePrintButton": self.findChild(QPushButton, 'singleNozzlePrintButton'),
            "movementTestPrintButton": self.findChild(QPushButton, 'movementTestPrintButton'),
            "dualCaliberationPrintButton": self.findChild(QPushButton, 'dualCaliberationPrintButton'),
            "dualNozzlePrintButton": self.findChild(QPushButton, 'dualNozzlePrintButton'),
            "bedLevelPrintButton": self.findChild(QPushButton, 'bedLevelPrintButton')
        }

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions
        self._connect_buttons()

        # Set the default screen
        if self.stackedWidget and self.pages["testPrintPage2"]:
            self.stackedWidget.setCurrentWidget(self.pages["testPrintPage2"])

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        check_ui_elements(self, self.pages, "TestPrintPage - Pages")
        check_ui_elements(self, self.nav_buttons, "TestPrintPage - Navigation Buttons")
        check_ui_elements(self, self.print_buttons, "TestPrintPage - Print Buttons")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        # Navigation buttons
        if self.nav_buttons["testPrintsNextButton"]:
            self.nav_buttons["testPrintsNextButton"].clicked.connect(self.main_window.switch_to_next_screen)
        
        for back_button in ["testPrintsBackButton", "testPrintsCancelButton"]:
            if self.nav_buttons[back_button]:
                self.nav_buttons[back_button].clicked.connect(self._return_to_main_calibration)
        
        # Print action buttons - map button names to their handler methods
        button_handlers = {
            "singleNozzlePrintButton": self._single_nozzle_test_print,
            "movementTestPrintButton": self._movement_stress_test,
            "dualCaliberationPrintButton": self._dual_calibration_print,
            "dualNozzlePrintButton": self._dual_nozzle_test_print,
            "bedLevelPrintButton": self._bed_leveling_print
        }
        
        # Connect each print button to its handler
        for button_name, handler in button_handlers.items():
            button = self.print_buttons.get(button_name)
            if button:
                button.clicked.connect(handler)

    def _return_to_main_calibration(self):
        """Return to the main calibration page"""
        if hasattr(self.main_window, 'calibrate_screen'):
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            print("Returning to main calibration page from test prints")

    # Print action methods
    def _single_nozzle_test_print(self):
        """Logic for single nozzle test print."""
        print("Single Nozzle Test Print button clicked")
        # Actual implementation would send commands to the printer
        # Example: self.main_window.octoprint_client.print_file('single_nozzle_test.gcode')

    def _movement_stress_test(self):
        """Logic for movement stress test."""
        print("Movement Stress Test button clicked")
        # Actual implementation would send commands to the printer

    def _dual_calibration_print(self):
        """Logic for dual calibration print."""
        print("Dual Calibration Print button clicked")
        # Actual implementation would send commands to the printer

    def _dual_nozzle_test_print(self):
        """Logic for dual nozzle test print."""
        print("Dual Nozzle Test Print button clicked")
        # Actual implementation would send commands to the printer

    def _bed_leveling_print(self):
        """Logic for bed leveling print."""
        print("Bed Leveling Print button clicked")
        # Actual implementation would send commands to the printer