from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QDoubleSpinBox, QStackedWidget
from utils.helpers import check_ui_elements

class ToolOffset(QWidget):
    """
    Tool Offset configuration page that allows users to set the XY and Z offsets
    between multiple extruders for dual-extruder printers.
    """
    def __init__(self, main_window):
        super(ToolOffset, self).__init__()
        self.main_window = main_window

        # Load the UI
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Connect buttons to their respective functions
        self._connect_buttons()

        # Set the default screen to toolOffsetXYPage
        self._navigate_to_page("toolOffsetXYPage")

    def _load_ui(self):
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('src/ui/calibrate_screen/toolOffset/toolOffset.ui', self)
            print("ToolOffset UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ToolOffset UI file: {e}")

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        # Container widgets
        self.container_widgets = {
            "stackedWidget": {"type": QStackedWidget, "instance": None}
        }
        
        # Pages in the stacked widget
        self.page_widgets = {
            "toolOffsetXYPage": {"type": QWidget, "instance": None},
            "toolOffsetZPage": {"type": QWidget, "instance": None}
        }
        
        # Navigation buttons
        self.nav_buttons = {
            "toolOffsetXYBackButton": {"type": QPushButton, "instance": None},
            "toolOffsetZBackButton": {"type": QPushButton, "instance": None}
        }
        
        # Action buttons
        self.action_buttons = {
            "toolOffsetXSetButton": {"type": QPushButton, "instance": None},
            "toolOffsetYSetButton": {"type": QPushButton, "instance": None},
            "toolOffsetZSetButton": {"type": QPushButton, "instance": None}
        }
        
        # Value input spinboxes
        self.spin_boxes = {
            "toolOffsetXDoubleSpinBox": {"type": QDoubleSpinBox, "instance": None},
            "toolOffsetYDoubleSpinBox": {"type": QDoubleSpinBox, "instance": None},
            "toolOffsetZDoubleSpinBox": {"type": QDoubleSpinBox, "instance": None}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.container_widgets)
        self.all_components.update(self.page_widgets)
        self.all_components.update(self.nav_buttons)
        self.all_components.update(self.action_buttons)
        self.all_components.update(self.spin_boxes)
        
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
                print(f"Found {component_type.__name__} '{name}'")
            else:
                print(f"WARNING: Could not find {component_type.__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create mappings of component categories for reporting
        component_groups = {
            "ToolOffset - Containers": {name: info["instance"] for name, info in self.container_widgets.items()},
            "ToolOffset - Pages": {name: info["instance"] for name, info in self.page_widgets.items()},
            "ToolOffset - Navigation Buttons": {name: info["instance"] for name, info in self.nav_buttons.items()},
            "ToolOffset - Action Buttons": {name: info["instance"] for name, info in self.action_buttons.items()},
            "ToolOffset - Spin Boxes": {name: info["instance"] for name, info in self.spin_boxes.items()}
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)
    
    def _connect_buttons(self):
        """Connect buttons to their respective functions with safety checks"""
        # Back buttons
        for button_name, button_info in self.nav_buttons.items():
            button = button_info["instance"]
            if button:
                button.clicked.connect(self._return_to_main_calibration)
                print(f"Connected {button_name} to back handler")
        
        # Action buttons - map button names to their handler methods
        action_handlers = {
            "toolOffsetXSetButton": self._set_tool_offset_x,
            "toolOffsetYSetButton": self._set_tool_offset_y,
            "toolOffsetZSetButton": self._set_tool_offset_z
        }
        
        # Connect each action button to its handler
        for button_name, handler in action_handlers.items():
            button = self.action_buttons.get(button_name, {}).get("instance")
            if button:
                button.clicked.connect(handler)
                print(f"Connected {button_name} to its handler")
            else:
                print(f"WARNING: Could not connect {button_name} - button not found")

    def _navigate_to_page(self, page_name):
        """Navigate to a specific page in the stackedWidget"""
        if not self.stackedWidget:
            print("ERROR: Cannot navigate - stacked widget is missing")
            return False
            
        target_page = self.page_widgets.get(page_name, {}).get("instance")
        if target_page:
            self.stackedWidget.setCurrentWidget(target_page)
            print(f"Navigating to {page_name}")
            return True
        else:
            print(f"ERROR: Cannot navigate to {page_name} - page not found")
            return False

    def _return_to_main_calibration(self):
        """Return to the main calibration page"""
        if hasattr(self.main_window, 'calibrate_screen'):
            # Use the standard navigation logic in CalibrateScreen
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            print("Returning to main calibration page from tool offset page")
        else:
            print("ERROR: Cannot return to main calibration - main_window.calibrate_screen not found")

    # Tool offset setting methods
    def _set_tool_offset_x(self):
        """Set the X offset for the tool."""
        spin_box = self.spin_boxes.get("toolOffsetXDoubleSpinBox", {}).get("instance")
        if spin_box:
            x_offset = spin_box.value()
            print(f"Tool X Offset set to: {x_offset} mm")
            # Actual implementation would send commands to the printer
            # Example: self.main_window.octoprint_client.set_tool_offset('X', x_offset)
        else:
            print("ERROR: Cannot set X offset - spin box not found")

    def _set_tool_offset_y(self):
        """Set the Y offset for the tool."""
        spin_box = self.spin_boxes.get("toolOffsetYDoubleSpinBox", {}).get("instance")
        if spin_box:
            y_offset = spin_box.value()
            print(f"Tool Y Offset set to: {y_offset} mm")
            # Actual implementation would send commands to the printer
            # Example: self.main_window.octoprint_client.set_tool_offset('Y', y_offset)
        else:
            print("ERROR: Cannot set Y offset - spin box not found")

    def _set_tool_offset_z(self):
        """Set the Z offset for the tool."""
        spin_box = self.spin_boxes.get("toolOffsetZDoubleSpinBox", {}).get("instance")
        if spin_box:
            z_offset = spin_box.value()
            print(f"Tool Z Offset set to: {z_offset} mm")
            # Actual implementation would send commands to the printer
            # Example: self.main_window.octoprint_client.set_tool_offset('Z', z_offset)
        else:
            print("ERROR: Cannot set Z offset - spin box not found")