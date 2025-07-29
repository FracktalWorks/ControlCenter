from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QComboBox
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils import dialog

from octoprint_client.octoprint_threaded_file_upload import ThreadFileUpload




class TestPrintPage(QWidget):
    """
    Test Print Page that provides various calibration print options for
    testing printer settings and alignment.
    """

    def __init__(self, main_window):
        super(TestPrintPage, self).__init__()
        self.main_window = main_window
        # Use centralized logger
        self.logger = get_logger(self.__class__.__name__)

        # Load the UI
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi(
                '/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/calibrate_screen/testPrintPage/testPrintPage.ui',
                self)
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
        self.testPrintsTool0SizeComboBox = self.findChild(QComboBox, "testPrintsTool0SizeComboBox")
        self.testPrintsTool1SizeComboBox = self.findChild(QComboBox, "testPrintsTool1SizeComboBox_6")

        # Validate all UI elements
        check_ui_elements(self, [
            self.stackedWidget, self.testPrintPage1, self.testPrintPage2,
            self.testPrintsNextButton, self.testPrintsBackButton, self.testPrintsCancelButton,
            self.singleNozzlePrintButton, self.movementTestPrintButton, self.dualCaliberationPrintButton,
            self.dualNozzlePrintButton, self.bedLevelPrintButton
        ], "TestPrintPage UI Elements")

        # Connect signals to slots
        self.testPrintsNextButton.pressed.connect(
            lambda: self.stackedWidget.setCurrentWidget(
                self.testPrintPage2
            )
        )
        self.testPrintsBackButton.pressed.connect(
            lambda: self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                    self.main_window.calibrate_screen.main_calibrate_page
            )
        )
        self.testPrintsCancelButton.pressed.connect(
            lambda: self.stackedWidget.setCurrentWidget(
                    self.testPrintPage1
            )
        )

        self.dualCaliberationPrintButton.pressed.connect(
            lambda: self.testPrint(
                str(self.testPrintsTool0SizeComboBox.currentText()).replace('.', ''),
                str(self.testPrintsTool1SizeComboBox.currentText()).replace('.', ''),
                'dualCalibration'
            )
        )
        self.bedLevelPrintButton.pressed.connect(
            lambda: self.testPrint(
                str(self.testPrintsTool0SizeComboBox.currentText()).replace('.', ''),
                str(self.testPrintsTool1SizeComboBox.currentText()).replace('.', ''),
                'bedLevel'
            )
        )
        self.movementTestPrintButton.pressed.connect(
            lambda: self.testPrint(
                str(self.testPrintsTool0SizeComboBox.currentText()).replace('.', ''),
                str(self.testPrintsTool1SizeComboBox.currentText()).replace('.', ''),
                'movementTest'
            )
        )
        self.singleNozzlePrintButton.pressed.connect(
            lambda: self.testPrint(
                str(self.testPrintsTool0SizeComboBox.currentText()).replace('.', ''),
                str(self.testPrintsTool1SizeComboBox.currentText()).replace('.', ''),
                'dualTest'
            )
        )
        self.dualNozzlePrintButton.pressed.connect(
            lambda: self.testPrint(
                str(self.testPrintsTool0SizeComboBox.currentText()).replace('.', ''),
                str(self.testPrintsTool1SizeComboBox.currentText()).replace('.', ''),
                'singleTest'
            )
        )

        # Set the default screen to second page
        self._navigate_to_page("testPrintPage1")

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

    def testPrint(self, tool0Diameter, tool1Diameter, gcode):
        """
        Prints a test print
        :param tool0Diameter: Diameter of tool 0 nozzle.04,06 or 08
        :param tool1Diameter: Diameter of tool 1 nozzle.40,06 or 08
        :param gcode: type of gcode to print, dual nozzle calibration, bed leveling, movement or samaple prints in
        single and dual. bedLevel, dualCalibration, movementTest, dualTest, singleTest
        :return:
        """
        logger.info("MainUiClass.testPrint started")
        try:
            if gcode is 'bedLevel':
                self.printFromPath(
                    '/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/gcode/' + tool0Diameter + '_BedLeveling.gcode',
                    True)
            elif gcode is 'dualCalibration':
                self.printFromPath(
                    '/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/gcode/' + tool0Diameter + '_' + tool1Diameter + '_dual_extruder_calibration_TwinDragon600.gcode',
                    True)
            elif gcode is 'movementTest':
                self.printFromPath(
                    '/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/gcode/movementTest.gcode',
                    True)
            elif gcode is 'dualTest':
                self.printFromPath(
                    '/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/gcode/' + tool0Diameter + '_' + tool1Diameter + '_Fracktal_logo_TwinDragon600.gcode',
                    True)
            elif gcode is 'singleTest':
                self.printFromPath(
                    '/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/gcode/' + tool0Diameter + '_Fracktal_logo_Idex.gcode',
                    True)

            else:
                print("gcode not found")
        except Exception as e:
            logger.error("Error in MainUiClass.testPrint: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.testPrint: {}".format(e), overlay=True)

    def printFromPath(self, path, prnt=True):
        """
        Transfers a file from a specific to octoprint's watched folder so that it gets automatically detected by Octoprint.
        Warning: If the file is read-only, octoprint API for reading the file crashes.
        """
        logger.info("MainUiClass.printFromPath started")
        try:
            self.uploadThread = ThreadFileUpload(path, print_after_upload=prnt)
            self.uploadThread.start()
            if prnt:
                self.stackedWidget.setCurrentWidget(self.main_window.home_screen)
        except Exception as e:
            logger.error("Error in MainUiClass.printFromPath: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.printFromPath: {}".format(e), overlay=True)

    # # Print action methods
    # def _single_nozzle_test_print(self):
    #     """Logic for single nozzle test print."""
    #     self.logger.info("Single Nozzle Test Print button clicked")
    #     # Actual implementation would send commands to the printer
    #     # Example: self.main_window.octoprint_client.print_file('single_nozzle_test.gcode')
    #
    # def _movement_stress_test(self):
    #     """Logic for movement stress test."""
    #     self.logger.info("Movement Stress Test button clicked")
    #     # Actual implementation would send commands to the printer
    #
    # def _dual_calibration_print(self):
    #     """Logic for dual calibration print."""
    #     self.logger.info("Dual Calibration Print button clicked")
    #     # Actual implementation would send commands to the printer
    #
    # def _dual_nozzle_test_print(self):
    #     """Logic for dual nozzle test print."""
    #     self.logger.info("Dual Nozzle Test Print button clicked")
    #     # Actual implementation would send commands to the printer
    #
    # def _bed_leveling_print(self):
    #     """Logic for bed leveling print."""
    #     self.logger.info("Bed Leveling Print button clicked")
    #     # Actual implementation would send commands to the printer