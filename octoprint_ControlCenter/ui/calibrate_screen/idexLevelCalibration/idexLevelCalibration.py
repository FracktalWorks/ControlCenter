from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

class IdexLevelCalibration(QWidget):
    """
    IDEX (Independent Dual Extruder) Level Calibration widget that guides the user
    through a multi-step calibration process for aligning the dual extruders.
    """
    def __init__(self, main_window):
        super(IdexLevelCalibration, self).__init__()
        self.main_window = main_window
        self.logger = setup_logger('idex_calibration')
        self.logger.info("Initializing IDEX Level Calibration screen")

        # Load the .ui file
        try:
            uic.loadUi('octoprint_ControlCenter/ui/calibrate_screen/idexLevelCalibration/idexLevelCalibration.ui', self)
            self.logger.info("IdexLevelCalibration UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load IdexLevelCalibration UI file: {e}")

        # Initialize UI elements
        self.stacked_widget = self.findChild(QStackedWidget, "stackedWidget")
        self.page1 = self.findChild(QWidget, "idexConfigStep1Page")
        self.page2 = self.findChild(QWidget, "idexConfigStep2Page")
        self.page3 = self.findChild(QWidget, "idexConfigStep3Page")
        self.page4 = self.findChild(QWidget, "idexConfigStep4Page")
        self.page5 = self.findChild(QWidget, "idexConfigStep5Page")

        self.next_button1 = self.findChild(QPushButton, "idexConfigStep1NextButton")
        self.next_button2 = self.findChild(QPushButton, "idexConfigStep2NextButton")
        self.next_button3 = self.findChild(QPushButton, "idexConfigStep3NextButton")
        self.next_button4 = self.findChild(QPushButton, "idexConfigStep4NextButton")
        self.next_button5 = self.findChild(QPushButton, "idexConfigStep5NextButton")

        self.cancel_button1 = self.findChild(QPushButton, "idexConfigStep1CancelButton")
        self.cancel_button2 = self.findChild(QPushButton, "idexConfigStep2CancelButton")
        self.cancel_button3 = self.findChild(QPushButton, "idexConfigStep3CancelButton")
        self.cancel_button4 = self.findChild(QPushButton, "idexConfigStep4CancelButton")
        self.cancel_button5 = self.findChild(QPushButton, "idexConfigStep5CancelButton")

        # Validate UI elements
        check_ui_elements(self, [
            self.stacked_widget, self.page1, self.page2, self.page3, self.page4, self.page5,
            self.next_button1, self.next_button2, self.next_button3, self.next_button4, self.next_button5,
            self.cancel_button1, self.cancel_button2, self.cancel_button3, self.cancel_button4, self.cancel_button5
        ], "IDEX Level Calibration")

        # Connect buttons to their respective functions
        if self.next_button1:
            self.next_button1.clicked.connect(lambda: self._navigate_to_step(2))
        if self.next_button2:
            self.next_button2.clicked.connect(lambda: self._navigate_to_step(3))
        if self.next_button3:
            self.next_button3.clicked.connect(lambda: self._navigate_to_step(4))
        if self.next_button4:
            self.next_button4.clicked.connect(lambda: self._navigate_to_step(5))
        if self.next_button5:
            self.next_button5.clicked.connect(self._finish_calibration)

        if self.cancel_button1:
            self.cancel_button1.clicked.connect(self._cancel_calibration)
        if self.cancel_button2:
            self.cancel_button2.clicked.connect(self._cancel_calibration)
        if self.cancel_button3:
            self.cancel_button3.clicked.connect(self._cancel_calibration)
        if self.cancel_button4:
            self.cancel_button4.clicked.connect(self._cancel_calibration)
        if self.cancel_button5:
            self.cancel_button5.clicked.connect(self._cancel_calibration)

        # Set the default screen
        self.reset_wizard()


    def _navigate_to_step(self, step_number):
        """Navigate to a specific step in the calibration process"""
        target_page = getattr(self, f"page{step_number}", None)

        if self.stacked_widget and target_page:
            self.logger.info(f"Navigating to IDEX Calibration Step {step_number}")
            self.stacked_widget.setCurrentWidget(target_page)
        else:
            self.logger.error(f"Error: Cannot navigate to IDEX Calibration Step {step_number}")

    def _cancel_calibration(self):
        """Cancel the IDEX calibration process and return to main calibration page"""
        self.logger.info("IDEX Calibration process canceled")
        self._return_to_main_calibration()

    def _finish_calibration(self):
        """Finish the IDEX calibration process and return to main calibration page"""
        self.logger.info("IDEX Calibration process completed successfully")
        self._return_to_main_calibration()

    def _return_to_main_calibration(self):
        """Common method to return to the main calibration screen"""
        if hasattr(self.main_window, 'calibrate_screen'):
            if hasattr(self.main_window.calibrate_screen, 'calibration_stacked_widget') and \
               hasattr(self.main_window.calibrate_screen, 'main_calibrate_page'):
                self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                    self.main_window.calibrate_screen.main_calibrate_page)
                self.logger.info("Returned to main calibration page")
            else:
                self.logger.error("Cannot return to main calibration - required widgets not found")
        else:
            self.logger.error("Cannot return to main calibration - calibrate_screen not found")

    def reset_wizard(self):
        """Reset the IDEX Level Calibration wizard to its initial state."""
        self._navigate_to_step(1)
        self.logger.info("IDEX Level Calibration wizard reset to initial state")