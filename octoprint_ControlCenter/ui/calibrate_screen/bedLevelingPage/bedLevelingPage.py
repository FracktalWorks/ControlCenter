import os
from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils.printer_ui_config import is_dual_nozzle_printer
from utils import dialog


logger = get_logger(__name__)

class BedLeveling(QWidget):
    """
    Bed Leveling widget that guides the user through the bed leveling calibration process
    with a multi-step wizard interface.
    """

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.model = main_window.printer_model
        self.octoprint_client = main_window.octoprint_client
        self.logger = get_logger(self.__class__.__name__)  # Using the centralized logger
        self.logger.info("Initializing Bed Leveling screen")

        try:
            # Use relative path from the current module's directory
            ui_file_path = os.path.join(os.path.dirname(__file__), "bedLevelingPage.ui")
            uic.loadUi(ui_file_path, self)
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

        self.moveZPT1CaliberateButton.pressed.connect(lambda: self.octoprint_client.jog(z=0.025))
        self.moveZMT1CaliberateButton.pressed.connect(lambda: self.octoprint_client.jog(z=-0.025))
        self.nozzleHeightStep1NextButton.clicked.connect(self.nozzleHeightStep1)
        self.nozzleHeightStep1CancelButton.clicked.connect(self.cancelStep)

        self.quickStep1NextButton.clicked.connect(self.quickStep2)
        self.quickStep2NextButton.clicked.connect(self.quickStep3)
        self.quickStep3NextButton.clicked.connect(self.quickStep4)
        self.quickStep4NextButton.clicked.connect(self.nozzleHeightStep1)

        self.quickStep1CancelButton.clicked.connect(self.cancelStep)
        self.quickStep2CancelButton.clicked.connect(self.cancelStep)
        self.quickStep3CancelButton.clicked.connect(self.cancelStep)
        self.quickStep4CancelButton.clicked.connect(self.cancelStep)

        # Remove old flag-based approach - now using signal/slot
        # self.setNewToolZOffsetFromCurrentZBool = False

        # Connect to position updates for tool offset calibration
        # This will be connected/disconnected dynamically when needed
        # self.main_window.printer_model.current_position_updated.connect(self.on_position_updated_for_tool_offset)

        # Ensure state variables are initialized even if quickStep1 hasn't run yet
        self.toolZOffsetCaliberationPageCount = 0
        
        # Store positions for tool offset calculation
        self.tool0_calibration_position = None
        self.tool1_calibration_position = None

        # self.quickStep1()
        self.logger.info("Bed Leveling initialization complete")

    def showEvent(self, event):
        """Reset to quickStep1Page whenever this widget is shown."""
        super().showEvent(event)
        try:
            self.stackedWidget.setCurrentWidget(self.quickStep1Page)
            self.logger.debug("Reset stacked widget to quickStep1Page on show")
        except Exception as e:
            self.logger.error(f"Error resetting to quickStep1Page: {e}")

    def quickStep1(self):
        """
        Shows welcome message.
        Homes to MAX
        goes to position where leveling screws can be opened
        :return:
        """
        self.logger.info("BedLeveling.quickStep1 started")
        try:
            self.toolZOffsetCaliberationPageCount = 0
            self.octoprint_client.gcode(command='M104 S200')
            
            # Only heat T1 for dual nozzle printers
            if is_dual_nozzle_printer():
                self.octoprint_client.gcode(command='M104 T1 S200')

            self.octoprint_client.gcode(command='T0')  # Set active tool to t0
            self.octoprint_client.gcode(
                command='M503')  # makes sure internal value of Z offset and Tool offsets are stored before erasing
            self.octoprint_client.gcode(command='M420 S0')  # Disable mesh bed leveling for good measure
            self.stackedWidget.setCurrentWidget(self.quickStep1Page)
            self.octoprint_client.home(['x', 'y', 'z'])
            self.octoprint_client.gcode(command='T0')
            self.octoprint_client.jog(x=40, y=40, absolute=True, speed=2000)
        except Exception as e:
            self.logger.error("Error in BedLeveling.quickStep1: {}".format(e))
            dialog.WarningOk(self, "Error in BedLeveling.quickStep1: {}".format(e), overlay=True)

    def quickStep2(self):
        """
        levels first position (RIGHT)
        :return:
        """
        self.logger.info("BedLeveling.quickStep2 started")
        try:
            self.stackedWidget.setCurrentWidget(self.quickStep2Page)
            self.octoprint_client.jog(
                x=self.main_window.printer_model.calibrationPosition['X1'],
                y=self.main_window.printer_model.calibrationPosition['Y1'],
                absolute=True, speed=10000
            )
            self.octoprint_client.jog(z=0, absolute=True, speed=1500)
            self.movie1 = QtGui.QMovie(
                os.path.join(os.path.dirname(__file__), "resources", "CalibrationPoint1.gif")
            )
            self.CalibrationPoint1.setMovie(self.movie1)
            self.movie1.start()
        except Exception as e:
            self.logger.error("Error in BedLeveling.quickStep2: {}".format(e))
            dialog.WarningOk(self, "Error in BedLeveling.quickStep2: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
            except:
                pass

    def quickStep3(self):
        """
        levels second leveling position (LEFT)
        """
        self.logger.info("BedLeveling.quickStep3 started")
        try:
            self.stackedWidget.setCurrentWidget(self.quickStep3Page)
            self.octoprint_client.jog(z=10, absolute=True, speed=1500)
            self.octoprint_client.jog(
                x=self.main_window.printer_model.calibrationPosition['X2'],
                y=self.main_window.printer_model.calibrationPosition['Y2'],
                absolute=True, speed=10000
            )
            self.octoprint_client.jog(z=0, absolute=True, speed=1500)
            self.movie1.stop()
            self.movie2 = QtGui.QMovie(
                os.path.join(os.path.dirname(__file__), "resources", "CalibrationPoint2.gif")
            )
            self.CalibrationPoint2.setMovie(self.movie2)
            self.movie2.start()
        except Exception as e:
            self.logger.error("Error in BedLeveling.quickStep3: {}".format(e))
            dialog.WarningOk(self, "Error in BedLeveling.quickStep3: {}".format(e), overlay=True)
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
        self.logger.info("BedLeveling.quickStep4 started")
        try:
            # sent twice for some reason
            self.stackedWidget.setCurrentWidget(self.quickStep4Page)
            self.octoprint_client.jog(z=10, absolute=True, speed=1500)
            self.octoprint_client.jog(
                x=self.main_window.printer_model.calibrationPosition['X3'],
                y=self.main_window.printer_model.calibrationPosition['Y3'],
                absolute=True, speed=10000
            )
            self.octoprint_client.jog(z=0, absolute=True, speed=1500)
            self.movie2.stop()
            self.movie3 = QtGui.QMovie(
                os.path.join(os.path.dirname(__file__), "resources", "CalibrationPoint3.gif")
            )
            self.CalibrationPoint3.setMovie(self.movie3)
            self.movie3.start()
        except Exception as e:
            self.logger.error("Error in BedLeveling.quickStep4: {}".format(e))
            dialog.WarningOk(self, "Error in BedLeveling.quickStep4: {}".format(e), overlay=True)
            try:
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass

    def nozzleHeightStep1(self):
        self.logger.info("BedLeveling.nozzleHeightStep1 started")
        try:
            self.movie3.stop()
            
            # For single nozzle printers, skip nozzle height calibration and go directly to done
            if not is_dual_nozzle_printer():
                self.logger.info("Single nozzle mode detected - skipping nozzle height calibration")
                self.doneStep()
                return
            
            if self.toolZOffsetCaliberationPageCount == 0:
                self.toolZOffsetLabel.setText(
                    "Move the bed up or down to the First Nozzle , testing height using paper")
                self.stackedWidget.setCurrentWidget(self.nozzleHeightStep1Page)
                self.octoprint_client.jog(z=10, absolute=True, speed=1500)
                self.octoprint_client.jog(
                    x=self.main_window.printer_model.calibrationPosition['X4'],
                    y=self.main_window.printer_model.calibrationPosition['Y4'],
                    absolute=True, speed=10000
                )
                self.octoprint_client.jog(z=1, absolute=True, speed=1500)
                self.toolZOffsetCaliberationPageCount = 1
            elif self.toolZOffsetCaliberationPageCount == 1:
                self.toolZOffsetLabel.setText(
                    "Move the bed up or down to the Second Nozzle , testing height using paper")
                self.octoprint_client.gcode(command='G92 Z0')  # set the current Z position to zero
                self.octoprint_client.jog(z=1, absolute=True, speed=1500)
                self.octoprint_client.gcode(command='T1')
                self.octoprint_client.jog(
                    x=self.main_window.printer_model.calibrationPosition['X4'],
                    y=self.main_window.printer_model.calibrationPosition['Y4'],
                    absolute=True, speed=10000
                )
                self.toolZOffsetCaliberationPageCount = 2
            else:
                self.doneStep()
        except Exception as e:
            self.logger.error("Error in BedLeveling.nozzleHeightStep1: {}".format(e))
            dialog.WarningOk(self, "Error in BedLeveling.nozzleHeightStep1: {}".format(e), overlay=True)
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
        self.logger.info("BedLeveling.doneStep started")
        try:
            # Only set tool offset for dual nozzle printers
            if is_dual_nozzle_printer():
                # Connect to position updates to capture T1 position for offset calculation
                self.main_window.printer_model.current_position_updated.connect(self.on_position_updated_for_tool_offset)
                self.logger.info("Connected to position updates for tool offset calculation")
                
                # Request current position - this will trigger our slot when response arrives
                self.octoprint_client.gcode(command='M114')
            
            self.octoprint_client.jog(z=4, absolute=True, speed=1500)
            self.octoprint_client.gcode(command='T0')

            self.main_window.calibrate_screen.show_calibrate_screen()
            self.octoprint_client.gcode(command='M104 S0')
            
            # Only turn off T1 heater for dual nozzle printers
            if is_dual_nozzle_printer():
                self.octoprint_client.gcode(command='M104 T1 S0')
                
            self.octoprint_client.gcode(command='M84')
            self.octoprint_client.gcode(
                command='M500')  # store eeprom settings to get Z home offset, mesh bed leveling back
        except Exception as e:
            self.logger.error("Error in BedLeveling.doneStep: {}".format(e))
            dialog.WarningOk(self, "Error in BedLeveling.doneStep: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass

    def cancelStep(self):
        self.logger.info("BedLeveling.cancelStep started")
        try:
            self.main_window.calibrate_screen.show_calibrate_screen()
            self.octoprint_client.home(['x', 'y', 'z'])
            self.octoprint_client.gcode(command='M104 S0')
            
            # Only turn off T1 heater for dual nozzle printers
            if is_dual_nozzle_printer():
                self.octoprint_client.gcode(command='M104 T1 S0')
                
            self.octoprint_client.gcode(command='M84')
            try:
                self.movie1.stop()
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass
        except Exception as e:
            self.logger.error("Error in BedLeveling.cancelStep: {}".format(e))
            dialog.WarningOk(self, "Error in BedLeveling.cancelStep: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass

    def on_position_updated_for_tool_offset(self, position: dict):
        """
        Handle position updates for tool offset calculation.
        This replaces the old flag-based approach with a clean signal/slot mechanism.
        """
        try:
            # Disconnect immediately to avoid multiple calls
            self.main_window.printer_model.current_position_updated.disconnect(self.on_position_updated_for_tool_offset)
            self.logger.info("Disconnected from position updates after receiving data")
            
            # Extract Z position for tool offset calculation
            if 'z' in position:
                z_position = position['z']
                self.logger.info(f"Received position for tool offset calculation: {position}")
                
                # Calculate and set tool offset using the new method
                self.calculate_and_set_tool_offset(z_position)
            else:
                self.logger.warning("Position update missing Z coordinate")
                
        except Exception as e:
            self.logger.error(f"Error in on_position_updated_for_tool_offset: {e}")
            # Ensure we disconnect even on error
            try:
                self.main_window.printer_model.current_position_updated.disconnect(self.on_position_updated_for_tool_offset)
            except:
                pass

    def calculate_and_set_tool_offset(self, current_z_position: float):
        """
        Calculate and set the tool offset based on the current Z position.
        This method implements the same logic as the old setZToolOffset but uses 
        the new signal-based position data.
        """
        try:
            self.logger.info(f"Calculating tool offset from current Z position: {current_z_position}")
            
            # Store the current position for potential future use
            self.currentZPosition = current_z_position
            
            # Calculate new tool offset: current tool offset + current Z position
            current_tool_offset_z = float(self.model.tool_offsets['Z'])
            new_tool_offset_z = current_tool_offset_z + float(current_z_position)
            
            self.logger.info(f"Current tool offset Z: {current_tool_offset_z}")
            self.logger.info(f"Current Z position: {current_z_position}")
            self.logger.info(f"New tool offset Z: {new_tool_offset_z}")
            
            # Set the tool offset using M218 command
            offset_command = f"M218 T1 Z{new_tool_offset_z}"
            self.logger.info(f"Setting tool offset with command: {offset_command}")
            self.octoprint_client.gcode(command=offset_command)
            
            # Save configuration to EEPROM
            self.octoprint_client.gcode(command='SAVE_CONFIG')
            
            self.logger.info(f"Tool Z offset set to: {new_tool_offset_z}mm and saved to EEPROM")
            
        except Exception as e:
            self.logger.error(f"Error calculating tool offset: {e}")
            dialog.WarningOk(self, f"Error calculating tool offset: {e}", overlay=True)
