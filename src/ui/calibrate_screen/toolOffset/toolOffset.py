from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QDoubleSpinBox, QStackedWidget
from utils.helpers import check_ui_elements

class ToolOffset(QWidget):
    def __init__(self, main_window):
        super(ToolOffset, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibrate_screen/toolOffset/toolOffset.ui', self)  # Updated path
            print("ToolOffset UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ToolOffset UI file: {e}")

        # Find buttons by their object names
        self.toolOffsetXYBackButton = self.findChild(QPushButton, 'toolOffsetXYBackButton')
        self.toolOffsetXSetButton = self.findChild(QPushButton, 'toolOffsetXSetButton')
        self.toolOffsetYSetButton = self.findChild(QPushButton, 'toolOffsetYSetButton')
        self.toolOffsetZSetButton = self.findChild(QPushButton, 'toolOffsetZSetButton')
        self.toolOffsetZBackButton = self.findChild(QPushButton, 'toolOffsetZBackButton')

        # Find spin boxes
        self.toolOffsetXDoubleSpinBox = self.findChild(QDoubleSpinBox, 'toolOffsetXDoubleSpinBox')
        self.toolOffsetYDoubleSpinBox = self.findChild(QDoubleSpinBox, 'toolOffsetYDoubleSpinBox')
        self.toolOffsetZDoubleSpinBox = self.findChild(QDoubleSpinBox, 'toolOffsetZDoubleSpinBox')

        # Find stacked widget and pages
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        self.toolOffsetXYPage = self.findChild(QWidget, 'toolOffsetXYPage')
        self.toolOffsetZPage = self.findChild(QWidget, 'toolOffsetZPage')

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions - with safety checks
        self._connect_buttons()

        # Set the default screen to toolOffsetXYPage
        if self.stackedWidget and self.toolOffsetXYPage:
            self.stackedWidget.setCurrentWidget(self.toolOffsetXYPage)

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Group widgets for better reporting
        pages = {
            "stackedWidget": self.stackedWidget,
            "toolOffsetXYPage": self.toolOffsetXYPage,
            "toolOffsetZPage": self.toolOffsetZPage
        }
        check_ui_elements(self, pages, "ToolOffset - Pages")
        
        buttons = {
            "toolOffsetXYBackButton": self.toolOffsetXYBackButton,
            "toolOffsetXSetButton": self.toolOffsetXSetButton,
            "toolOffsetYSetButton": self.toolOffsetYSetButton,
            "toolOffsetZSetButton": self.toolOffsetZSetButton,
            "toolOffsetZBackButton": self.toolOffsetZBackButton
        }
        check_ui_elements(self, buttons, "ToolOffset - Buttons")
        
        spin_boxes = {
            "toolOffsetXDoubleSpinBox": self.toolOffsetXDoubleSpinBox,
            "toolOffsetYDoubleSpinBox": self.toolOffsetYDoubleSpinBox,
            "toolOffsetZDoubleSpinBox": self.toolOffsetZDoubleSpinBox
        }
        check_ui_elements(self, spin_boxes, "ToolOffset - Spin Boxes")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        if self.toolOffsetXYBackButton:
            self.toolOffsetXYBackButton.clicked.connect(self._handle_back_button)

        if self.toolOffsetXSetButton:
            self.toolOffsetXSetButton.clicked.connect(self.set_tool_offset_x)

        if self.toolOffsetYSetButton:
            self.toolOffsetYSetButton.clicked.connect(self.set_tool_offset_y)

        if self.toolOffsetZSetButton:
            self.toolOffsetZSetButton.clicked.connect(self.set_tool_offset_z)

        if self.toolOffsetZBackButton:
            self.toolOffsetZBackButton.clicked.connect(self._handle_back_button)
            
    def _handle_back_button(self):
        """Return to the main calibration page when back button is pressed"""
        # Get the parent calibration screen from MainWindow and set to main page
        if hasattr(self.main_window, 'calibrate_screen'):
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            print("Returning to main calibration page from tool offset page")

    def set_tool_offset_x(self):
        """Set the X offset for the tool."""
        if self.toolOffsetXDoubleSpinBox:
            x_offset = self.toolOffsetXDoubleSpinBox.value()
            print(f"Tool X Offset set to: {x_offset} mm")
        else:
            print("X offset spin box not found")

    def set_tool_offset_y(self):
        """Set the Y offset for the tool."""
        if self.toolOffsetYDoubleSpinBox:
            y_offset = self.toolOffsetYDoubleSpinBox.value()
            print(f"Tool Y Offset set to: {y_offset} mm")
        else:
            print("Y offset spin box not found")

    def set_tool_offset_z(self):
        """Set the Z offset for the tool."""
        if self.toolOffsetZDoubleSpinBox:
            z_offset = self.toolOffsetZDoubleSpinBox.value()
            print(f"Tool Z Offset set to: {z_offset} mm")
        else:
            print("Z offset spin box not found")

    # def go_to_calibrate_page(self):
    #     """Navigate back to the CalibratePage."""
    #     print("Navigating back to CalibratePage")
    #     self.main_window.switch_to_calibrate_screen()