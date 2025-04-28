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

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibrate_screen/toolOffset/toolOffset.ui', self)
            print("ToolOffset UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ToolOffset UI file: {e}")

        # Find stacked widget and pages
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        
        # Define UI elements by groups
        self.pages = {
            "toolOffsetXYPage": self.findChild(QWidget, 'toolOffsetXYPage'),
            "toolOffsetZPage": self.findChild(QWidget, 'toolOffsetZPage')
        }
        
        # Navigation buttons
        self.nav_buttons = {
            "toolOffsetXYBackButton": self.findChild(QPushButton, 'toolOffsetXYBackButton'),
            "toolOffsetZBackButton": self.findChild(QPushButton, 'toolOffsetZBackButton')
        }
        
        # Action buttons
        self.action_buttons = {
            "toolOffsetXSetButton": self.findChild(QPushButton, 'toolOffsetXSetButton'),
            "toolOffsetYSetButton": self.findChild(QPushButton, 'toolOffsetYSetButton'),
            "toolOffsetZSetButton": self.findChild(QPushButton, 'toolOffsetZSetButton')
        }
        
        # Value input spinboxes
        self.spin_boxes = {
            "toolOffsetXDoubleSpinBox": self.findChild(QDoubleSpinBox, 'toolOffsetXDoubleSpinBox'),
            "toolOffsetYDoubleSpinBox": self.findChild(QDoubleSpinBox, 'toolOffsetYDoubleSpinBox'),
            "toolOffsetZDoubleSpinBox": self.findChild(QDoubleSpinBox, 'toolOffsetZDoubleSpinBox')
        }

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions
        self._connect_buttons()

        # Set the default screen to toolOffsetXYPage
        self._navigate_to_page("toolOffsetXYPage")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        check_ui_elements(self, self.pages, "ToolOffset - Pages")
        check_ui_elements(self, self.nav_buttons, "ToolOffset - Navigation Buttons")
        check_ui_elements(self, self.action_buttons, "ToolOffset - Action Buttons")
        check_ui_elements(self, self.spin_boxes, "ToolOffset - Spin Boxes")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        # Back buttons
        for button_name, button in self.nav_buttons.items():
            if button:
                button.clicked.connect(self._return_to_main_calibration)
        
        # Action buttons - map button names to their handler methods
        button_handlers = {
            "toolOffsetXSetButton": self._set_tool_offset_x,
            "toolOffsetYSetButton": self._set_tool_offset_y,
            "toolOffsetZSetButton": self._set_tool_offset_z
        }
        
        # Connect each action button to its handler
        for button_name, handler in button_handlers.items():
            button = self.action_buttons.get(button_name)
            if button:
                button.clicked.connect(handler)

    def _navigate_to_page(self, page_name):
        """Navigate to a specific page in the stackedWidget"""
        target_page = self.pages.get(page_name)
        if self.stackedWidget and target_page:
            print(f"Navigating to {page_name}")
            self.stackedWidget.setCurrentWidget(target_page)
        else:
            print(f"Error: Cannot navigate to {page_name}")

    def _return_to_main_calibration(self):
        """Return to the main calibration page"""
        if hasattr(self.main_window, 'calibrate_screen'):
            # Use the standard navigation logic in CalibrateScreen
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            print("Returning to main calibration page from tool offset page")

    # Tool offset setting methods
    def _set_tool_offset_x(self):
        """Set the X offset for the tool."""
        if self.spin_boxes["toolOffsetXDoubleSpinBox"]:
            x_offset = self.spin_boxes["toolOffsetXDoubleSpinBox"].value()
            print(f"Tool X Offset set to: {x_offset} mm")
            # Actual implementation would send commands to the printer
            # Example: self.main_window.octoprint_client.set_tool_offset('X', x_offset)

    def _set_tool_offset_y(self):
        """Set the Y offset for the tool."""
        if self.spin_boxes["toolOffsetYDoubleSpinBox"]:
            y_offset = self.spin_boxes["toolOffsetYDoubleSpinBox"].value()
            print(f"Tool Y Offset set to: {y_offset} mm")
            # Actual implementation would send commands to the printer
            # Example: self.main_window.octoprint_client.set_tool_offset('Y', y_offset)

    def _set_tool_offset_z(self):
        """Set the Z offset for the tool."""
        if self.spin_boxes["toolOffsetZDoubleSpinBox"]:
            z_offset = self.spin_boxes["toolOffsetZDoubleSpinBox"].value()
            print(f"Tool Z Offset set to: {z_offset} mm")
            # Actual implementation would send commands to the printer
            # Example: self.main_window.octoprint_client.set_tool_offset('Z', z_offset)