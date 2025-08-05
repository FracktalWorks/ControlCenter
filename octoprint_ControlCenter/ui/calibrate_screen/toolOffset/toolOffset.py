from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QDoubleSpinBox, QStackedWidget
from PyQt5.QtGui import QPalette, QColor
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils import dialog


logger = get_logger(__name__)

class ToolOffset(QWidget):
    """
    Tool Offset configuration page that allows users to set the XY and Z offsets
    between multiple extruders for dual-extruder printers.
    """
    def __init__(self, main_window):
        super(ToolOffset, self).__init__()
        self.main_window = main_window
        # Use centralized logger
        self.logger = get_logger(self.__class__.__name__)
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
            self.toolOffsetXSetButton.clicked.connect(self.setToolOffsetX)
        if self.toolOffsetYSetButton:
            self.toolOffsetYSetButton.clicked.connect(self.setToolOffsetY)
        if self.toolOffsetZSetButton:
            self.toolOffsetZSetButton.clicked.connect(self.setToolOffsetZ)

    # ! Local signal slot connections
        self.main_window.printer_model.tool_offset_updated.connect(self.getToolOffset)

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

    def setToolOffsetX(self):
        logger.info("MainUiClass.setToolOffsetX started")
        try:
            self.main_window.octoprint_client.gcode(
                command='M218 T1 X{}'.format(round(self.toolOffsetXDoubleSpinBox.value(), 2))
            )  # restore eeprom settings to get Z home offset, mesh bed leveling back
            self.main_window.octoprint_client.gcode(command='M500')
            logger.info("X offset set to: {}".format(round(self.toolOffsetXDoubleSpinBox.value(), 2)))
        except Exception as e:
            logger.error("Error in MainUiClass.setToolOffsetX: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.setToolOffsetX: {}".format(e), overlay=True)

    def setToolOffsetY(self):
        logger.info("MainUiClass.setToolOffsetY started")
        try:
            self.main_window.octoprint_client.gcode(
                command='M218 T1 Y{}'.format(round(self.toolOffsetYDoubleSpinBox.value(), 2))
            )  # restore eeprom settings to get Z home offset, mesh bed leveling back
            self.main_window.octoprint_client.gcode(command='M500')
            self.main_window.octoprint_client.gcode(command='M500')
            logger.info("Y offset set to: {}".format(round(self.toolOffsetYDoubleSpinBox.value(), 2)))
        except Exception as e:
            logger.error("Error in MainUiClass.setToolOffsetY: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.setToolOffsetY: {}".format(e), overlay=True)

    def setToolOffsetZ(self):
        logger.info("MainUiClass.setToolOffsetZ started")
        try:
            self.main_window.octoprint_client.gcode(
                command='M218 T1 Z{}'.format(round(self.toolOffsetZDoubleSpinBox.value(), 2))
            )  # restore eeprom settings to get Z home offset, mesh bed leveling back
            self.main_window.octoprint_client.gcode(command='M500')
            logger.info("Z offset set to: {}".format(round(self.toolOffsetZDoubleSpinBox.value(), 2)))
        except Exception as e:
            logger.error("Error in MainUiClass.setToolOffsetZ: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.setToolOffsetZ: {}".format(e), overlay=True)

    def getToolOffset(self, M218Data):
        logger.info("MainUiClass.getToolOffset started")
        try:
            # if float(M218Data[M218Data.index('X') + 1:].split(' ', 1)[0] ) > 0:
            print("____________________TOOL OFFSET CALLED____________________")
            self.toolOffsetZ = M218Data[M218Data.index('Z') + 1:].split(' ', 1)[0]
            self.toolOffsetX = M218Data[M218Data.index('X') + 1:].split(' ', 1)[0]
            self.toolOffsetY = M218Data[M218Data.index('Y') + 1:].split(' ', 1)[0]
            self.toolOffsetXDoubleSpinBox.setValue(float(self.toolOffsetX))
            self.toolOffsetYDoubleSpinBox.setValue(float(self.toolOffsetY))
            self.toolOffsetZDoubleSpinBox.setValue(float(self.toolOffsetZ))
            self.idexToolOffsetRestoreValue = float(self.toolOffsetZ)
            print("____________________TOOL OFFSET CALLED END____________________")
        except Exception as e:
            logger.error("Error in MainUiClass.getToolOffset: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.getToolOffset: {}".format(e), overlay=True)

