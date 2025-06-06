from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

class TestPrintPage(QWidget):
    """
    Test Print Page that provides various calibration print options for
    testing printer settings and alignment.
    """
    def __init__(self, main_window):
        super(TestPrintPage, self).__init__()
        self.main_window = main_window
        # Set up logger for this class
        self.logger = setup_logger('TestPrintPage')
        
        # Load the UI
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/calibrate_screen/testPrintPage/testPrintPage.ui', self)
            self.logger.info("TestPrintPage UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load TestPrintPage UI file: {e}", exc_info=True)
        
        # Initialize UI components
        # Container widgets
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")

        # Pages in the stacked widget
        self.testPrintPage1 = self.findChild(QWidget, "testPrintPage1")
        self.testPrintPage2 = self.findChild(QWidget, "testPrintPage2")

        # Navigation buttons
        self.testPrintsNextButton = self.findChild(QPushButton, "testPrintsNextButton")
        self.testPrintsBackButton = self.findChild(QPushButton, "testPrintsBackButton")
        self.testPrintsCancelButton = self.findChild(QPushButton, "testPrintsCancelButton")

        # Print action buttons
        self.singleNozzlePrintButton = self.findChild(QPushButton, "singleNozzlePrintButton")
        self.movementTestPrintButton = self.findChild(QPushButton, "movementTestPrintButton")
        self.dualCaliberationPrintButton = self.findChild(QPushButton, "dualCaliberationPrintButton")
        self.dualNozzlePrintButton = self.findChild(QPushButton, "dualNozzlePrintButton")
        self.bedLevelPrintButton = self.findChild(QPushButton, "bedLevelPrintButton")

        # Validate all UI elements
        check_ui_elements(self, [
            self.stackedWidget, self.testPrintPage1, self.testPrintPage2,
            self.testPrintsNextButton, self.testPrintsBackButton, self.testPrintsCancelButton,
            self.singleNozzlePrintButton, self.movementTestPrintButton, self.dualCaliberationPrintButton,
            self.dualNozzlePrintButton, self.bedLevelPrintButton
        ], "TestPrintPage UI Elements")
        
        
        # Connect signals to slots
        if self.testPrintsNextButton:
            self.testPrintsNextButton.clicked.connect(self._next_page)

        if self.testPrintsBackButton:
            self.testPrintsBackButton.clicked.connect(self._return_to_main_calibration)

        if self.testPrintsCancelButton:
            self.testPrintsCancelButton.clicked.connect(self._return_to_main_calibration)

        if self.singleNozzlePrintButton:
            self.singleNozzlePrintButton.clicked.connect(self._single_nozzle_test_print)

        if self.movementTestPrintButton:
            self.movementTestPrintButton.clicked.connect(self._movement_stress_test)

        if self.dualCaliberationPrintButton:
            self.dualCaliberationPrintButton.clicked.connect(self._dual_calibration_print)

        if self.dualNozzlePrintButton:
            self.dualNozzlePrintButton.clicked.connect(self._dual_nozzle_test_print)

        if self.bedLevelPrintButton:
            self.bedLevelPrintButton.clicked.connect(self._bed_leveling_print)

        # Set the default screen to second page
        self._navigate_to_page("testPrintPage2")


    def _navigate_to_page(self, page_name):
        """Navigate to a specific page in the stackedWidget"""
        if not self.stackedWidget:
            self.logger.error("Cannot navigate - stacked widget is missing")
            return False
        
        # Use direct attribute access instead of page_widgets dictionary
        if hasattr(self, page_name):
            target_page = getattr(self, page_name)
            self.stackedWidget.setCurrentWidget(target_page)
            self.logger.debug(f"Navigating to {page_name}")
            return True
        else:
            self.logger.error(f"Cannot navigate to {page_name} - page not found")
            return False
            
    def _next_page(self):
        """Navigate to the next page if available, or perform another action"""
        if self.stackedWidget:
            current_index = self.stackedWidget.currentIndex()
            if current_index < self.stackedWidget.count() - 1:
                self.stackedWidget.setCurrentIndex(current_index + 1)
                self.logger.debug(f"Moving to next test print page: {current_index + 1}")
            else:
                self.logger.debug("Already at last test print page")
        else:
            self.logger.error("Cannot navigate - stackedWidget is missing")

    def _return_to_main_calibration(self):
        """Return to the main calibration page"""
        self.logger.info("Returning to main calibration page from test prints")
        if hasattr(self.main_window, 'calibrate_screen'):
            if hasattr(self.main_window.calibrate_screen, 'calibration_stacked_widget') and \
               hasattr(self.main_window.calibrate_screen, 'main_calibrate_page'):
                self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                    self.main_window.calibrate_screen.main_calibrate_page)
                self.logger.debug("Successfully returned to main calibration page")
            else:
                self.logger.error("Cannot return to main calibration - required widgets not found")
        else:
            self.logger.error("Cannot return to main calibration - main_window.calibrate_screen not found")

    # Print action methods
    def _single_nozzle_test_print(self):
        """Logic for single nozzle test print."""
        self.logger.info("Single Nozzle Test Print button clicked")
        # Actual implementation would send commands to the printer
        # Example: self.main_window.octoprint_client.print_file('single_nozzle_test.gcode')

    def _movement_stress_test(self):
        """Logic for movement stress test."""
        self.logger.info("Movement Stress Test button clicked")
        # Actual implementation would send commands to the printer

    def _dual_calibration_print(self):
        """Logic for dual calibration print."""
        self.logger.info("Dual Calibration Print button clicked")
        # Actual implementation would send commands to the printer

    def _dual_nozzle_test_print(self):
        """Logic for dual nozzle test print."""
        self.logger.info("Dual Nozzle Test Print button clicked")
        # Actual implementation would send commands to the printer

    def _bed_leveling_print(self):
        """Logic for bed leveling print."""
        self.logger.info("Bed Leveling Print button clicked")
        # Actual implementation would send commands to the printer