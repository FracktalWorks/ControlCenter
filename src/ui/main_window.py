from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from ui.home_screen.home_screen import HomeScreen
from ui.loading_screen.loading_screen import LoadingScreen
from ui.menu_screen.menu_screen import MenuScreen
from ui.settings_screen.settings_screen import SettingsScreen
from ui.control_screen.control_screen import ControlScreen
from ui.print_from_location.print_from_location import PrintFromLocation
from ui.changeFilament.changeFilament import ChangeFilament
from ui.calibrate_screen.calibrate_screen import CalibrateScreen
from ui.calibrate_screen.nozzleOffsetPage.nozzleOffsetPage import NozzleOffsetPage
from ui.calibrate_screen.toolOffset.toolOffset import ToolOffset
from ui.calibrate_screen.bedLevelingPage.bedLevelingPage import BedLeveling
from ui.calibrate_screen.idexLevelCalibration.idexLevelCalibration import IdexLevelCalibration
from ui.calibrate_screen.testPrintPage.testPrintPage import TestPrintPage
import ui.resources.resource_rc  # Ensure resources are loaded

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # Screen navigation history for back button functionality
        self.screen_history = []
        self.current_screen = None
        
        # Next screen for wizard-style multi-step flows
        self.next_screen = None

        # Load all screens
        self.load_home_screen()
        self.load_loading_screen()
        self.load_menu_screen()
        self.load_settings_screen()
        self.load_control_screen()
        self.load_print_location_screen()
        self.load_change_filament_screen()
        self.load_calibration_screens()

        # Start with the loading screen
        self.switch_screen(self.loading_screen)

        # Adjust the size of the main window to fit its contents
        self.adjustSize()

    # Screen Loading Methods
    def load_home_screen(self):
        self.home_screen = HomeScreen(self)
        self.stacked_widget.addWidget(self.home_screen)

    def load_loading_screen(self):
        self.loading_screen = LoadingScreen(self)
        self.stacked_widget.addWidget(self.loading_screen)

    def load_menu_screen(self):
        self.menu_screen = MenuScreen(self)
        self.stacked_widget.addWidget(self.menu_screen)

    def load_settings_screen(self):
        self.settings_screen = SettingsScreen(self)
        self.stacked_widget.addWidget(self.settings_screen)

    def load_control_screen(self):
        self.control_screen = ControlScreen(self)
        self.stacked_widget.addWidget(self.control_screen)

    def load_print_location_screen(self):
        self.print_location_screen = PrintFromLocation(self)
        self.stacked_widget.addWidget(self.print_location_screen)

    def load_change_filament_screen(self):
        self.change_filament_screen = ChangeFilament(self)
        self.stacked_widget.addWidget(self.change_filament_screen)

    def load_calibration_screens(self):
        # Main calibration screen
        self.calibrate_screen = CalibrateScreen(self)
        self.stacked_widget.addWidget(self.calibrate_screen)

        # Calibration sub-screens
        self.nozzle_offset_screen = NozzleOffsetPage(self)
        self.stacked_widget.addWidget(self.nozzle_offset_screen)

        self.tool_offset_screen = ToolOffset(self)
        self.stacked_widget.addWidget(self.tool_offset_screen)
        
        self.bed_leveling_screen = BedLeveling(self)
        self.stacked_widget.addWidget(self.bed_leveling_screen)
        
        self.idex_calibration_screen = IdexLevelCalibration(self)
        self.stacked_widget.addWidget(self.idex_calibration_screen)
        
        self.test_print_screen = TestPrintPage(self)
        self.stacked_widget.addWidget(self.test_print_screen)

    # Screen Navigation Methods
    def switch_screen(self, widget):
        """Switch to the given screen and update navigation history."""
        print(f"Switching to screen: {widget.__class__.__name__}")
        print(f"Current screen before switch: {self.current_screen.__class__.__name__ if self.current_screen else None}")
        
        if self.current_screen is not None:
            self.screen_history.append(self.current_screen)
            print(f"Added {self.current_screen.__class__.__name__} to history")
        
        self.current_screen = widget
        self.stacked_widget.setCurrentWidget(widget)
        
        print(f"History now contains: {[screen.__class__.__name__ for screen in self.screen_history]}")

    def switch_to_previous_screen(self):
        """Go back to the previous screen in history."""
        if self.screen_history:
            previous_screen = self.screen_history.pop()
            self.current_screen = previous_screen
            self.stacked_widget.setCurrentWidget(previous_screen)
        else:
            # Default to home screen if no history exists
            self.switch_to_home_screen()

        # Ensure the stacked widget's current page is updated for multi-step wizards
        if hasattr(self.current_screen, 'stackedWidget') and self.current_screen.stackedWidget:
            self.current_screen.stackedWidget.setCurrentIndex(0)
            
    def switch_to_next_screen(self):
        """Used in multi-step flows like wizards to go to the next screen."""
        if self.next_screen:
            self.switch_screen(self.next_screen)
            self.next_screen = None
        else:
            # If no next screen is defined, do nothing or go to a default
            print("No next screen defined")

    # Direct navigation methods for main screens
    def switch_to_home_screen(self):
        self.switch_screen(self.home_screen)

    def switch_to_loading_screen(self):
        self.switch_screen(self.loading_screen)

    def switch_to_menu_screen(self):
        self.switch_screen(self.menu_screen)

    def switch_to_settings_screen(self):
        self.switch_screen(self.settings_screen)

    def switch_to_control_screen(self):
        self.switch_screen(self.control_screen)

    def switch_to_print_location_screen(self):
        self.switch_screen(self.print_location_screen)

    def switch_to_change_filament_screen(self):
        self.switch_screen(self.change_filament_screen)

    # Calibration screen navigation methods
    def switch_to_calibrate_screen(self):
        self.switch_screen(self.calibrate_screen)

    def switch_to_nozzle_offset(self):
        self.switch_screen(self.nozzle_offset_screen)

    def switch_to_tool_offset_xy(self):
        self.switch_screen(self.tool_offset_screen)
        self.tool_offset_screen.stackedWidget.setCurrentWidget(self.tool_offset_screen.toolOffsetXYPage)

    def switch_to_tool_offset_z(self):
        self.switch_screen(self.tool_offset_screen)
        self.tool_offset_screen.stackedWidget.setCurrentWidget(self.tool_offset_screen.toolOffsetZPage)

    def switch_to_bed_leveling(self):
        self.switch_screen(self.bed_leveling_screen)

    def switch_to_idex_calibration_wizard(self):
        self.switch_screen(self.idex_calibration_screen)

    def switch_to_test_prints(self):
        self.switch_screen(self.test_print_screen)

    def switch_to_input_shaper_calibration(self):
        # Placeholder if you implement this screen later
        print("Input Shaper Calibration not yet implemented")
        # self.switch_screen(self.input_shaper_screen)



