import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils import dialog
import time


class ZProbeOffsetPage(QWidget):
    """
    Z Probe Offset calibration widget that guides the user through Z probe offset calibration
    Uses MVP architecture - receives probe results via model signals
    """

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.model = main_window.printer_model
        self.octoprint_client = main_window.octoprint_client
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing Z Probe Offset screen")

        # Initialize probe result variables
        self.probe_results = {
            'tool0': None,
            'tool1': None
        }
        self.current_probing_tool = None
        self.probe_data_collected = False

        try:
            # Use relative path from the current module's directory
            ui_file_path = os.path.join(os.path.dirname(__file__), "zProbeOffsetPage.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("ZProbeOffsetPage UI loaded successfully")
        except Exception as e:
            self.logger.exception(f"Failed to load ZProbeOffsetPage UI file: {e}")

        # Initialize the Pages
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.welcomePage = self.findChild(QWidget, "welcomePage")
        self.calibrationPage = self.findChild(QWidget, "calibrationPage")
        
        # Initialize step label
        self.stepLabel = self.findChild(QLabel, "stepLabel")
        
        # Initialize calibration label for status updates
        self.calibrationLabel = self.findChild(QLabel, "calibrationLabel")

        # Initialize buttons
        self.nextButton1 = self.findChild(QPushButton, "nextButton1")
        self.cancelButton1 = self.findChild(QPushButton, "cancelButton1")

        # Validate UI components
        check_ui_elements(self, [
            self.stackedWidget, self.welcomePage, self.calibrationPage,
            self.nextButton1, self.cancelButton1, self.stepLabel, self.calibrationLabel
        ], "ZProbeOffsetPage")

        # Connect button signals
        if self.nextButton1:
            self.nextButton1.clicked.connect(self.handle_next_button)
        if self.cancelButton1:
            self.cancelButton1.clicked.connect(self.cancel_calibration)

        # Connect the probe result signal from model (MVP architecture)
        self.model.probe_accuracy_result_received.connect(self.on_probe_result_received)

        # Start with the welcome page
        if self.stackedWidget and self.welcomePage:
            self.stackedWidget.setCurrentWidget(self.welcomePage)
            self.update_step_label()

    def update_step_label(self):
        """Update the step label based on current page"""
        if not self.stepLabel or not self.stackedWidget:
            return
            
        if self.stackedWidget.currentWidget() == self.welcomePage:
            self.stepLabel.setText("Step 1/2")
        elif self.stackedWidget.currentWidget() == self.calibrationPage:
            self.stepLabel.setText("Step 2/2")

    def showEvent(self, event):
        """Reset to welcome page and home axes when this widget is shown."""
        super().showEvent(event)
        try:
            if self.stackedWidget and self.welcomePage:
                self.stackedWidget.setCurrentWidget(self.welcomePage)
                self.update_step_label()
            
            # Reset button text to "Next" in case we're returning from calibration page
            if self.nextButton1:
                self.nextButton1.setText("Next")
            
            self.logger.info("Z Probe Offset calibration started - homing all axes")
            # Home all axes immediately when the wizard opens, following the pattern of other wizards
            self.octoprint_client.home(['x', 'y', 'z'])
            
        except Exception as e:
            self.logger.error(f"Error in ZProbeOffsetPage showEvent: {e}")

    def handle_next_button(self):
        """Handle the next button based on current page"""
        self.logger.info("ZProbeOffsetPage.handle_next_button started")
        try:
            if self.stackedWidget and self.welcomePage and self.calibrationPage:
                if self.stackedWidget.currentWidget() == self.welcomePage:
                    # Move to calibration page and start probing sequence
                    self.stackedWidget.setCurrentWidget(self.calibrationPage)
                    self.update_step_label()
                    if self.nextButton1:
                        self.nextButton1.setText("Processing...")
                        self.nextButton1.setEnabled(False)
                    self.logger.info("Moved to calibration page - starting probe sequence")
                    
                    # Start the automated probing sequence
                    self.start_probe_sequence()
                    
                elif self.stackedWidget.currentWidget() == self.calibrationPage:
                    # Only allow finishing if probing is complete
                    if self.probe_data_collected:
                        self.finish_calibration()
                    else:
                        dialog.WarningOk(self, "Please wait for probe calibration to complete.", overlay=True)
                        
        except Exception as e:
            self.logger.error(f"Error in ZProbeOffsetPage.handle_next_button: {e}")
            dialog.WarningOk(self, f"Error handling next button: {str(e)}", overlay=True)

    def start_probe_sequence(self):
        """Start the automated probe sequence for both tools"""
        try:
            self.logger.info("Starting automated probe sequence")
            
            # Reset probe results
            self.probe_results = {'tool0': None, 'tool1': None}
            self.probe_data_collected = False
            self.current_probing_tool = 'tool0'
            
            # Update status label to show current progress
            self.calibrationLabel.setText("Starting Z probe calibration...\n\nTool 0 - Moving to center and starting probe accuracy test.")
            
            # Start with Tool 0
            self.probe_tool(0)
            
        except Exception as e:
            self.logger.error(f"Error starting probe sequence: {e}")
            dialog.WarningOk(self, f"Error starting probe sequence: {str(e)}", overlay=True)

    def probe_tool(self, tool_number):
        """Probe a specific tool"""
        try:
            self.logger.info(f"Probing tool {tool_number}")
            self.current_probing_tool = f'tool{tool_number}'
            
            # Switch to the specified tool
            self.octoprint_client.gcode(command=f'T{tool_number}')
            
            # Move to center of bed (you may need to adjust these coordinates)
            center_x = self.model.calibrationPosition.get('X4', 150)  # Default to 150 if not found
            center_y = self.model.calibrationPosition.get('Y4', 150)  # Default to 150 if not found
            
            # Move to center position
            self.octoprint_client.jog(x=center_x, y=center_y, absolute=True, speed=5000)
            
            # Wait a moment for movement to complete, then start probe accuracy
            time.sleep(2)
            
            # Run probe accuracy macro with specified speed
            self.logger.info(f"Running PROBE_ACCURACY PROBE_SPEED=3 for tool {tool_number}")
            self.octoprint_client.gcode(command='PROBE_ACCURACY PROBE_SPEED=3')
            
        except Exception as e:
            self.logger.error(f"Error probing tool {tool_number}: {e}")
            dialog.WarningOk(self, f"Error probing tool {tool_number}: {str(e)}", overlay=True)

    def on_probe_result_received(self, tool_name, probe_data):
        """
        Handle the probe result signal - this replaces the old websocket message handler
        
        Args:
            tool_name (str): "tool0" or "tool1"
            probe_data (dict): Complete probe data with keys: maximum, minimum, range, average, median, standard_deviation
        """
        try:
            self.logger.info(f"Received probe result signal: {tool_name} = {probe_data}")
            
            # Store the complete probe data for the specified tool
            if tool_name in self.probe_results:
                self.probe_results[tool_name] = probe_data
                
                # Get the average value for display and calculations
                average_value = probe_data.get('average', 0.0)
                std_dev = probe_data.get('standard_deviation', 0.0)
                
                # Update UI and proceed based on which tool was just probed
                if tool_name == 'tool0' and self.probe_results['tool1'] is None:
                    # Tool 0 done, now probe tool 1
                    self.logger.info("Tool 0 probing complete via signal, starting tool 1")
                    self.calibrationLabel.setText(f"Tool 0 complete!\nAvg: {average_value:.6f}mm, Std Dev: {std_dev:.6f}mm\n\nTool 1 - Moving to center and starting probe accuracy test.")
                    
                    # Small delay before starting tool 1
                    self.logger.info("Waiting 2 seconds before probing tool 1...")
                    time.sleep(2)
                    self.probe_tool(1)
                    
                elif tool_name == 'tool1':
                    # Both tools done, calculate offset
                    self.logger.info("Tool 1 probing complete via signal, calculating offset")
                    self.calibrationLabel.setText(f"Tool 1 complete!\nAvg: {average_value:.6f}mm, Std Dev: {std_dev:.6f}mm\n\nCalculating Z offset...")
                    self.calculate_z_offset()
            else:
                self.logger.error(f"Invalid tool_name received: {tool_name}")
                
        except Exception as e:
            self.logger.error(f"Error in on_probe_result_received: {e}")
            dialog.WarningOk(self, f"Error processing probe result: {str(e)}", overlay=True)

    def calculate_z_offset(self):
        """Calculate the Z offset between the two tools using complete probe data"""
        try:
            if self.probe_results['tool0'] is not None and self.probe_results['tool1'] is not None:
                tool0_data = self.probe_results['tool0']
                tool1_data = self.probe_results['tool1']
                
                # Extract average values for offset calculation
                tool0_avg = tool0_data.get('average', 0.0)
                tool1_avg = tool1_data.get('average', 0.0)
                z_offset = tool0_avg - tool1_avg
                
                # Extract standard deviations for quality assessment
                tool0_std = tool0_data.get('standard_deviation', 0.0)
                tool1_std = tool1_data.get('standard_deviation', 0.0)
                
                self.logger.info(f"Probe results - Tool 0: avg={tool0_avg:.6f}, std={tool0_std:.6f}")
                self.logger.info(f"Probe results - Tool 1: avg={tool1_avg:.6f}, std={tool1_std:.6f}")
                self.logger.info(f"Calculated Z offset: {z_offset:.6f}")
                
                # Update UI with comprehensive results
                self.calibrationLabel.setText(f"Z Probe Offset Calibration Complete!\n\n"
                                            f"Tool 0: {tool0_avg:.6f}mm (±{tool0_std:.6f})\n"
                                            f"Tool 1: {tool1_avg:.6f}mm (±{tool1_std:.6f})\n\n"
                                            f"Calculated Z offset: {z_offset:.6f}mm\n\n"
                                            f"Click Finish to apply the offset and return to calibration menu.")
                
                # Enable the finish button
                if self.nextButton1:
                    self.nextButton1.setText("Finish")
                    self.nextButton1.setEnabled(True)
                
                # Mark data as collected
                self.probe_data_collected = True
                self.logger.info(f"Z offset calculation complete: {z_offset:.6f}mm")
            else:
                self.logger.warning("Cannot calculate Z offset - missing probe data for one or both tools")
                
        except Exception as e:
            self.logger.error(f"Error in calculate_z_offset: {e}")
            dialog.WarningOk(self, f"Error calculating Z offset: {str(e)}", overlay=True)

    def apply_z_offset(self, z_offset):
        """Apply the calculated Z offset to the printer configuration"""
        try:
            self.logger.info(f"Applying Z offset: {z_offset:.6f}")
            
            # Set the tool offset using M218 command
            offset_command = f"M218 T1 Z{z_offset:.6f}"
            self.logger.info(f"Setting tool Z offset with command: {offset_command}")
            self.octoprint_client.gcode(command=offset_command)
            
            # Save to EEPROM
            self.octoprint_client.gcode(command='M500')
            
            self.logger.info(f"Z offset {z_offset:.6f} applied and saved to EEPROM")
            
        except Exception as e:
            self.logger.error(f"Error applying Z offset: {e}")
            dialog.WarningOk(self, f"Error applying Z offset: {str(e)}", overlay=True)

    def finish_calibration(self):
        """Finish the calibration and return to main calibration screen."""
        self.logger.info("ZProbeOffsetPage.finish_calibration started")
        try:
            # Apply the calculated Z offset if both tools were probed
            if (self.probe_results.get('tool0') is not None and 
                self.probe_results.get('tool1') is not None):
                
                tool0_avg = self.probe_results['tool0'].get('average', 0.0)
                tool1_avg = self.probe_results['tool1'].get('average', 0.0)
                z_offset = tool0_avg - tool1_avg
                
                self.logger.info(f"Applying calculated Z offset: {z_offset:.6f}mm")
                self.apply_z_offset(z_offset)
            else:
                self.logger.warning("Cannot apply Z offset - missing probe data")
            
            # Return to tool 0
            self.octoprint_client.gcode(command='T0')
            
            # Home all axes and return to calibration screen
            self.octoprint_client.home(['x', 'y', 'z'])
            self.main_window.calibrate_screen.show_calibrate_screen()
            
        except Exception as e:
            self.logger.error(f"Error in ZProbeOffsetPage.finish_calibration: {e}")
            dialog.WarningOk(self, f"Error finishing calibration: {str(e)}", overlay=True)

    def cancel_calibration(self):
        """Cancel the calibration and return to main calibration screen."""
        self.logger.info("ZProbeOffsetPage.cancel_calibration started")
        try:
            # Reset button text and go back to welcome page
            if self.nextButton1:
                self.nextButton1.setText("Next")
                self.nextButton1.setEnabled(True)
            if self.stackedWidget and self.welcomePage:
                self.stackedWidget.setCurrentWidget(self.welcomePage)
                self.update_step_label()
            
            # Reset probe data
            self.probe_results = {'tool0': None, 'tool1': None}
            self.probe_data_collected = False
            self.current_probing_tool = None
            
            # Return to tool 0
            self.octoprint_client.gcode(command='T0')
            
            self.octoprint_client.home(['x', 'y', 'z'])
            self.main_window.calibrate_screen.show_calibrate_screen()
            
        except Exception as e:
            self.logger.error(f"Error in ZProbeOffsetPage.cancel_calibration: {e}")
            dialog.WarningOk(self, f"Error canceling calibration: {str(e)}", overlay=True)
