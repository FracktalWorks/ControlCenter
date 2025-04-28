from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QDoubleSpinBox, QLabel
from PyQt5.QtGui import QPalette, QColor
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

class NozzleOffsetPage(QWidget):
    """
    Nozzle Offset configuration page that allows users to adjust and set the
    offset values for the printer's nozzle.
    """
    def __init__(self, main_window):
        super(NozzleOffsetPage, self).__init__()
        self.main_window = main_window
        self.current_nozzle_offset = 0.0
        
        # Set up logger for this class
        self.logger = setup_logger('NozzleOffsetPage')
        self.logger.info("Initializing NozzleOffsetPage")

        # Load the UI
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions
        self._connect_buttons()

        # Initialize the current nozzle offset display
        self._update_current_nozzle_offset_label()

    def _load_ui(self):
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('src/ui/calibrate_screen/nozzleOffsetPage/nozzleOffsetPage.ui', self)
            self.logger.info("NozzleOffsetPage UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load NozzleOffsetPage UI file: {e}", exc_info=True)

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        self.logger.debug("Initializing UI components")
        # Navigation buttons 
        self.nav_buttons = {
            "nozzleOffsetBackButton": {"type": QPushButton, "instance": None}
        }
        
        # Action buttons
        self.action_buttons = {
            "nozzleOffsetSetButton": {"type": QPushButton, "instance": None}
        }
        
        # Input controls
        self.input_controls = {
            "nozzleOffsetDoubleSpinBox": {"type": QDoubleSpinBox, "instance": None},
            "currentNozzleOffsetLabel": {"type": QLabel, "instance": None}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.nav_buttons)
        self.all_components.update(self.action_buttons)
        self.all_components.update(self.input_controls)
        
        # Find all components using the dictionary
        self._find_components()

        # Apply readonly, disabled, and palette settings to the spinbox
        self._configure_spinbox()

    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_type = component_info["type"]
            
            # Special mapping for the current offset label which has a different name in the UI
            if name == "currentNozzleOffsetLabel":
                component = self.findChild(component_type, 'currentNozzleOffset_2')
            else:
                component = self.findChild(component_type, name)
                
            component_info["instance"] = component
            
            # Log component discovery
            if component:
                self.logger.debug(f"Found {component_type.__name__} '{name}'")
            else:
                self.logger.warning(f"Could not find {component_type.__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        self.logger.debug("Checking UI elements existence")
        # Create mappings of component categories for reporting
        component_groups = {
            "NozzleOffsetPage - Navigation Buttons": {name: info["instance"] for name, info in self.nav_buttons.items()},
            "NozzleOffsetPage - Action Buttons": {name: info["instance"] for name, info in self.action_buttons.items()},
            "NozzleOffsetPage - Input Controls": {name: info["instance"] for name, info in self.input_controls.items()}
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        self.logger.debug("Connecting button signals to slots")
        # Back button
        back_button = self.nav_buttons.get("nozzleOffsetBackButton", {}).get("instance")
        if back_button:
            back_button.clicked.connect(self._return_to_main_calibration)
            self.logger.debug("Connected back button to return_to_main_calibration")
        else:
            self.logger.warning("Could not connect back button - button not found")
        
        # Set button
        set_button = self.action_buttons.get("nozzleOffsetSetButton", {}).get("instance")
        if set_button:
            set_button.clicked.connect(self._set_nozzle_offset)
            self.logger.debug("Connected set button to set_nozzle_offset")
        else:
            self.logger.warning("Could not connect set button - button not found")
            
    def _return_to_main_calibration(self):
        """Return to the main calibration page when back button is pressed"""
        self.logger.info("Returning to main calibration page")
        if hasattr(self.main_window, 'calibrate_screen'):
            # Use the standard navigation logic in CalibrateScreen
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            self.logger.debug("Successfully switched to main calibration page")
        else:
            self.logger.error("Cannot return to main calibration - main_window.calibrate_screen not found")

    def _set_nozzle_offset(self):
        """Set the nozzle offset based on the value in the spin box."""
        spin_box = self.input_controls.get("nozzleOffsetDoubleSpinBox", {}).get("instance")
        if spin_box:
            self.current_nozzle_offset = spin_box.value()
            self.logger.info(f"Setting nozzle offset to: {self.current_nozzle_offset} mm")
            self._update_current_nozzle_offset_label()
            # Actual implementation would send commands to the printer
            # Example: self.main_window.octoprint_client.set_nozzle_offset(self.current_nozzle_offset)
        else:
            self.logger.error("Cannot set nozzle offset - spin box not found")

    def _update_current_nozzle_offset_label(self):
        """Update the label to display the current nozzle offset."""
        label = self.input_controls.get("currentNozzleOffsetLabel", {}).get("instance")
        if label:
            label.setText(f"{self.current_nozzle_offset:.2f} mm")
            self.logger.debug(f"Updated nozzle offset label to: {self.current_nozzle_offset:.2f} mm")
        else:
            self.logger.error("Cannot update nozzle offset label - label not found")

    def _configure_spinbox(self):
        """Configure the nozzle offset spinbox to be readonly, disabled, and styled."""
        spinbox = self.input_controls["nozzleOffsetDoubleSpinBox"].get("instance")

        if spinbox:
            spinbox.lineEdit().setReadOnly(True)
            spinbox.lineEdit().setDisabled(True)
            palette = QPalette()
            palette.setColor(QPalette.Highlight, QColor(40, 40, 40))
            spinbox.lineEdit().setPalette(palette)