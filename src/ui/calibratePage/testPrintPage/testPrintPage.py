from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget

class TestPrintPage(QWidget):
    def __init__(self, main_window):
        super(TestPrintPage, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibratePage/testPrintPage/testPrintPage.ui', self)
            print("UI file loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

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

        # Check if all elements are found
        if not all([ self.testPrintsNextButton, self.testPrintsBackButton,
            self.testPrintsCancelButton, self.singleNozzlePrintButton, self.movementTestPrintButton,
            self.dualCaliberationPrintButton, self.dualNozzlePrintButton, self.bedLevelPrintButton,
            self.stackedWidget, self.testPrintPage2
        ]):
            raise ValueError("One or more UI elements not found in the UI file")

        # Connect buttons to their respective functions
        self.testPrintsNextButton.clicked.connect(self.main_window.switch_to_next_screen)
        self.testPrintsBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        self.testPrintsCancelButton.clicked.connect(self.main_window.switch_to_previous_screen)
        self.singleNozzlePrintButton.clicked.connect(self.single_nozzle_test_print)
        self.movementTestPrintButton.clicked.connect(self.movement_stress_test)
        self.dualCaliberationPrintButton.clicked.connect(self.dual_calibration_print)
        self.dualNozzlePrintButton.clicked.connect(self.dual_nozzle_test_print)
        self.bedLevelPrintButton.clicked.connect(self.bed_leveling_print)

        # Set the default screen
        self.stackedWidget.setCurrentWidget(self.testPrintPage2)

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