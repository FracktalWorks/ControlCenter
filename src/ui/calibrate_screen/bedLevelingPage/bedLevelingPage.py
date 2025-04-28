from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

class BedLeveling(QWidget):
    """
    Bed Leveling widget that guides the user through the bed leveling calibration process
    with a multi-step wizard interface.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.logger = setup_logger('bed_leveling')
        self.logger.info("Initializing Bed Leveling screen")

        try:
            uic.loadUi('src/ui/calibrate_screen/bedLevelingPage/bedLevelingPage.ui', self)
            self.logger.info("BedLeveling UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load BedLeveling UI file: {e}")


        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.nozzleHeightStep1Page = self.findChild(QWidget, "nozzleHeightStep1Page")
        self.quickStep1Page = self.findChild(QWidget, "quickStep1Page")
        self.quickStep2Page = self.findChild(QWidget, "quickStep2Page")
        self.quickStep3Page = self.findChild(QWidget, "quickStep3Page")
        self.quickStep4Page = self.findChild(QWidget, "quickStep4Page")

        self.moveZPT1CaliberateButton = self.findChild(QPushButton, "moveZPT1CaliberateButton")
        self.moveZMT1CaliberateButton = self.findChild(QPushButton, "moveZMT1CaliberateButton")
        self.nozzleHeightStep1NextButton = self.findChild(QPushButton, "nozzleHeightStep1NextButton")
        self.nozzleHeightStep1CancelButton = self.findChild(QPushButton, "nozzleHeightStep1CancelButton")
        self.quickStep1NextButton = self.findChild(QPushButton, "quickStep1NextButton")
        self.quickStep1CancelButton = self.findChild(QPushButton, "quickStep1CancelButton")
        self.quickStep2NextButton = self.findChild(QPushButton, "quickStep2NextButton")
        self.quickStep2CancelButton = self.findChild(QPushButton, "quickStep2CancelButton")
        self.quickStep3NextButton = self.findChild(QPushButton, "quickStep3NextButton")
        self.quickStep3CancelButton = self.findChild(QPushButton, "quickStep3CancelButton")
        self.quickStep4NextButton = self.findChild(QPushButton, "quickStep4NextButton")
        self.quickStep4CancelButton = self.findChild(QPushButton, "quickStep4CancelButton")

        # Validate UI elements
        check_ui_elements(self, [
            self.stackedWidget, self.nozzleHeightStep1Page, self.quickStep1Page, self.quickStep2Page, self.quickStep3Page, self.quickStep4Page,
            self.moveZPT1CaliberateButton, self.moveZMT1CaliberateButton, self.nozzleHeightStep1NextButton, self.nozzleHeightStep1CancelButton,
            self.quickStep1NextButton, self.quickStep1CancelButton, self.quickStep2NextButton, self.quickStep2CancelButton,
            self.quickStep3NextButton, self.quickStep3CancelButton, self.quickStep4NextButton, self.quickStep4CancelButton
        ], "BedLeveling")

        if self.moveZPT1CaliberateButton:
            self.moveZPT1CaliberateButton.clicked.connect(self.move_z_pt1)
        if self.moveZMT1CaliberateButton:
            self.moveZMT1CaliberateButton.clicked.connect(self.move_z_mt1)
        if self.nozzleHeightStep1NextButton:
            self.nozzleHeightStep1NextButton.clicked.connect(lambda: self._navigate_to_page(self.quickStep1Page))
        if self.nozzleHeightStep1CancelButton:
            self.nozzleHeightStep1CancelButton.clicked.connect(self._return_to_main_calibration)
        if self.quickStep1NextButton:
            self.quickStep1NextButton.clicked.connect(lambda: self._navigate_to_page(self.quickStep2Page))
        if self.quickStep2NextButton:
            self.quickStep2NextButton.clicked.connect(lambda: self._navigate_to_page(self.quickStep3Page))
        if self.quickStep3NextButton:
            self.quickStep3NextButton.clicked.connect(lambda: self._navigate_to_page(self.quickStep4Page))
        if self.quickStep4NextButton:
            self.quickStep4NextButton.clicked.connect(self._finish_bed_leveling)
        if self.quickStep1CancelButton:
            self.quickStep1CancelButton.clicked.connect(self._return_to_main_calibration)
        if self.quickStep2CancelButton:
            self.quickStep2CancelButton.clicked.connect(self._return_to_main_calibration)
        if self.quickStep3CancelButton:
            self.quickStep3CancelButton.clicked.connect(self._return_to_main_calibration)
        if self.quickStep4CancelButton:
            self.quickStep4CancelButton.clicked.connect(self._return_to_main_calibration)
        
        # Initialize to the first page
        self.reset_wizard()
        self.logger.info("Bed Leveling initialization complete")

    def _navigate_to_page(self, page):
        """Navigate to a specific page within the bed leveling wizard"""
        if self.stackedWidget and page:
            self.logger.info(f"Navigating to {page.objectName()}")
            self.stackedWidget.setCurrentWidget(page)
        else:
            self.logger.error(f"Cannot navigate - stackedWidget or page is missing")

    def _return_to_main_calibration(self):
        """Return to the main calibration page"""
        self.logger.info("Bed leveling process canceled by user")
        if hasattr(self.main_window, 'calibrate_screen'):
            if hasattr(self.main_window.calibrate_screen, 'calibration_stacked_widget') and \
               hasattr(self.main_window.calibrate_screen, 'main_calibrate_page'):
                self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                    self.main_window.calibrate_screen.main_calibrate_page)
                self.logger.info("Returning to main calibration page")
            else:
                self.logger.error("Cannot return to main calibration - required widgets not found")
        else:
            self.logger.error("Cannot return to main calibration - calibrate_screen not found")

    def _finish_bed_leveling(self):
        """Complete the bed leveling process and return to main calibration"""
        self.logger.info("Bed leveling process completed successfully")
        self._return_to_main_calibration()

    def move_z_pt1(self):
        """Move Z-axis +0.1mm for calibration"""
        self.logger.info("Moving Z-axis +0.1mm for calibration")

    def move_z_mt1(self):
        """Move Z-axis -0.1mm for calibration"""
        self.logger.info("Moving Z-axis -0.1mm for calibration")

    def reset_wizard(self):
        """Reset the wizard to the first page"""
        if self.stackedWidget and self.quickStep1Page:
            self.stackedWidget.setCurrentWidget(self.quickStep1Page)
            self.logger.info("Bed Leveling wizard reset to initial state")
        else:
            self.logger.error("Cannot reset wizard - required widgets not found")