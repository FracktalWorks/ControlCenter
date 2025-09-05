import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils import dialog


class ZProbeOffsetPage(QWidget):
    """
    Z Probe Offset calibration widget that guides the user through Z probe offset calibration
    """

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.model = main_window.printer_model
        self.octoprint_client = main_window.octoprint_client
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing Z Probe Offset screen")

        try:
            # Use relative path from the current module's directory
            ui_file_path = os.path.join(os.path.dirname(__file__), "zProbeOffsetPage.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("ZProbeOffsetPage UI loaded successfully")
        except Exception as e:
            self.logger.exception(f"Failed to load ZProbeOffsetPage UI file: {e}")

        # Initialize the Pages
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.welcomePage = self.findChild(QWidget, "welcomePage")
        self.calibrationPage = self.findChild(QWidget, "calibrationPage")

        # Initialize buttons
        self.nextButton1 = self.findChild(QPushButton, "nextButton1")
        self.cancelButton1 = self.findChild(QPushButton, "cancelButton1")
        self.nextButton2 = self.findChild(QPushButton, "nextButton2")
        self.cancelButton2 = self.findChild(QPushButton, "cancelButton2")

        # Validate UI components
        check_ui_elements(self, [
            self.stackedWidget, self.welcomePage, self.calibrationPage,
            self.nextButton1, self.cancelButton1, self.nextButton2, self.cancelButton2
        ], "ZProbeOffsetPage")

        # Connect button signals
        if self.nextButton1:
            self.nextButton1.clicked.connect(self.next_page)
        if self.cancelButton1:
            self.cancelButton1.clicked.connect(self.cancel_calibration)
        if self.nextButton2:
            self.nextButton2.clicked.connect(self.finish_calibration)
        if self.cancelButton2:
            self.cancelButton2.clicked.connect(self.cancel_calibration)

        # Start with the welcome page
        if self.stackedWidget and self.welcomePage:
            self.stackedWidget.setCurrentWidget(self.welcomePage)

    def showEvent(self, event):
        """Reset to welcome page and home axes when this widget is shown."""
        super().showEvent(event)
        try:
            if self.stackedWidget and self.welcomePage:
                self.stackedWidget.setCurrentWidget(self.welcomePage)
            self.logger.info("Z Probe Offset calibration started - homing all axes")
            self.octoprint_client.home(['x', 'y', 'z'])
        except Exception as e:
            self.logger.error(f"Error in ZProbeOffsetPage showEvent: {e}")

    def next_page(self):
        """Move to the next page in the calibration wizard."""
        self.logger.info("ZProbeOffsetPage.next_page started")
        try:
            if self.stackedWidget and self.welcomePage and self.calibrationPage:
                if self.stackedWidget.currentWidget() == self.welcomePage:
                    self.stackedWidget.setCurrentWidget(self.calibrationPage)
                    self.logger.info("Moved to calibration page")
        except Exception as e:
            self.logger.error(f"Error in ZProbeOffsetPage.next_page: {e}")
            dialog.WarningOk(self, f"Error moving to next page: {str(e)}", overlay=True)

    def finish_calibration(self):
        """Finish the calibration and return to main calibration screen."""
        self.logger.info("ZProbeOffsetPage.finish_calibration started")
        try:
            # Add your calibration completion logic here
            self.octoprint_client.home(['x', 'y', 'z'])
            self.main_window.calibrate_screen.show_calibrate_screen()
        except Exception as e:
            self.logger.error(f"Error in ZProbeOffsetPage.finish_calibration: {e}")
            dialog.WarningOk(self, f"Error finishing calibration: {str(e)}", overlay=True)

    def cancel_calibration(self):
        """Cancel the calibration and return to main calibration screen."""
        self.logger.info("ZProbeOffsetPage.cancel_calibration started")
        try:
            self.octoprint_client.home(['x', 'y', 'z'])
            self.main_window.calibrate_screen.show_calibrate_screen()
        except Exception as e:
            self.logger.error(f"Error in ZProbeOffsetPage.cancel_calibration: {e}")
            dialog.WarningOk(self, f"Error canceling calibration: {str(e)}", overlay=True)
