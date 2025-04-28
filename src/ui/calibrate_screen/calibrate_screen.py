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

        # Load the UI
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Initialize all calibration sub-screens
        self._initialize_calibration_subscreens()
        
        # Connect buttons to their respective functions
        self._connect_buttons()
        
        # Make sure the main calibration page is shown initially
        self._show_main_page()

    def _load_ui(self):
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('src/ui/calibrate_screen/calibrate_screen.ui', self)
            print("CalibrateScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load CalibrateScreen UI file: {e}")

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        # Container widgets
        self.container_widgets = {
            "mainCalibrateStackedWidget": {"type": QStackedWidget, "instance": None},
            "mainCalibratePage": {"type": QWidget, "instance": None}
        }
        
        # Tool buttons for navigation to calibration sub-screens
        self.tool_buttons = {
            "calibrationWizardButton": {"type": QToolButton, "instance": None, "target": "bed_leveling"},
            "testPrintsButton": {"type": QToolButton, "instance": None, "target": "test_prints"},
            "inputShaperCalibrateButton": {"type": QToolButton, "instance": None, "target": "input_shaper"},
            "nozzleOffsetButton": {"type": QToolButton, "instance": None, "target": "nozzle_offset"},
            "toolOffsetZButton": {"type": QToolButton, "instance": None, "target": "tool_offset_z"},
            "toolOffsetXYButton": {"type": QToolButton, "instance": None, "target": "tool_offset_xy"},
            "idexCalibrationWizardButton": {"type": QToolButton, "instance": None, "target": "idex_calibration"}
        }
        
        # Push buttons for navigation controls
        self.push_buttons = {
            "calibrateBackButton": {"type": QPushButton, "instance": None, "target": "back"}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.container_widgets)
        self.all_components.update(self.tool_buttons)
        self.all_components.update(self.push_buttons)
        
        # Find all components using the dictionary
        self._find_components()
        
        # Store references to essential widgets for convenience
        self.calibration_stacked_widget = self.container_widgets["mainCalibrateStackedWidget"]["instance"]
        self.main_calibrate_page = self.container_widgets["mainCalibratePage"]["instance"]
        
        if not self.calibration_stacked_widget:
            print("ERROR: Could not find mainCalibrateStackedWidget in UI file")
        if not self.main_calibrate_page:
            print("ERROR: Could not find mainCalibratePage in UI file")
            
        print(f"Found main calibrate page: {self.main_calibrate_page}")

    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_type = component_info["type"]
            component = self.findChild(component_type, name)
            component_info["instance"] = component
            
            # Debug output
            if component:
                print(f"Found {component_type.__name__} '{name}'")
            else:
                print(f"WARNING: Could not find {component_type.__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create mappings of component categories for reporting
        component_groups = {
            "CalibrateScreen - Containers": {name: info["instance"] for name, info in self.container_widgets.items()},
            "CalibrateScreen - Tool Buttons": {name: info["instance"] for name, info in self.tool_buttons.items()},
            "CalibrateScreen - Push Buttons": {name: info["instance"] for name, info in self.push_buttons.items()}
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)

    def _initialize_calibration_subscreens(self):
        """Initialize all calibration sub-screens to be managed within this class"""
        if not self.calibration_stacked_widget:
            print("ERROR: Cannot initialize sub-screens - stacked widget is missing")
            return
            
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

        # Add this screen to the main window's stacked widget
        self.main_window.stacked_widget.addWidget(self)

    def _connect_buttons(self):
        """Connect buttons to their respective functions with safety checks"""
        # Connect tool buttons
        for name, info in self.tool_buttons.items():
            button = info["instance"]
            target = info["target"]
            
            if button:
                if target == "input_shaper":
                    button.clicked.connect(self._input_shaper_not_implemented)
                elif target == "tool_offset_z":
                    button.clicked.connect(self._show_tool_offset_z)
                elif target == "tool_offset_xy":
                    button.clicked.connect(self._show_tool_offset_xy)
                else:
                    button.clicked.connect(lambda checked=False, t=target: self.show_calibrate_screen(t))
                print(f"Connected {name} to handler for {target}")
        
        # Connect push buttons
        for name, info in self.push_buttons.items():
            button = info["instance"]
            target = info["target"]
            
            if button and target == "back":
                button.clicked.connect(self._handle_back_button)
                print(f"Connected {name} to back handler")

    def _show_main_page(self):
        """Show the main calibration page"""
        if self.calibration_stacked_widget and self.main_calibrate_page:
            self.calibration_stacked_widget.setCurrentWidget(self.main_calibrate_page)
            print("Set current widget to main_calibrate_page")

    def _input_shaper_not_implemented(self):
        """Print a message when inputShaperCalibrateButton is clicked"""
        print("Input Shaper Calibration not yet implemented")
        
    def _show_tool_offset_z(self):
        """Show the tool offset screen with Z tab selected"""
        self.show_calibrate_screen("tool_offset")
        # Access the tool offset screen and set it to show Z tab
        tool_offset_screen = self.screens.get("tool_offset")
        if tool_offset_screen and hasattr(tool_offset_screen, "stackedWidget") and hasattr(tool_offset_screen, "pages"):
            z_page = tool_offset_screen.pages.get("toolOffsetZPage")
            if tool_offset_screen.stackedWidget and z_page:
                tool_offset_screen.stackedWidget.setCurrentWidget(z_page)
                print("Showing Tool Offset Z tab")
    
    def _show_tool_offset_xy(self):
        """Show the tool offset screen with XY tab selected"""
        self.show_calibrate_screen("tool_offset")
        # Access the tool offset screen and set it to show XY tab
        tool_offset_screen = self.screens.get("tool_offset")
        if tool_offset_screen and hasattr(tool_offset_screen, "stackedWidget") and hasattr(tool_offset_screen, "pages"):
            xy_page = tool_offset_screen.pages.get("toolOffsetXYPage")
            if tool_offset_screen.stackedWidget and xy_page:
                tool_offset_screen.stackedWidget.setCurrentWidget(xy_page)
                print("Showing Tool Offset XY tab")

    def show_calibrate_screen(self, target_screen=None):
        """Show a specific calibration screen or the main calibration page

        Args:
            target_screen: Optional string identifying which sub-screen to navigate to.
                           None means show the main calibration page.
        """
        print(f"show_calibrate_screen called with target_screen={target_screen}")

        # Only switch to this screen in the main window if we're not already on it
        if self.main_window.current_screen != self:
            self.main_window.switch_screen(self)

        # If no specific target is requested, show the main calibration page
        if not target_screen or target_screen not in self.screens:
            self._show_main_page()
            print(f"Current widget is now: {self.calibration_stacked_widget.currentWidget().objectName()}")
            return

        # Navigate to the requested sub-screen
        screen = self.screens[target_screen]
        self.calibration_stacked_widget.setCurrentWidget(screen)
        print(f"Navigated to {target_screen}")

    def _handle_back_button(self):
        """Handle back button logic for CalibrateScreen"""
        if not self.calibration_stacked_widget or not self.main_calibrate_page:
            print("ERROR: Cannot handle back button - required widgets missing")
            return
            
        current_widget = self.calibration_stacked_widget.currentWidget()
        print(f"Back button pressed. Current widget: {current_widget.objectName()}")

        if current_widget == self.main_calibrate_page:
            # If we're on the main calibrate page, use navigation history to go back
            print("On main page, returning to previous screen")
            self.main_window.switch_to_previous_screen()
        else:
            # If we're on a sub-screen, return to the main calibrate page
            print(f"On sub-screen, returning to main calibration page")
            self.calibration_stacked_widget.setCurrentWidget(self.main_calibrate_page)
            print(f"After navigation: Current widget is now {self.calibration_stacked_widget.currentWidget().objectName()}")