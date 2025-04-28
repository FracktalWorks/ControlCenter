from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton, QStackedWidget
from PyQt5 import uic
from utils.helpers import check_ui_elements

# Import all calibration sub-screens
from ui.calibrate_screen.nozzleOffsetPage.nozzleOffsetPage import NozzleOffsetPage
from ui.calibrate_screen.toolOffset.toolOffset import ToolOffset
from ui.calibrate_screen.bedLevelingPage.bedLevelingPage import BedLeveling
from ui.calibrate_screen.testPrintPage.testPrintPage import TestPrintPage
from ui.calibrate_screen.idexLevelCalibration.idexLevelCalibration import IdexLevelCalibration

class CalibrateScreen(QWidget):
    def __init__(self, main_window):
        super(CalibrateScreen, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibrate_screen/calibrate_screen.ui', self)
            print("CalibrateScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load CalibrateScreen UI file: {e}")

        # Get the built-in stacked widget from UI
        self.calibration_stacked_widget = self.findChild(QStackedWidget, "mainCalibrateStackedWidget")
        if not self.calibration_stacked_widget:
            print("ERROR: Could not find mainCalibrateStackedWidget in UI file")
            return

        # Find the main page within the stacked widget
        self.main_calibrate_page = self.findChild(QWidget, "mainCalibratePage")
        if not self.main_calibrate_page:
            print("ERROR: Could not find mainCalibratePage in UI file")
            return

        print(f"Found main calibrate page: {self.main_calibrate_page}")

        # Initialize buttons by finding them in the UI
        self.buttons = {
            "calibrationWizardButton": "bed_leveling",
            "testPrintsButton": "test_prints",
            "inputShaperCalibrateButton": "input_shaper",
            "nozzleOffsetButton": "nozzle_offset",
            "toolOffsetZButton": "tool_offset",  # Changed from tool_offset_z to tool_offset
            "toolOffsetXYButton": "tool_offset", # Changed from tool_offset_xy to tool_offset
            "idexCalibrationWizardButton": "idex_calibration",
            "calibrateBackButton": "back"
        }

        self.ui_buttons = {name: self.findChild(QToolButton, name) for name in self.buttons.keys()}

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Initialize all calibration sub-screens
        self.screens = {}
        self._initialize_calibration_subscreens()

        # Connect buttons to their respective functions dynamically
        self._connect_buttons()

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        check_ui_elements(self, self.ui_buttons, "CalibrateScreen")

    def _initialize_calibration_subscreens(self):
        """Initialize all calibration sub-screens to be managed within this class"""
        self.screens = {
            "nozzle_offset": NozzleOffsetPage(self.main_window),
            "tool_offset": ToolOffset(self.main_window),
            "bed_leveling": BedLeveling(self.main_window),
            "test_prints": TestPrintPage(self.main_window),
            "idex_calibration": IdexLevelCalibration(self.main_window)
        }

        for name, screen in self.screens.items():
            screen.setObjectName(name)
            self.calibration_stacked_widget.addWidget(screen)

        print(f"Stacked widget has {self.calibration_stacked_widget.count()} pages")
        for i in range(self.calibration_stacked_widget.count()):
            widget = self.calibration_stacked_widget.widget(i)
            print(f"Page {i}: {widget.objectName()}")

        # Make sure the main calibration page is shown initially
        self.calibration_stacked_widget.setCurrentWidget(self.main_calibrate_page)

        # Add this screen to the main window's stacked widget
        self.main_window.stacked_widget.addWidget(self)

    def _connect_buttons(self):
        """Connect buttons dynamically to their respective navigation logic"""
        for button_name, target_screen in self.buttons.items():
            button = self.ui_buttons.get(button_name)
            if button:
                if target_screen == "back":
                    button.clicked.connect(self._handle_back_button)
                elif target_screen == "input_shaper":
                    # Just add a print statement for the inputShaperCalibrateButton
                    button.clicked.connect(self._input_shaper_not_implemented)
                elif button_name == "toolOffsetZButton":
                    # For tool offset Z, make sure it goes to the right tab
                    button.clicked.connect(self._show_tool_offset_z)
                elif button_name == "toolOffsetXYButton":
                    # For tool offset XY, make sure it goes to the right tab
                    button.clicked.connect(self._show_tool_offset_xy)
                else:
                    button.clicked.connect(lambda _, ts=target_screen: self.show_calibrate_screen(ts))
                print(f"Connected {button_name} to {target_screen}")

    def _input_shaper_not_implemented(self):
        """Print a message when inputShaperCalibrateButton is clicked"""
        print("Input Shaper Calibration not yet implemented")
        
    def _show_tool_offset_z(self):
        """Show the tool offset screen with Z tab selected"""
        self.show_calibrate_screen("tool_offset")
        # Access the tool offset screen and set it to show Z tab
        tool_offset_screen = self.screens.get("tool_offset")
        if tool_offset_screen and hasattr(tool_offset_screen, "stackedWidget"):
            print("Showing Tool Offset Z tab")
            tool_offset_screen.stackedWidget.setCurrentWidget(tool_offset_screen.toolOffsetZPage)
    
    def _show_tool_offset_xy(self):
        """Show the tool offset screen with XY tab selected"""
        self.show_calibrate_screen("tool_offset")
        # Access the tool offset screen and set it to show XY tab
        tool_offset_screen = self.screens.get("tool_offset")
        if tool_offset_screen and hasattr(tool_offset_screen, "stackedWidget"):
            print("Showing Tool Offset XY tab")
            tool_offset_screen.stackedWidget.setCurrentWidget(tool_offset_screen.toolOffsetXYPage)

    def show_calibrate_screen(self, target_screen=None):
        """Show a specific calibration screen or the main calibration page

        Args:
            target_screen: Optional string identifying which sub-screen to navigate to.
                           None means show the main calibration page.
        """
        print(f"show_calibrate_screen called with target_screen={target_screen}")

        # First, make sure we're showing this screen in the main window
        self.main_window.switch_screen(self)

        # If no specific target is requested, show the main calibration page
        if not target_screen or target_screen not in self.screens:
            print("Setting current widget to main_calibrate_page")
            self.calibration_stacked_widget.setCurrentWidget(self.main_calibrate_page)
            print(f"Current widget is now: {self.calibration_stacked_widget.currentWidget().objectName()}")
            return

        # Navigate to the requested sub-screen
        screen = self.screens[target_screen]
        self.calibration_stacked_widget.setCurrentWidget(screen)
        print(f"Navigated to {target_screen}")

    def _handle_back_button(self):
        """Handle back button logic for CalibrateScreen"""
        current_widget = self.calibration_stacked_widget.currentWidget()
        print(f"Back button pressed. Current widget: {current_widget.objectName()}")

        if current_widget == self.main_calibrate_page:
            # If we're on the main calibrate page, go back to menu
            print("On main page, returning to menu screen")
            self.main_window.switch_to_menu_screen()
        else:
            # If we're on a sub-screen, return to the main calibrate page
            print(f"On sub-screen, returning to main calibration page")
            self.calibration_stacked_widget.setCurrentWidget(self.main_calibrate_page)
            print(f"After navigation: Current widget is now {self.calibration_stacked_widget.currentWidget().objectName()}")