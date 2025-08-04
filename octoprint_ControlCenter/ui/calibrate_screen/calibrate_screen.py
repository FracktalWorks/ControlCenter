import os
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton, QStackedWidget
from PyQt5 import uic
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils import dialog

# Import all calibration sub-screens
from ui.calibrate_screen.nozzleOffsetPage.nozzleOffsetPage import NozzleOffsetPage
from ui.calibrate_screen.toolOffset.toolOffset import ToolOffset
from ui.calibrate_screen.bedLevelingPage.bedLevelingPage import BedLeveling
from ui.calibrate_screen.testPrintPage.testPrintPage import TestPrintPage
from ui.calibrate_screen.idexLevelCalibration.idexLevelCalibration import IdexLevelCalibration


logger = get_logger(__name__)

class CalibrateScreen(QWidget):
    def __init__(self, main_window):
        super(CalibrateScreen, self).__init__()
        self.main_window = main_window
        self.logger = get_logger(self.__class__.__name__)

        # Load the UI
        try:
            ui_file_path = os.path.join(os.path.dirname(__file__), 'calibrate_screen.ui')
            uic.loadUi(ui_file_path, self)
            self.logger.info("CalibrateScreen UI loaded successfully")
        except Exception as e:
            self.logger.exception(f"Failed to load CalibrateScreen UI file: {e}")

        # Initialize UI components
        self.calibration_stacked_widget = self.findChild(QStackedWidget, "mainCalibrateStackedWidget")
        self.main_calibrate_page = self.findChild(QWidget, "mainCalibratePage")

        self.calibrationWizardButton = self.findChild(QToolButton, "calibrationWizardButton")
        self.testPrintsButton = self.findChild(QToolButton, "testPrintsButton")
        self.inputShaperCalibrateButton = self.findChild(QToolButton, "inputShaperCalibrateButton")
        self.nozzleOffsetButton = self.findChild(QToolButton, "nozzleOffsetButton")
        self.toolOffsetZButton = self.findChild(QToolButton, "toolOffsetZButton")
        self.toolOffsetXYButton = self.findChild(QToolButton, "toolOffsetXYButton")
        self.idexCalibrationWizardButton = self.findChild(QToolButton, "idexCalibrationWizardButton")

        self.calibrateBackButton = self.findChild(QPushButton, "calibrateBackButton")

        # Validate UI components
        check_ui_elements(self, [
            self.calibration_stacked_widget, self.main_calibrate_page,
            self.calibrationWizardButton, self.testPrintsButton, self.inputShaperCalibrateButton,
            self.nozzleOffsetButton, self.toolOffsetZButton, self.toolOffsetXYButton, self.idexCalibrationWizardButton,
            self.calibrateBackButton
        ], "CalibrateScreen")

        # Initialize all sub-screens
        self.screens = {}
        self._initialize_sub_screens()

        # Connect buttons to their respective methods
        if self.calibrationWizardButton:
            self.calibrationWizardButton.clicked.connect(lambda: self.navigate_to_bed_leveling())
        if self.testPrintsButton:
            self.testPrintsButton.clicked.connect(lambda: self.show_calibrate_screen("test_prints"))
        if self.inputShaperCalibrateButton:
            self.inputShaperCalibrateButton.clicked.connect(self.inputShaperCalibrate)
        if self.nozzleOffsetButton:
            self.nozzleOffsetButton.clicked.connect(lambda: self.show_calibrate_screen("nozzle_offset"))
        if self.toolOffsetZButton:
            self.toolOffsetZButton.clicked.connect(self._show_tool_offset_z)
        if self.toolOffsetXYButton:
            self.toolOffsetXYButton.clicked.connect(self._show_tool_offset_xy)
        if self.idexCalibrationWizardButton:
            self.idexCalibrationWizardButton.clicked.connect(self.navigate_to_idex_calibration)
        if self.calibrateBackButton:
            self.calibrateBackButton.clicked.connect(self._handle_back_button)

        # Show the main calibration page initially
        if self.calibration_stacked_widget and self.main_calibrate_page:
            self.calibration_stacked_widget.setCurrentWidget(self.main_calibrate_page)
            self.logger.debug("Set current widget to mainCalibratePage")

    def _initialize_sub_screens(self):
        """Initialize all calibration sub-screens"""
        try:
            # Create instances of each sub-screen
            self.screens["bed_leveling"] = BedLeveling(self.main_window)
            self.screens["nozzle_offset"] = NozzleOffsetPage(self.main_window)
            self.screens["tool_offset"] = ToolOffset(self.main_window)
            self.screens["test_prints"] = TestPrintPage(self.main_window)
            self.screens["idex_calibration"] = IdexLevelCalibration(self.main_window)

            # Add each screen to the stacked widget
            for name, screen in self.screens.items():
                self.calibration_stacked_widget.addWidget(screen)
                self.logger.info(f"Added {name} screen to calibration stacked widget")
        except Exception as e:
            self.logger.exception(f"Error initializing sub-screens: {e}")

    def inputShaperCalibrate(self):
        self.logger.info("MainUiClass.inputShaperCalibrate started")
        try:
            dialog.WarningOk(self, "Wait for all calibration movements to finish before proceeding.", overlay=True)
            self.main_window.octoprint_client.gcode(command='G28')
            self.main_window.octoprint_client.gcode(command='SHAPER_CALIBRATE')
            self.main_window.octoprint_client.gcode(command='SAVE_CONFIG')

        except Exception as e:
            error_message = f"Error in inptuShaperCalibrate: {str(e)}"
            self.logger.error(error_message)
            dialog.WarningOk(error_message, overlay=True)

    def _show_tool_offset_z(self):
        """Show the tool offset screen with Z tab selected"""
        self.show_calibrate_screen("tool_offset")
        # Access the tool offset screen and set it to show Z tab
        tool_offset_screen = self.screens.get("tool_offset")
        if tool_offset_screen and hasattr(tool_offset_screen, "stackedWidget"):
            if hasattr(tool_offset_screen, "toolOffsetZPage"):
                tool_offset_screen.stackedWidget.setCurrentWidget(tool_offset_screen.toolOffsetZPage)
                self.logger.debug("Showing Tool Offset Z tab")
            else:
                self.logger.error("Tool Offset Z page not found")

    def _show_tool_offset_xy(self):
        """Show the tool offset screen with XY tab selected"""
        self.show_calibrate_screen("tool_offset")
        # Access the tool offset screen and set it to show XY tab
        tool_offset_screen = self.screens.get("tool_offset")
        if tool_offset_screen and hasattr(tool_offset_screen, "stackedWidget"):
            if hasattr(tool_offset_screen, "toolOffsetXYPage"):
                tool_offset_screen.stackedWidget.setCurrentWidget(tool_offset_screen.toolOffsetXYPage)
                self.logger.debug("Showing Tool Offset XY tab")
            else:
                self.logger.error("Tool Offset XY page not found")

    def show_calibrate_screen(self, target_screen=None):
        """Show a specific calibration screen or the main calibration page

        Args:
            target_screen: Optional string identifying which sub-screen to navigate to.
                           None means show the main calibration page.
        """
        self.logger.debug(f"show_calibrate_screen called with target_screen={target_screen}")

        # Only switch to this screen in the main window if we're not already on it
        if self.main_window.current_screen != self:
            self.main_window.switch_screen(self)

        # If no specific target is requested, show the main calibration page
        if not target_screen:
            if self.calibration_stacked_widget and self.main_calibrate_page:
                self.calibration_stacked_widget.setCurrentWidget(self.main_calibrate_page)
                self.logger.debug("Showing main calibration page")
            return

        # Check if the requested screen exists
        if target_screen not in self.screens:
            self.logger.error(f"Requested screen '{target_screen}' not found in available screens")
            return

        # Navigate to the requested sub-screen
        screen = self.screens[target_screen]
        self.calibration_stacked_widget.setCurrentWidget(screen)
        self.logger.info(f"Navigated to {target_screen}")

    def _handle_back_button(self):
        """Handle back button logic for CalibrateScreen"""
        if not self.calibration_stacked_widget or not self.main_calibrate_page:
            logger.error("Cannot handle back button - required widgets missing")
            return

        current_widget = self.calibration_stacked_widget.currentWidget()
        self.logger.debug(
            f"Back button pressed. Current widget: {current_widget.objectName() if hasattr(current_widget, 'objectName') else 'unknown'}")

        if current_widget == self.main_calibrate_page:
            # If we're on the main calibrate page, use navigation history to go back
            self.logger.debug("On main page, returning to previous screen")
            self.main_window.switch_to_previous_screen()
        else:
            # If we're on a sub-screen, return to the main calibrate page
            self.logger.debug("On sub-screen, returning to main calibration page")
            self.calibration_stacked_widget.setCurrentWidget(self.main_calibrate_page)

    def navigate_to_bed_leveling(self):
        """Open the Bed Leveling screen and reset the wizard."""
        self.logger.info("Navigating to Bed Leveling screen")
        bed_leveling_screen = self.screens.get("bed_leveling")
        if bed_leveling_screen and hasattr(bed_leveling_screen, "reset_wizard"):
            bed_leveling_screen.reset_wizard()
        self.show_calibrate_screen("bed_leveling")
        bed_leveling_screen.quickStep1()

    def navigate_to_idex_calibration(self):
        """Open the IDEX Level Calibration screen and reset the wizard."""
        self.logger.info("Navigating to IDEX Level Calibration screen")
        idex_calibration_screen = self.screens.get("idex_calibration")
        if idex_calibration_screen and hasattr(idex_calibration_screen, "reset_wizard"):
            idex_calibration_screen.reset_wizard()
        self.show_calibrate_screen("idex_calibration")
        idex_calibration_screen.idexConfigStep1()
