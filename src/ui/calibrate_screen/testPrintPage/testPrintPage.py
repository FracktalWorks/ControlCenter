from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

class TestPrintPage(QWidget):
    """
    Test Print Page that provides various calibration print options for
    testing printer settings and alignment.
    """
    def __init__(self, main_window):
        super(TestPrintPage, self).__init__()
        self.main_window = main_window
        # Set up logger for this class
        self.logger = setup_logger('TestPrintPage')
        
        # Load the UI
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Connect signals to slots
        self._connect_buttons()

        # Set the default screen to second page
        self._navigate_to_page("testPrintPage2")

    def _load_ui(self):
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('src/ui/calibrate_screen/testPrintPage/testPrintPage.ui', self)
            self.logger.info("TestPrintPage UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load TestPrintPage UI file: {e}", exc_info=True)

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        # Container widgets
        self.container_widgets = {
            "stackedWidget": {"type": QStackedWidget, "instance": None}
        }
        
        # Pages in the stacked widget
        self.page_widgets = {
            "testPrintPage1": {"type": QWidget, "instance": None},
            "testPrintPage2": {"type": QWidget, "instance": None}
        }
        
        # Navigation buttons
        self.nav_buttons = {
            "testPrintsNextButton": {"type": QPushButton, "instance": None},
            "testPrintsBackButton": {"type": QPushButton, "instance": None},
            "testPrintsCancelButton": {"type": QPushButton, "instance": None}
        }
        
        # Print action buttons
        self.print_buttons = {
            "singleNozzlePrintButton": {"type": QPushButton, "instance": None},
            "movementTestPrintButton": {"type": QPushButton, "instance": None},
            "dualCaliberationPrintButton": {"type": QPushButton, "instance": None},
            "dualNozzlePrintButton": {"type": QPushButton, "instance": None},
            "bedLevelPrintButton": {"type": QPushButton, "instance": None}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.container_widgets)
        self.all_components.update(self.page_widgets)
        self.all_components.update(self.nav_buttons)
        self.all_components.update(self.print_buttons)
        
        # Find all components using the dictionary
        self._find_components()
        
        # Store reference to essential stacked widget for convenience
        self.stackedWidget = self.container_widgets["stackedWidget"]["instance"]

    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_type = component_info["type"]
            component = self.findChild(component_type, name)
            component_info["instance"] = component
            
            # Debug output
            if component:
                self.logger.debug(f"Found {component_type.__name__} '{name}'")
            else:
                self.logger.warning(f"Could not find {component_type.__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create mappings of component categories for reporting
        component_groups = {
            "TestPrintPage - Containers": {name: info["instance"] for name, info in self.container_widgets.items()},
            "TestPrintPage - Pages": {name: info["instance"] for name, info in self.page_widgets.items()},
            "TestPrintPage - Navigation Buttons": {name: info["instance"] for name, info in self.nav_buttons.items()},
            "TestPrintPage - Print Buttons": {name: info["instance"] for name, info in self.print_buttons.items()}
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)
    
    def _connect_buttons(self):
        """Connect buttons to their respective functions with safety checks"""
        # Navigation button for going to next screen
        next_button = self.nav_buttons.get("testPrintsNextButton", {}).get("instance")
        if next_button:
            next_button.clicked.connect(self.main_window.switch_to_next_screen)
            self.logger.debug("Connected next button to switch_to_next_screen")
        
        # Navigation buttons for going back/cancel
        back_button_names = ["testPrintsBackButton", "testPrintsCancelButton"]
        for button_name in back_button_names:
            button = self.nav_buttons.get(button_name, {}).get("instance")
            if button:
                button.clicked.connect(self._return_to_main_calibration)
                self.logger.debug(f"Connected {button_name} to return_to_main_calibration")
            else:
                self.logger.warning(f"Could not connect {button_name} - button not found")
        
        # Print action buttons - map button names to their handler methods
        button_handlers = {
            "singleNozzlePrintButton": self._single_nozzle_test_print,
            "movementTestPrintButton": self._movement_stress_test,
            "dualCaliberationPrintButton": self._dual_calibration_print,
            "dualNozzlePrintButton": self._dual_nozzle_test_print,
            "bedLevelPrintButton": self._bed_leveling_print
        }
        
        # Connect each print button to its handler
        for button_name, handler in button_handlers.items():
            button = self.print_buttons.get(button_name, {}).get("instance")
            if button:
                button.clicked.connect(handler)
                self.logger.debug(f"Connected {button_name} to its handler")
            else:
                self.logger.warning(f"Could not connect {button_name} - button not found")

    def _navigate_to_page(self, page_name):
        """Navigate to a specific page in the stackedWidget"""
        if not self.stackedWidget:
            self.logger.error("Cannot navigate - stacked widget is missing")
            return False
            
        target_page = self.page_widgets.get(page_name, {}).get("instance")
        if target_page:
            self.stackedWidget.setCurrentWidget(target_page)
            self.logger.debug(f"Navigating to {page_name}")
            return True
        else:
            self.logger.error(f"Cannot navigate to {page_name} - page not found")
            return False

    def _return_to_main_calibration(self):
        """Return to the main calibration page"""
        if hasattr(self.main_window, 'calibrate_screen'):
            # Use the standard navigation logic in CalibrateScreen
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            self.logger.info("Returning to main calibration page from test prints")
        else:
            self.logger.error("Cannot return to main calibration - main_window.calibrate_screen not found")

    # Print action methods
    def _single_nozzle_test_print(self):
        """Logic for single nozzle test print."""
        self.logger.info("Single Nozzle Test Print button clicked")
        # Actual implementation would send commands to the printer
        # Example: self.main_window.octoprint_client.print_file('single_nozzle_test.gcode')

    def _movement_stress_test(self):
        """Logic for movement stress test."""
        self.logger.info("Movement Stress Test button clicked")
        # Actual implementation would send commands to the printer

    def _dual_calibration_print(self):
        """Logic for dual calibration print."""
        self.logger.info("Dual Calibration Print button clicked")
        # Actual implementation would send commands to the printer

    def _dual_nozzle_test_print(self):
        """Logic for dual nozzle test print."""
        self.logger.info("Dual Nozzle Test Print button clicked")
        # Actual implementation would send commands to the printer

    def _bed_leveling_print(self):
        """Logic for bed leveling print."""
        self.logger.info("Bed Leveling Print button clicked")
        # Actual implementation would send commands to the printer