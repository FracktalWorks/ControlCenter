from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QDoubleSpinBox, QStackedWidget

class ToolOffset(QWidget):
    def __init__(self, main_window):
        super(ToolOffset, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibratePage/toolOffset/toolOffset.ui', self)
            print("UI file loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

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
        self.toolOffsetZPage = self.findChild(QWidget, 'toolOffsetZpage')

        # Check if all elements are found
        if not all([
            self.toolOffsetXYBackButton, self.toolOffsetXSetButton, self.toolOffsetYSetButton,
            self.toolOffsetZSetButton, self.toolOffsetZBackButton, self.toolOffsetXDoubleSpinBox,
            self.toolOffsetYDoubleSpinBox, self.toolOffsetZDoubleSpinBox, self.stackedWidget,
            self.toolOffsetXYPage, self.toolOffsetZPage
        ]):
            raise ValueError("One or more UI elements not found in the UI file")

        # Connect buttons to their respective functions
        self.toolOffsetXYBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        self.toolOffsetXSetButton.clicked.connect(self.set_tool_offset_x)
        self.toolOffsetYSetButton.clicked.connect(self.set_tool_offset_y)
        self.toolOffsetZSetButton.clicked.connect(self.set_tool_offset_z)
        self.toolOffsetZBackButton.clicked.connect(self.go_to_xy_page)

        # Set the default screen to toolOffsetXYPage
        self.stackedWidget.setCurrentWidget(self.toolOffsetXYPage)

    def set_tool_offset_x(self):
        """Set the X offset for the tool."""
        x_offset = self.toolOffsetXDoubleSpinBox.value()
        print(f"Tool X Offset set to: {x_offset} mm")

    def set_tool_offset_y(self):
        """Set the Y offset for the tool."""
        y_offset = self.toolOffsetYDoubleSpinBox.value()
        print(f"Tool Y Offset set to: {y_offset} mm")

    def set_tool_offset_z(self):
        """Set the Z offset for the tool."""
        z_offset = self.toolOffsetZDoubleSpinBox.value()
        print(f"Tool Z Offset set to: {z_offset} mm")

    def go_to_xy_page(self):
        """Navigate back to the XY offset page."""
        print("Navigating to XY Offset Page")
        self.stackedWidget.setCurrentWidget(self.toolOffsetXYPage)