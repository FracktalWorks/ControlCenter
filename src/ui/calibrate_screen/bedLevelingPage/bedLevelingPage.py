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
        super(BedLeveling, self).__init__()
        self.main_window = main_window
        
        # Setup logger for bed leveling
        self.logger = setup_logger('bed_leveling')
        self.logger.info("Initializing Bed Leveling screen")

        # Load the UI
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions
        self._connect_buttons()

        # Set the default screen to nozzleHeightStep1Page
        self._navigate_to_page("nozzleHeightStep1Page")
        
        self.logger.info("Bed Leveling initialization complete")

    def _load_ui(self):
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('src/ui/calibrate_screen/bedLevelingPage/bedLevelingPage.ui', self)
            self.logger.info("BedLeveling UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load BedLeveling UI file: {e}")

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        # Page containers
        self.containers = {
            "stackedWidget": {"type": QStackedWidget, "instance": None}
        }
        
        # Pages
        self.pages = {
            "nozzleHeightStep1Page": {"type": QWidget, "instance": None},
            "quickStep1Page": {"type": QWidget, "instance": None},
            "quickStep2Page": {"type": QWidget, "instance": None},
            "quickStep3Page": {"type": QWidget, "instance": None},
            "quickStep4Page": {"type": QWidget, "instance": None}
        }
        
        # Height adjustment buttons (Step 1)
        self.height_adjustment_buttons = {
            "moveZPT1CaliberateButton": {"type": QPushButton, "instance": None},
            "moveZMT1CaliberateButton": {"type": QPushButton, "instance": None}
        }
        
        # Step 1 Navigation buttons
        self.step1_nav_buttons = {
            "nozzleHeightStep1NextButton": {"type": QPushButton, "instance": None},
            "nozzleHeightStep1CancelButton": {"type": QPushButton, "instance": None}
        }
        
        # Quick Step Navigation buttons
        self.quick_step_nav_buttons = {
            "quickStep1NextButton": {"type": QPushButton, "instance": None},
            "quickStep1CancelButton": {"type": QPushButton, "instance": None},
            "quickStep2NextButton": {"type": QPushButton, "instance": None},
            "quickStep2CancelButton": {"type": QPushButton, "instance": None},
            "quickStep3NextButton": {"type": QPushButton, "instance": None},
            "quickStep3CancelButton": {"type": QPushButton, "instance": None},
            "quickStep4NextButton": {"type": QPushButton, "instance": None},
            "quickStep4CancelButton": {"type": QPushButton, "instance": None}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.containers)
        self.all_components.update(self.pages)
        self.all_components.update(self.height_adjustment_buttons)
        self.all_components.update(self.step1_nav_buttons)
        self.all_components.update(self.quick_step_nav_buttons)
        
        # Find all components using the dictionary
        self._find_components()
        
        self.logger.info("Bed Leveling UI components initialized")

    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_info["instance"] = self.findChild(component_info["type"], name)
            
            # Debug output
            if component_info["instance"]:
                self.logger.debug(f"Found {component_info['type'].__name__} '{name}'")
            else:
                self.logger.warning(f"Could not find {component_info['type'].__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create mappings of component categories for reporting
        component_groups = {
            "BedLeveling - Containers": {name: info["instance"] for name, info in self.containers.items()},
            "BedLeveling - Pages": {name: info["instance"] for name, info in self.pages.items()},
            "BedLeveling - Height Adjustment Buttons": {name: info["instance"] for name, info in self.height_adjustment_buttons.items()},
            "BedLeveling - Step 1 Navigation Buttons": {name: info["instance"] for name, info in self.step1_nav_buttons.items()},
            "BedLeveling - Quick Step Navigation Buttons": {name: info["instance"] for name, info in self.quick_step_nav_buttons.items()}
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        # Movement control buttons
        zpt1_button = self.height_adjustment_buttons.get("moveZPT1CaliberateButton", {}).get("instance")
        if zpt1_button:
            zpt1_button.clicked.connect(self.move_z_pt1)
            self.logger.debug("Connected Z+0.1 button")

        zmt1_button = self.height_adjustment_buttons.get("moveZMT1CaliberateButton", {}).get("instance")
        if zmt1_button:
            zmt1_button.clicked.connect(self.move_z_mt1)
            self.logger.debug("Connected Z-0.1 button")

        # Navigation buttons - Step 1
        step1_next = self.step1_nav_buttons.get("nozzleHeightStep1NextButton", {}).get("instance")
        if step1_next:
            step1_next.clicked.connect(lambda: self._navigate_to_page("quickStep1Page"))
            self.logger.debug("Connected Step 1 Next button")

        step1_cancel = self.step1_nav_buttons.get("nozzleHeightStep1CancelButton", {}).get("instance")
        if step1_cancel:
            step1_cancel.clicked.connect(self._return_to_main_calibration)
            self.logger.debug("Connected Step 1 Cancel button")

        # Navigation buttons - Quick Steps
        steps = [
            ("quickStep1NextButton", "quickStep2Page"),
            ("quickStep2NextButton", "quickStep3Page"),
            ("quickStep3NextButton", "quickStep4Page"),
            ("quickStep4NextButton", None)  # None will trigger finish_bed_leveling
        ]
        
        for button_name, next_page in steps:
            button = self.quick_step_nav_buttons.get(button_name, {}).get("instance")
            if button:
                if next_page:
                    button.clicked.connect(
                        lambda checked=False, page=next_page: self._navigate_to_page(page))
                    self.logger.debug(f"Connected {button_name} to navigate to {next_page}")
                else:
                    button.clicked.connect(self._finish_bed_leveling)
                    self.logger.debug(f"Connected {button_name} to finish bed leveling")
            else:
                self.logger.warning(f"Could not connect {button_name} - button not found")
        
        # Cancel buttons - all quick steps
        cancel_buttons = [
            "quickStep1CancelButton",
            "quickStep2CancelButton",
            "quickStep3CancelButton",
            "quickStep4CancelButton"
        ]
        
        for button_name in cancel_buttons:
            button = self.quick_step_nav_buttons.get(button_name, {}).get("instance")
            if button:
                button.clicked.connect(self._return_to_main_calibration)
                self.logger.debug(f"Connected {button_name} to return to main calibration")
            else:
                self.logger.warning(f"Could not connect {button_name} - button not found")
        
        self.logger.info("Bed Leveling buttons connected")

    def _navigate_to_page(self, page_name):
        """Navigate to a specific page in the stackedWidget"""
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance")
        target_page = self.pages.get(page_name, {}).get("instance")
        
        if stacked_widget and target_page:
            self.logger.info(f"Navigating to {page_name}")
            stacked_widget.setCurrentWidget(target_page)
        else:
            self.logger.error(f"Cannot navigate to {page_name} - widget or page not found")

    def _return_to_main_calibration(self):
        """Cancel bed leveling process and return to main calibration page"""
        self.logger.info("Bed leveling process canceled by user")
        if hasattr(self.main_window, 'calibrate_screen'):
            # Use standard navigation logic in CalibrateScreen
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            self.logger.info("Returning to main calibration page from bed leveling")
        else:
            self.logger.error("Cannot return to main calibration - main_window.calibrate_screen not found")

    def _finish_bed_leveling(self):
        """Finish bed leveling process and return to main calibration page"""
        self.logger.info("Bed leveling process completed successfully")
        self._return_to_main_calibration()

    # Motion control methods
    def move_z_pt1(self):
        """Move Z-axis to positive direction for calibration"""
        self.logger.info("Moving Z-axis +0.1mm for calibration")
        # Actual implementation would send commands to the printer
        # Example: self.main_window.octoprint_client.move_z(amount=0.1)

    def move_z_mt1(self):
        """Move Z-axis to negative direction for calibration"""
        self.logger.info("Moving Z-axis -0.1mm for calibration")
        # Actual implementation would send commands to the printer
        # Example: self.main_window.octoprint_client.move_z(amount=-0.1)