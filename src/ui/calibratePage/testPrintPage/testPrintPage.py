from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements

class TestPrintPage(QWidget):
    def __init__(self, main_window):
        super(TestPrintPage, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibratePage/testPrintPage/testPrintPage.ui', self)
            print("TestPrintPage UI loaded successfully")
        except Exception as e:
            print(f"Failed to load TestPrintPage UI file: {e}")

        # Find buttons by their object names
        self.testPrintsNextButton = self.findChild(QPushButton, 'testPrintsNextButton')
        self.testPrintsBackButton = self.findChild(QPushButton, 'testPrintsBackButton')
        self.testPrintsCancelButton = self.findChild(QPushButton, 'testPrintsCancelButton')
        self.singleNozzlePrintButton = self.findChild(QPushButton, 'singleNozzlePrintButton')
        self.movementTestPrintButton = self.findChild(QPushButton, 'movementTestPrintButton')
        self.dualCaliberationPrintButton = self.findChild(QPushButton, 'dualCaliberationPrintButton')
        self.dualNozzlePrintButton = self.findChild(QPushButton, 'dualNozzlePrintButton')
        self.bedLevelPrintButton = self.findChild(QPushButton, 'bedLevelPrintButton')

        # Find stacked widget and pages
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        self.testPrintPage1 = self.findChild(QWidget, 'testPrintPage1')
        self.testPrintPage2 = self.findChild(QWidget, 'testPrintPage2')

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions - with safety checks
        self._connect_buttons()

        # Set the default screen
        if self.stackedWidget and self.testPrintPage2:
            self.stackedWidget.setCurrentWidget(self.testPrintPage2)

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Group widgets for better reporting
        pages = {
            "stackedWidget": self.stackedWidget,
            "testPrintPage1": self.testPrintPage1,
            "testPrintPage2": self.testPrintPage2
        }
        check_ui_elements(self, pages, "TestPrintPage - Pages")
        
        navigation_buttons = {
            "testPrintsNextButton": self.testPrintsNextButton,
            "testPrintsBackButton": self.testPrintsBackButton,
            "testPrintsCancelButton": self.testPrintsCancelButton
        }
        check_ui_elements(self, navigation_buttons, "TestPrintPage - Navigation Buttons")
        
        print_buttons = {
            "singleNozzlePrintButton": self.singleNozzlePrintButton,
            "movementTestPrintButton": self.movementTestPrintButton,
            "dualCaliberationPrintButton": self.dualCaliberationPrintButton,
            "dualNozzlePrintButton": self.dualNozzlePrintButton,
            "bedLevelPrintButton": self.bedLevelPrintButton
        }
        check_ui_elements(self, print_buttons, "TestPrintPage - Print Buttons")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        if self.testPrintsNextButton:
            self.testPrintsNextButton.clicked.connect(self.main_window.switch_to_next_screen)
        
        if self.testPrintsBackButton:
            self.testPrintsBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        
        if self.testPrintsCancelButton:
            self.testPrintsCancelButton.clicked.connect(self.main_window.switch_to_previous_screen)
        
        if self.singleNozzlePrintButton:
            self.singleNozzlePrintButton.clicked.connect(self.single_nozzle_test_print)
        
        if self.movementTestPrintButton:
            self.movementTestPrintButton.clicked.connect(self.movement_stress_test)
        
        if self.dualCaliberationPrintButton:
            self.dualCaliberationPrintButton.clicked.connect(self.dual_calibration_print)
        
        if self.dualNozzlePrintButton:
            self.dualNozzlePrintButton.clicked.connect(self.dual_nozzle_test_print)
        
        if self.bedLevelPrintButton:
            self.bedLevelPrintButton.clicked.connect(self.bed_leveling_print)

    def single_nozzle_test_print(self):
        """Logic for single nozzle test print."""
        print("Single Nozzle Test Print button clicked")

    def movement_stress_test(self):
        """Logic for movement stress test."""
        print("Movement Stress Test button clicked")

    def dual_calibration_print(self):
        """Logic for dual calibration print."""
        print("Dual Calibration Print button clicked")

    def dual_nozzle_test_print(self):
        """Logic for dual nozzle test print."""
        print("Dual Nozzle Test Print button clicked")

    def bed_leveling_print(self):
        """Logic for bed leveling print."""
        print("Bed Leveling Print button clicked")