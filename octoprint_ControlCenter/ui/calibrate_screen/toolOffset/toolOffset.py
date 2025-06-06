from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QDoubleSpinBox, QStackedWidget
from PyQt5.QtGui import QPalette, QColor
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

class ToolOffset(QWidget):
    """
    Tool Offset configuration page that allows users to set the XY and Z offsets
    between multiple extruders for dual-extruder printers.
    """
    def __init__(self, main_window):
        super(ToolOffset, self).__init__()
        self.main_window = main_window
        # Properly initialize logger with a distinct name
        self.logger = setup_logger('ToolOffset')
        self.logger.info("Initializing ToolOffset page")

        # Load the UI
        try:
            uic.loadUi('/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/calibrate_screen/toolOffset/toolOffset.ui', self)
            self.logger.info("ToolOffset UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load ToolOffset UI file: {e}")

    # Initialize UI components
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.toolOffsetXYPage = self.findChild(QWidget, "toolOffsetXYPage")
        self.toolOffsetZPage = self.findChild(QWidget, "toolOffsetZPage")
        self.toolOffsetXYBackButton = self.findChild(QPushButton, "toolOffsetXYBackButton")
        self.toolOffsetZBackButton = self.findChild(QPushButton, "toolOffsetZBackButton")
        self.toolOffsetXSetButton = self.findChild(QPushButton, "toolOffsetXSetButton")
        self.toolOffsetYSetButton = self.findChild(QPushButton, "toolOffsetYSetButton")
        self.toolOffsetZSetButton = self.findChild(QPushButton, "toolOffsetZSetButton")
        self.toolOffsetXDoubleSpinBox = self.findChild(QDoubleSpinBox, "toolOffsetXDoubleSpinBox")
        self.toolOffsetYDoubleSpinBox = self.findChild(QDoubleSpinBox, "toolOffsetYDoubleSpinBox")
        self.toolOffsetZDoubleSpinBox = self.findChild(QDoubleSpinBox, "toolOffsetZDoubleSpinBox")

        # Configure spinboxes
        spinboxes = [
            self.toolOffsetXDoubleSpinBox,
            self.toolOffsetYDoubleSpinBox,
            self.toolOffsetZDoubleSpinBox
        ]
        for spinbox in spinboxes:
            if spinbox:
                spinbox.lineEdit().setReadOnly(True)
                spinbox.lineEdit().setDisabled(True)
                palette = QPalette()
                palette.setColor(QPalette.Highlight, QColor(40, 40, 40))
                spinbox.lineEdit().setPalette(palette)

    # Validate UI components
        check_ui_elements(self, [
            self.stackedWidget,
            self.toolOffsetXYPage,
            self.toolOffsetZPage,
            self.toolOffsetXYBackButton,
            self.toolOffsetZBackButton,
            self.toolOffsetXSetButton,
            self.toolOffsetYSetButton,
            self.toolOffsetZSetButton,
            self.toolOffsetXDoubleSpinBox,
            self.toolOffsetYDoubleSpinBox,
            self.toolOffsetZDoubleSpinBox
        ], "ToolOffset Page")

    # Connect buttons to their respective methods
        if self.toolOffsetXYBackButton:
            self.toolOffsetXYBackButton.clicked.connect(self._return_to_main_calibration)
        if self.toolOffsetZBackButton:
            self.toolOffsetZBackButton.clicked.connect(self._return_to_main_calibration)
        if self.toolOffsetXSetButton:
            self.toolOffsetXSetButton.clicked.connect(self._set_tool_offset_x)
        if self.toolOffsetYSetButton:
            self.toolOffsetYSetButton.clicked.connect(self._set_tool_offset_y)
        if self.toolOffsetZSetButton:
            self.toolOffsetZSetButton.clicked.connect(self._set_tool_offset_z)

    def _return_to_main_calibration(self):
        """Return to the main calibration page"""
        self.logger.info("Returning to main calibration from tool offset page")
        if hasattr(self.main_window, 'calibrate_screen'):
            if hasattr(self.main_window.calibrate_screen, 'calibration_stacked_widget') and \
               hasattr(self.main_window.calibrate_screen, 'main_calibrate_page'):
                self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                    self.main_window.calibrate_screen.main_calibrate_page)
                self.logger.debug("Successfully returned to main calibration page")
            else:
                self.logger.error("Cannot return to main calibration - required widgets not found")
        else:
            self.logger.error("Cannot return to main calibration - main_window.calibrate_screen not found")

    def _set_tool_offset_x(self):
        """Set the X offset for the tool."""
        if self.toolOffsetXDoubleSpinBox:
            x_offset = self.toolOffsetXDoubleSpinBox.value()
            self.logger.info(f"Tool X Offset set to: {x_offset} mm")
        else:
            self.logger.error("Cannot set X offset - spin box not found")

    def _set_tool_offset_y(self):
        """Set the Y offset for the tool."""
        if self.toolOffsetYDoubleSpinBox:
            y_offset = self.toolOffsetYDoubleSpinBox.value()
            self.logger.info(f"Tool Y Offset set to: {y_offset} mm")
        else:
            self.logger.error("Cannot set Y offset - spin box not found")

    def _set_tool_offset_z(self):
        """Set the Z offset for the tool."""
        if self.toolOffsetZDoubleSpinBox:
            z_offset = self.toolOffsetZDoubleSpinBox.value()
            self.logger.info(f"Tool Z Offset set to: {z_offset} mm")
        else:
            self.logger.error("Cannot set Z offset - spin box not found")