from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

from utils import logger
from utils import dialog


class BedLeveling(QWidget):
    """
    Bed Leveling widget that guides the user through the bed leveling calibration process
    with a multi-step wizard interface.
    """

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.logger = setup_logger('bed_leveling')
        self.logger.info("Initializing Bed Leveling screen")

        try:
            uic.loadUi(
                '/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/calibrate_screen/bedLevelingPage/bedLevelingPage.ui',
                self)
            self.logger.info("BedLeveling UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load BedLeveling UI file: {e}")

        # Initialize the Pages
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.nozzleHeightStep1Page = self.findChild(QWidget, "nozzleHeightStep1Page")
        self.quickStep1Page = self.findChild(QWidget, "quickStep1Page")
        self.quickStep2Page = self.findChild(QWidget, "quickStep2Page")
        self.quickStep3Page = self.findChild(QWidget, "quickStep3Page")
        self.quickStep4Page = self.findChild(QWidget, "quickStep4Page")

        # Initialize the buttons
        self.moveZPT1CaliberateButton = self.findChild(QPushButton, "moveZPT1CaliberateButton")
        self.moveZMT1CaliberateButton = self.findChild(QPushButton, "moveZMT1CaliberateButton")
        self.nozzleHeightStep1NextButton = self.findChild(QPushButton, "nozzleHeightStep1NextButton")
        self.nozzleHeightStep1CancelButton = self.findChild(QPushButton, "nozzleHeightStep1CancelButton")
        self.quickStep1NextButton = self.findChild(QPushButton, "quickStep1NextButton")
        self.quickStep1CancelButton = self.findChild(QPushButton, "quickStep1CancelButton")
        self.quickStep2NextButton = self.findChild(QPushButton, "quickStep2NextButton")
        self.quickStep2CancelButton = self.findChild(QPushButton, "quickStep2CancelButton")
        self.quickStep3NextButton = self.findChild(QPushButton, "quickStep3NextButton")
        self.quickStep3CancelButton = self.findChild(QPushButton, "quickStep3CancelButton")
        self.quickStep4NextButton = self.findChild(QPushButton, "quickStep4NextButton")
        self.quickStep4CancelButton = self.findChild(QPushButton, "quickStep4CancelButton")

        # Validate UI elements
        check_ui_elements(self, [
            self.stackedWidget, self.nozzleHeightStep1Page, self.quickStep1Page, self.quickStep2Page,
            self.quickStep3Page, self.quickStep4Page,
            self.moveZPT1CaliberateButton, self.moveZMT1CaliberateButton, self.nozzleHeightStep1NextButton,
            self.nozzleHeightStep1CancelButton,
            self.quickStep1NextButton, self.quickStep1CancelButton, self.quickStep2NextButton,
            self.quickStep2CancelButton,
            self.quickStep3NextButton, self.quickStep3CancelButton, self.quickStep4NextButton,
            self.quickStep4CancelButton
        ], "BedLeveling")

        if self.moveZPT1CaliberateButton:
            self.moveZPT1CaliberateButton.pressed.connect(lambda: self.main_window.octoprint_client.jog(z=0.025))
        if self.moveZMT1CaliberateButton:
            self.moveZMT1CaliberateButton.pressed.connect(lambda: self.main_window.octoprint_client.jog(z=-0.025))
        if self.nozzleHeightStep1NextButton:
            self.nozzleHeightStep1NextButton.clicked.connect(self.nozzleHeightStep1)
        if self.nozzleHeightStep1CancelButton:
            self.nozzleHeightStep1CancelButton.clicked.connect(self.cancelStep)

        if self.quickStep1NextButton:
            self.quickStep1NextButton.clicked.connect(self.quickStep2)
        if self.quickStep2NextButton:
            self.quickStep2NextButton.clicked.connect(self.quickStep3)
        if self.quickStep3NextButton:
            self.quickStep3NextButton.clicked.connect(self.quickStep4)
        if self.quickStep4NextButton:
            self.quickStep4NextButton.clicked.connect(self.nozzleHeightStep1)

        if self.quickStep1CancelButton:
            self.quickStep1CancelButton.clicked.connect(self.cancelStep)
        if self.quickStep2CancelButton:
            self.quickStep2CancelButton.clicked.connect(self.cancelStep)
        if self.quickStep3CancelButton:
            self.quickStep3CancelButton.clicked.connect(self.cancelStep)
        if self.quickStep4CancelButton:
            self.quickStep4CancelButton.clicked.connect(self.cancelStep)

        # Initialize to the first page
        self.reset_wizard()
        # self.quickStep1()
        self.logger.info("Bed Leveling initialization complete")

    def quickStep1(self):
        """
        Shows welcome message.
        Homes to MAX
        goes to position where leveling screws can be opened
        :return:
        """
        logger.info("MainUiClass.quickStep1 started")
        try:
            self.toolZOffsetCaliberationPageCount = 0
            self.main_window.octoprint_client.gcode(command='M104 S200')
            self.main_window.octoprint_client.gcode(command='M104 T1 S200')

            self.main_window.octoprint_client.gcode(command='T0')  # Set active tool to t0
            self.main_window.octoprint_client.gcode(
                command='M503')  # makes sure internal value of Z offset and Tool offsets are stored before erasing
            self.main_window.octoprint_client.gcode(command='M420 S0')  # Disable mesh bed leveling for good measure
            self.stackedWidget.setCurrentWidget(self.quickStep1Page)
            self.main_window.octoprint_client.home(['x', 'y', 'z'])
            self.main_window.octoprint_client.gcode(command='T0')
            self.main_window.octoprint_client.jog(x=40, y=40, absolute=True, speed=2000)
        except Exception as e:
            logger.error("Error in MainUiClass.quickStep1: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.quickStep1: {}".format(e), overlay=True)

    def quickStep2(self):
        """
        levels first position (RIGHT)
        :return:
        """
        logger.info("MainUiClass.quickStep2 started")
        try:
            self.stackedWidget.setCurrentWidget(self.quickStep2Page)
            self.main_window.octoprint_client.jog(
                x=self.main_window.printer_model.calibrationPosition['X1'],
                y=self.main_window.printer_model.calibrationPosition['Y1'],
                absolute=True, speed=10000
            )
            self.main_window.octoprint_client.jog(z=0, absolute=True, speed=1500)
            self.movie1 = QtGui.QMovie(
                "/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/resources/img/Calibration/CalibrationPoint1.gif"
            )
            self.CalibrationPoint1.setMovie(self.movie1)
            self.movie1.start()
        except Exception as e:
            logger.error("Error in MainUiClass.quickStep2: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.quickStep2: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
            except:
                pass

    def quickStep3(self):
        """
        levels second leveling position (LEFT)
        """
        logger.info("MainUiClass.quickStep3 started")
        try:
            self.stackedWidget.setCurrentWidget(self.quickStep3Page)
            self.main_window.octoprint_client.jog(z=10, absolute=True, speed=1500)
            self.main_window.octoprint_client.jog(
                x=self.main_window.printer_model.calibrationPosition['X2'],
                y=self.main_window.printer_model.calibrationPosition['Y2'],
                absolute=True, speed=10000
            )
            self.main_window.octoprint_client.jog(z=0, absolute=True, speed=1500)
            self.movie1.stop()
            self.movie2 = QtGui.QMovie(
                "/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/resources/img/Calibration/CalibrationPoint2.gif"
            )
            self.CalibrationPoint2.setMovie(self.movie2)
            self.movie2.start()
        except Exception as e:
            logger.error("Error in MainUiClass.quickStep3: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.quickStep3: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
                self.movie2.stop()
            except:
                pass

    def quickStep4(self):
        """
        levels third leveling position  (BACK)
        :return:
        """
        logger.info("MainUiClass.quickStep4 started")
        try:
            # sent twice for some reason
            self.stackedWidget.setCurrentWidget(self.quickStep4Page)
            self.main_window.octoprint_client.jog(z=10, absolute=True, speed=1500)
            self.main_window.octoprint_client.jog(
                x=self.main_window.printer_model.calibrationPosition['X3'],
                y=self.main_window.printer_model.calibrationPosition['Y3'],
                absolute=True, speed=10000
            )
            self.main_window.octoprint_client.jog(z=0, absolute=True, speed=1500)
            self.movie2.stop()
            self.movie3 = QtGui.QMovie(
                "/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/resources/img/Calibration/CalibrationPoint3.gif"
            )
            self.CalibrationPoint3.setMovie(self.movie3)
            self.movie3.start()
        except Exception as e:
            logger.error("Error in MainUiClass.quickStep4: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.quickStep4: {}".format(e), overlay=True)
            try:
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass

    def nozzleHeightStep1(self):
        logger.info("MainUiClass.nozzleHeightStep1 started")
        try:
            self.movie3.stop()
            if self.toolZOffsetCaliberationPageCount == 0:
                self.toolZOffsetLabel.setText(
                    "Move the bed up or down to the First Nozzle , testing height using paper")
                self.stackedWidget.setCurrentWidget(self.nozzleHeightStep1Page)
                self.main_window.octoprint_client.jog(z=10, absolute=True, speed=1500)
                self.main_window.octoprint_client.jog(
                    x=self.main_window.printer_model.calibrationPosition['X4'],
                    y=self.main_window.printer_model.calibrationPosition['Y4'],
                    absolute=True, speed=10000
                )
                self.main_window.octoprint_client.jog(z=1, absolute=True, speed=1500)
                self.toolZOffsetCaliberationPageCount = 1
            elif self.toolZOffsetCaliberationPageCount == 1:
                self.toolZOffsetLabel.setText(
                    "Move the bed up or down to the Second Nozzle , testing height using paper")
                self.main_window.octoprint_client.gcode(command='G92 Z0')  # set the current Z position to zero
                self.main_window.octoprint_client.jog(z=1, absolute=True, speed=1500)
                self.main_window.octoprint_client.gcode(command='T1')
                self.main_window.octoprint_client.jog(
                    x=self.main_window.printer_model.calibrationPosition['X4'],
                    y=self.main_window.printer_model.calibrationPosition['Y4'],
                    absolute=True, speed=10000
                )
                self.toolZOffsetCaliberationPageCount = 2
            else:
                self.doneStep()
        except Exception as e:
            logger.error("Error in MainUiClass.nozzleHeightStep1: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.nozzleHeightStep1: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass

    def doneStep(self):
        """
        Exits leveling
        :return:
        """
        logger.info("MainUiClass.doneStep started")
        try:
            self.setNewToolZOffsetFromCurrentZBool = True
            self.main_window.octoprint_client.gcode(command='M114')
            self.main_window.octoprint_client.jog(z=4, absolute=True, speed=1500)
            self.main_window.octoprint_client.gcode(command='T0')

            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            self.main_window.octoprint_client.home(['x', 'y', 'z'])
            self.main_window.octoprint_client.gcode(command='M104 S0')
            self.main_window.octoprint_client.gcode(command='M104 T1 S0')
            self.main_window.octoprint_client.gcode(command='M84')
            self.main_window.octoprint_client.gcode(
                command='M500')  # store eeprom settings to get Z home offset, mesh bed leveling back
        except Exception as e:
            logger.error("Error in MainUiClass.doneStep: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.doneStep: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass

    def cancelStep(self):
        logger.info("MainUiClass.cancelStep started")
        try:
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page)
            self.main_window.octoprint_client.home(['x', 'y', 'z'])
            self.main_window.octoprint_client.gcode(command='M104 S0')
            self.main_window.octoprint_client.gcode(command='M104 T1 S0')
            self.main_window.octoprint_client.gcode(command='M84')
            try:
                self.movie1.stop()
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass
        except Exception as e:
            # self._return_to_main_calibration()
            logger.error("Error in MainUiClass.cancelStep: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.cancelStep: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass

    # ! To be commented out later
    def _navigate_to_page(self, page):
        """Navigate to a specific page within the bed leveling wizard"""
        if self.stackedWidget and page:
            self.logger.info(f"Navigating to {page.objectName()}")
            self.stackedWidget.setCurrentWidget(page)
        else:
            self.logger.error(f"Cannot navigate - stackedWidget or page is missing")

    def _return_to_main_calibration(self):
        """Return to the main calibration page"""
        self.logger.info("Bed leveling process canceled by user")
        if hasattr(self.main_window, 'calibrate_screen'):
            if hasattr(self.main_window.calibrate_screen, 'calibration_stacked_widget') and \
                    hasattr(self.main_window.calibrate_screen, 'main_calibrate_page'):
                self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                    self.main_window.calibrate_screen.main_calibrate_page
                )
                self.logger.info("Returning to main calibration page")
            else:
                self.logger.error("Cannot return to main calibration - required widgets not found")
        else:
            self.logger.error("Cannot return to main calibration - calibrate_screen not found")

    def _finish_bed_leveling(self):
        """Complete the bed leveling process and return to main calibration"""
        self.logger.info("Bed leveling process completed successfully")
        self._return_to_main_calibration()

    def move_z_pt1(self):
        """Move Z-axis +0.1mm for calibration"""
        self.logger.info("Moving Z-axis +0.1mm for calibration")

    def move_z_mt1(self):
        """Move Z-axis -0.1mm for calibration"""
        self.logger.info("Moving Z-axis -0.1mm for calibration")

    def reset_wizard(self):
        """
        Function is called when the bed levelling class is initialized.
        Sets quickStep1 Page as the first page
        """
        if self.stackedWidget and self.quickStep1Page:
            self.stackedWidget.setCurrentWidget(self.quickStep1Page)
            self.logger.info("Bed Leveling wizard reset to initial state")
        else:
            self.logger.error("Cannot reset wizard - required widgets not found")