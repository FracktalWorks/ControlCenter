from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

from utils import logger, dialog

class IdexLevelCalibration(QWidget):
    """
    IDEX (Independent Dual Extruder) Level Calibration widget that guides the user
    through a multi-step calibration process for aligning the dual extruders.
    """
    def __init__(self, main_window):
        super(IdexLevelCalibration, self).__init__()
        self.main_window = main_window
        self.logger = setup_logger('idex_calibration')
        self.logger.info("Initializing IDEX Level Calibration screen")

        # Load the .ui file
        try:
            uic.loadUi('/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/calibrate_screen/idexLevelCalibration/idexLevelCalibration.ui', self)
            self.logger.info("IdexLevelCalibration UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load IdexLevelCalibration UI file: {e}")

        # Initialize UI elements
        self.stacked_widget = self.findChild(QStackedWidget, "stackedWidget")
        self.idexConfigStep1Page = self.findChild(QWidget, "idexConfigStep1Page")
        self.idexConfigStep2Page = self.findChild(QWidget, "idexConfigStep2Page")
        self.idexConfigStep3Page = self.findChild(QWidget, "idexConfigStep3Page")
        self.idexConfigStep4Page = self.findChild(QWidget, "idexConfigStep4Page")
        self.idexConfigStep5Page = self.findChild(QWidget, "idexConfigStep5Page")

        self.idexConfigStep1NextButton = self.findChild(QPushButton, "idexConfigStep1NextButton")
        self.idexConfigStep2NextButton = self.findChild(QPushButton, "idexConfigStep2NextButton")
        self.idexConfigStep3NextButton = self.findChild(QPushButton, "idexConfigStep3NextButton")
        self.idexConfigStep4NextButton = self.findChild(QPushButton, "idexConfigStep4NextButton")
        self.idexConfigStep5NextButton = self.findChild(QPushButton, "idexConfigStep5NextButton")

        self.idexConfigStep1CancelButton = self.findChild(QPushButton, "idexConfigStep1CancelButton")
        self.idexConfigStep2CancelButton = self.findChild(QPushButton, "idexConfigStep2CancelButton")
        self.idexConfigStep3CancelButton = self.findChild(QPushButton, "idexConfigStep3CancelButton")
        self.idexConfigStep4CancelButton = self.findChild(QPushButton, "idexConfigStep4CancelButton")
        self.idexConfigStep5CancelButton = self.findChild(QPushButton, "idexConfigStep5CancelButton")

        self.CalibrationPoint1_2 = self.findChild(QLabel, "CalibrationPoint1_2")
        self.CalibrationPoint2_2 = self.findChild(QLabel, "CalibrationPoint2_2")
        self.CalibrationPoint3 = self.findChild(QLabel, "CalibrationPoint3")
        self.Nozzlelevel1 = self.findChild(QLabel, "Nozzlelevel1")
        self.Nozzlelevel2 = self.findChild(QLabel, "Nozzlelevel2")

        self.moveZMIdexButton = self.findChild(QPushButton, "moveZMIdexButton")
        self.moveZPIdexButton = self.findChild(QPushButton, "moveZPIdexButton")

        # Validate UI elements
        check_ui_elements(self, [
            self.idexConfigStep1Page, self.idexConfigStep2Page, self.idexConfigStep3Page, self.idexConfigStep4Page, self.idexConfigStep5Page,
            self.idexConfigStep1NextButton, self.idexConfigStep2NextButton, self.idexConfigStep3NextButton, self.idexConfigStep4NextButton, self.idexConfigStep5NextButton,
            self.idexConfigStep1CancelButton, self.idexConfigStep2CancelButton, self.idexConfigStep3CancelButton, self.idexConfigStep4CancelButton, self.idexConfigStep5CancelButton,
        ], "IDEX Level Calibration")

        # Connect buttons to their respective functions
        if self.idexConfigStep1NextButton:
            self.idexConfigStep1NextButton.clicked.connect(self.idexConfigStep2)
        if self.idexConfigStep2NextButton:
            self.idexConfigStep2NextButton.clicked.connect(self.idexConfigStep3)
        if self.idexConfigStep3NextButton:
            self.idexConfigStep3NextButton.clicked.connect(self.idexConfigStep4)
        if self.idexConfigStep4NextButton:
            self.idexConfigStep4NextButton.clicked.connect(self.idexConfigStep5)
        if self.idexConfigStep5NextButton:
            self.idexConfigStep5NextButton.clicked.connect(self.idexDoneStep)

        if self.idexConfigStep1CancelButton:
            self.idexConfigStep1CancelButton.clicked.connect(self.idexCancelStep)
        if self.idexConfigStep2CancelButton:
            self.idexConfigStep2CancelButton.clicked.connect(self.idexCancelStep)
        if self.idexConfigStep3CancelButton:
            self.idexConfigStep3CancelButton.clicked.connect(self.idexCancelStep)
        if self.idexConfigStep4CancelButton:
            self.idexConfigStep4CancelButton.clicked.connect(self.idexCancelStep)
        if self.idexConfigStep5CancelButton:
            self.idexConfigStep5CancelButton.clicked.connect(self.idexCancelStep)

        self.moveZMIdexButton.pressed.connect(lambda: self.main_window.octoprint_client.jog(z=-0.1))
        self.moveZPIdexButton.pressed.connect(lambda: self.main_window.octoprint_client.jog(z=0.1))

        # Set the default screen
        self.reset_wizard()


    def _navigate_to_step(self, step_number):
        """Navigate to a specific step in the calibration process"""
        target_page = getattr(self, f"page{step_number}", None)

        if self.stacked_widget and target_page:
            self.logger.info(f"Navigating to IDEX Calibration Step {step_number}")
            self.stacked_widget.setCurrentWidget(target_page)
        else:
            self.logger.error(f"Error: Cannot navigate to IDEX Calibration Step {step_number}")

    def _cancel_calibration(self):
        """Cancel the IDEX calibration process and return to main calibration page"""
        self.logger.info("IDEX Calibration process canceled")
        self._return_to_main_calibration()

    def _finish_calibration(self):
        """Finish the IDEX calibration process and return to main calibration page"""
        self.logger.info("IDEX Calibration process completed successfully")
        self._return_to_main_calibration()

    def _return_to_main_calibration(self):
        """Common method to return to the main calibration screen"""
        if hasattr(self.main_window, 'calibrate_screen'):
            if hasattr(self.main_window.calibrate_screen, 'calibration_stacked_widget') and \
               hasattr(self.main_window.calibrate_screen, 'main_calibrate_page'):
                self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                    self.main_window.calibrate_screen.main_calibrate_page)
                self.logger.info("Returned to main calibration page")
            else:
                self.logger.error("Cannot return to main calibration - required widgets not found")
        else:
            self.logger.error("Cannot return to main calibration - calibrate_screen not found")

    def reset_wizard(self):
        """Reset the IDEX Level Calibration wizard to its initial state."""
        if self.stackedWidget and self.idexConfigStep1Page:
            self.stackedWidget.setCurrentWidget(self.idexConfigStep1Page)
            self.logger.info("Bed Leveling wizard reset to initial state")
        else:
            self.logger.error("Cannot reset wizard - required widgets not found")

    def idexConfigStep1(self):
        """
        Shows welcome message.
        Welcome Page, Give Info. Unlock nozzle and push down
        :return:
        """
        logger.info("MainUiClass.idexConfigStep1 started")
        try:
            self.main_window.octoprint_client.gcode(command='M503')  # Gets old tool offset position
            self.main_window.octoprint_client.gcode(command='M218 T1 Z0')  # set nozzle tool offsets to 0
            self.main_window.octoprint_client.gcode(command='M104 S200')
            self.main_window.octoprint_client.gcode(command='M104 T1 S200')
            self.main_window.octoprint_client.home(['x', 'y', 'z'])
            self.main_window.octoprint_client.gcode(command='G1 X10 Y10 Z20 F5000')
            self.main_window.octoprint_client.gcode(command='T0')  # Set active tool to t0
            self.main_window.octoprint_client.gcode(command='M420 S0')  # Dissable mesh bed leveling for good measure
            self.stackedWidget.setCurrentWidget(self.idexConfigStep1Page)
            self.movie5 = QtGui.QMovie(
                "/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/resources/img/Calibration/Nozzlelevel1.gif"
            )
            self.Nozzlelevel1.setMovie(self.movie5)
            self.movie5.start()
        except Exception as e:
            logger.error("Error in MainUiClass.idexConfigStep1: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.idexConfigStep1: {}".format(e), overlay=True)
            try:
                self.movie5.stop()
            except:
                pass

    def idexConfigStep2(self):
        """
        levels first position (RIGHT)
        :return:
        """
        logger.info("MainUiClass.idexConfigStep2 started")
        try:
            self.stackedWidget.setCurrentWidget(self.idexConfigStep2Page)
            self.main_window.octoprint_client.jog(
                x=self.main_window.printer_model.calibrationPosition['X1'],
                y=self.main_window.printer_model.calibrationPosition['Y1'],
                absolute=True, speed=10000
            )
            self.main_window.octoprint_client.jog(z=0, absolute=True, speed=1500)
            self.movie5.stop()
            self.movie6 = QtGui.QMovie(
                "/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/resources/img/Calibration/CalibrationPoint1.gif"
            )
            self.CalibrationPoint1_2.setMovie(self.movie6)
            self.movie6.start()
        except Exception as e:
            logger.error("Error in MainUiClass.idexConfigStep2: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.idexConfigStep2: {}".format(e), overlay=True)
            try:
                self.movie5.stop()
                self.movie6.stop()
            except:
                pass

    def idexConfigStep3(self):
        """
        levels second leveling position (LEFT)
        """
        logger.info("MainUiClass.idexConfigStep3 started")
        try:
            self.stackedWidget.setCurrentWidget(self.idexConfigStep3Page)
            self.main_window.octoprint_client.jog(z=10, absolute=True, speed=1500)
            self.main_window.octoprint_client.jog(
                x=self.main_window.printer_model.calibrationPosition['X2'],
                y=self.main_window.printer_model.calibrationPosition['Y2'],
                absolute=True, speed=10000
            )
            self.main_window.octoprint_client.jog(z=0, absolute=True, speed=1500)
            self.movie6.stop()
            self.movie7 = QtGui.QMovie(
                "/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/resources/img/Calibration/CalibrationPoint2.gif"
            )
            self.CalibrationPoint2_2.setMovie(self.movie7)
            self.movie7.start()
        except Exception as e:
            logger.error("Error in MainUiClass.idexConfigStep3: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.idexConfigStep3: {}".format(e), overlay=True)
            try:
                self.movie6.stop()
                self.movie7.stop()
            except:
                pass

    def idexConfigStep4(self):
        """
        Set to Mirror mode and asks to loosen the carriage, push both doen to max
        :return:
        """
        logger.info("MainUiClass.idexConfigStep4 started")
        try:
            self.stackedWidget.setCurrentWidget(self.idexConfigStep4Page)
            self.main_window.octoprint_client.jog(z=10, absolute=True, speed=1500)
            self.main_window.octoprint_client.gcode(command='M605 S3')
            self.main_window.octoprint_client.jog(
                x=self.main_window.printer_model.calibrationPosition['X1'],
                y=self.main_window.printer_model.calibrationPosition['Y1'],
                absolute=True, speed=10000
            )
            self.movie7.stop()
            self.movie8 = QtGui.QMovie(
                "/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/resources/img/Calibration/NozzleLevelNew1.gif"
            )
            self.CalibrationPoint3.setMovie(self.movie8)
            self.movie8.start()
        except Exception as e:
            logger.error("Error in MainUiClass.idexConfigStep4: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.idexConfigStep4: {}".format(e), overlay=True)
            try:
                self.movie7.stop()
                self.movie8.stop()
            except:
                pass

    def idexConfigStep5(self):
        """
        take bed up until both nozzles touch the bed. ASk to take nozzle up and down till nozzle just rests on the bed and tighten
        :return:
        """
        logger.info("MainUiClass.idexConfigStep5 started")
        try:
            self.stackedWidget.setCurrentWidget(self.idexConfigStep5Page)
            self.main_window.octoprint_client.jog(z=1, absolute=True, speed=10000)
            self.movie8.stop()
            self.movie9 = QtGui.QMovie(
                "/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/resources/img/Calibration/NozzlelevelNew2.gif"
            )
            self.Nozzlelevel2.setMovie(self.movie9)
            self.movie9.start()
        except Exception as e:
            logger.error("Error in MainUiClass.idexConfigStep5: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.idexConfigStep5: {}".format(e), overlay=True)
            try:
                self.movie8.stop()
                self.movie9.stop()
            except:
                pass

    def idexDoneStep(self):
        """
        Exits leveling
        :return:
        """
        logger.info("MainUiClass.idexDoneStep started")
        try:
            self.main_window.octoprint_client.jog(z=4, absolute=True, speed=1500)
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page
            )
            self.movie9.stop()
            self.main_window.octoprint_client.home(['z'])
            self.main_window.octoprint_client.home(['x', 'y'])
            self.main_window.octoprint_client.gcode(command='M104 S0')
            self.main_window.octoprint_client.gcode(command='M104 T1 S0')
            self.main_window.octoprint_client.gcode(command='M605 S1')
            self.main_window.octoprint_client.gcode(command='M218 T1 Z0') #set nozzle offsets to 0
            self.main_window.octoprint_client.gcode(command='M84')
            self.main_window.octoprint_client.gcode(command='M500')  # store eeprom settings to get Z home offset, mesh bed leveling back
        except Exception as e:
            logger.error("Error in MainUiClass.idexDoneStep: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.idexDoneStep: {}".format(e), overlay=True)
            try:
                self.movie9.stop()
            except:
                pass

    def idexCancelStep(self):
        logger.info("MainUiClass.idexCancelStep started")
        try:
            self.main_window.calibrate_screen.calibration_stacked_widget.setCurrentWidget(
                self.main_window.calibrate_screen.main_calibrate_page
            )
            try:
                self.movie5.stop()
                self.movie6.stop()
                self.movie7.stop()
                self.movie8.stop()
                self.movie9.stop()
            except:
                pass
            self.main_window.octoprint_client.gcode(command='M605 S1')
            self.main_window.octoprint_client.home(['z'])
            self.main_window.octoprint_client.home(['x', 'y'])
            self.main_window.octoprint_client.gcode(command='M104 S0')
            self.main_window.octoprint_client.gcode(command='M104 T1 S0')
            self.main_window.calibrate_screen.screens.get("tool_offset")
            self.main_window.octoprint_client.gcode(
                command='M218 T1 Z{}'.format(
                    self.main_window.calibrate_screen.screens.get("tool_offset").idexToolOffsetRestoreValue
                )
            )
            self.main_window.octoprint_client.gcode(command='M84')
        except Exception as e:
            logger.error("Error in MainUiClass.idexCancelStep: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.idexCancelStep: {}".format(e), overlay=True)
