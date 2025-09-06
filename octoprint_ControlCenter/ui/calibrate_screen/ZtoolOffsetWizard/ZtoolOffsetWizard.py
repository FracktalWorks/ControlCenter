import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel
from PyQt5.QtCore import QTimer
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils import dialog
import time


class ZtoolOffsetWizard(QWidget):
    """
    Z Tool Offset calibration wizard that guides the user through Z tool offset calibration.
    
    This wizard uses a 2-step process:
    1. Welcome - Introduction and preparation
    2. Calibration - Automated probe sequence for both tools
    
    Uses MVP architecture - receives probe results via model signals from printer_model.
    Properly handles existing tool offsets by adding measured differences to current values.
    """

    # Step indices for clarity and maintainability
    STEP_WELCOME = 0
    STEP_CALIBRATION = 1
    TOTAL_STEPS = 2

    def __init__(self, main_window):
        """Initialize the Z Tool Offset Wizard with UI and connections."""
        super().__init__()
        self.main_window = main_window
        self.model = main_window.printer_model
        self.octoprint_client = main_window.octoprint_client
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing Z Tool Offset Wizard")

        # Initialize state variables
        self._init_state_variables()
        
        # Load UI and initialize components
        self._load_ui()
        self._init_ui_components()
        self._connect_signals()

        self.logger.info("Z Tool Offset Wizard initialized successfully")

    def _init_state_variables(self):
        """Initialize all state tracking variables."""
        # Probe result storage
        self.probe_results = {
            'tool0': None,
            'tool1': None
        }
        self.current_probing_tool = None
        self.probe_data_collected = False

        # Signal connection tracking
        self._probe_tracking_connected = False

        # Wizard navigation state
        self._current_step = 0

    def _load_ui(self):
        """Load the UI file with proper error handling."""
        try:
            ui_file_path = os.path.join(os.path.dirname(__file__), "ZtoolOffsetWizard.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("ZtoolOffsetWizard UI loaded successfully")
        except Exception as e:
            self.logger.exception(f"Failed to load ZtoolOffsetWizard UI file: {e}")
            raise

    def _init_ui_components(self):
        """Initialize and validate all UI components."""
        # Main navigation components
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.welcomePage = self.findChild(QWidget, "welcomePage")
        self.calibrationPage = self.findChild(QWidget, "calibrationPage")
        
        # Labels for user feedback
        self.stepLabel = self.findChild(QLabel, "stepLabel")
        self.calibrationLabel = self.findChild(QLabel, "calibrationLabel")

        # Navigation buttons
        self.nextButton = self.findChild(QPushButton, "nextButton")
        self.cancelButton = self.findChild(QPushButton, "cancelButton1")

        # Validate all required UI components exist
        required_components = [
            self.stackedWidget, self.welcomePage, self.calibrationPage,
            self.nextButton, self.cancelButton, self.stepLabel, self.calibrationLabel
        ]
        check_ui_elements(self, required_components, "ZtoolOffsetWizard")

    def _connect_signals(self):
        """Connect all signal handlers."""
        # Button connections
        if self.nextButton:
            self.nextButton.clicked.connect(self.on_next_clicked)
        if self.cancelButton:
            self.cancelButton.clicked.connect(self.on_cancel_clicked)

        # Note: probe_accuracy_result_received signal is connected only when needed
        # during probe sequence, similar to how cameraToolOffsetCalibration 
        # handles current_position_updated

    # ==================== WIZARD NAVIGATION METHODS ====================

    def showEvent(self, event):
        """Reset wizard state and home axes when widget is shown."""
        super().showEvent(event)
        try:
            # Reset to welcome step
            self.goto_step(self.STEP_WELCOME)
            
            self.logger.info("Z Tool Offset calibration started - getting latest tool offsets and homing")
            
            # Validate we have necessary components
            if not self.octoprint_client:
                self.logger.error("No OctoPrint client available")
                self._show_error("Connection Error", "No OctoPrint client available. Please check connection.")
                return
                
            if not self.model:
                self.logger.error("No printer model available")
                self._show_error("Model Error", "No printer model available. Please restart the application.")
                return
            
            # Get latest M218 tool offsets from printer (similar to camera wizard)
            self.octoprint_client.gcode(command='M503')
            
            # Home all axes for consistent starting position
            self.octoprint_client.home(['x', 'y', 'z'])
            self.octoprint_client.jog(x=0, y=0, z=5, absolute=True, speed=9000)  # Raise Z slightly
            
        except Exception as e:
            self.logger.error(f"Error in ZtoolOffsetWizard showEvent: {e}")
            self._show_error("Initialization Error", str(e))

    def goto_step(self, index: int):
        """
        Switch to the specified step with proper bounds checking and setup.
        
        Args:
            index (int): Step index to navigate to
        """
        index = max(0, min(index, self.TOTAL_STEPS - 1))
        prev_step = getattr(self, "_current_step", 0)

        self._current_step = index
        
        # Update UI to show correct page
        if self.stackedWidget:
            if index == self.STEP_WELCOME:
                self.stackedWidget.setCurrentWidget(self.welcomePage)
            elif index == self.STEP_CALIBRATION:
                self.stackedWidget.setCurrentWidget(self.calibrationPage)
        
        # Update step indicator
        self._update_step_label()

        # Execute step-specific setup
        if index == self.STEP_WELCOME:
            self._setup_welcome_step()
        elif index == self.STEP_CALIBRATION:
            self._setup_calibration_step()

        self.logger.info(f"Switched to step {index + 1}/{self.TOTAL_STEPS}")

    def _update_step_label(self):
        """Update the step progress indicator."""
        if not self.stepLabel:
            return
        
        try:
            self.stepLabel.setText(f"Step {self._current_step + 1}/{self.TOTAL_STEPS}")
        except Exception as e:
            self.logger.error(f"Error updating step label: {e}")

    # ==================== STEP SETUP METHODS ====================

    def _setup_welcome_step(self):
        """Configure UI for the welcome step."""
        try:
            if self.nextButton:
                self.nextButton.setText("Start Calibration")
                self.nextButton.setEnabled(True)
        except Exception as e:
            self.logger.error(f"Error setting up welcome step: {e}")

    def _setup_calibration_step(self):
        """Configure UI and start the automated calibration process."""
        try:
            # Connect probe tracking FIRST before starting any probe operations
            self._connect_probe_tracking()
            
            # Update button to processing state
            if self.nextButton:
                self.nextButton.setText("Processing...")
                self.nextButton.setEnabled(False)
            
            # Show initial status
            if self.calibrationLabel:
                self.calibrationLabel.setText(
                    "🔧 Initializing Z Tool Offset Calibration...\n\n"
                    "• Preparing automated probe sequence\n"
                    "• Both tools will be calibrated automatically\n"
                    "• Please wait while the system measures tool heights\n\n"
                    "Status: Starting calibration..."
                )
            
            self.logger.info("Starting automated probe sequence")
            # Use QTimer to ensure signal connection is complete before starting probe sequence
            QTimer.singleShot(100, self.start_probe_sequence)
            
        except Exception as e:
            self.logger.error(f"Error setting up calibration step: {e}")
            self._show_error("Error starting calibration", str(e))

    # ==================== BUTTON HANDLERS ====================

    def on_next_clicked(self):
        """Handle next button clicks with step-based navigation."""
        self.logger.info("Next button clicked")
        try:
            if self._current_step == self.STEP_WELCOME:
                # Move to calibration step
                self.goto_step(self.STEP_CALIBRATION)
            elif self._current_step == self.STEP_CALIBRATION:
                # Only allow finishing if calibration is complete
                if self.probe_data_collected:
                    self.finish_calibration()
                else:
                    dialog.WarningOk(self, "Please wait for probe calibration to complete.", overlay=True)
                    
        except Exception as e:
            self.logger.error(f"Error in on_next_clicked: {e}")
            self._show_error("Navigation Error", str(e))

    def on_cancel_clicked(self):
        """Handle cancel button - reset wizard and return to main screen."""
        self.logger.info("Cancel button clicked")
        try:
            # Reset wizard state
            self._reset_wizard_state()
            
            # Return to tool 0 and home
            if self.octoprint_client:
                self.octoprint_client.gcode(command='T0')
                self.octoprint_client.home(['x', 'y', 'z'])
            
            # Return to main calibration screen
            if hasattr(self.main_window, 'calibrate_screen'):
                self.main_window.calibrate_screen.show_calibrate_screen()
            
        except Exception as e:
            self.logger.error(f"Error in on_cancel_clicked: {e}")
            # Still try to return to main screen even if there's an error
            if hasattr(self.main_window, 'calibrate_screen'):
                self.main_window.calibrate_screen.show_calibrate_screen()

    # ==================== PROBE SEQUENCE METHODS ====================

    def start_probe_sequence(self):
        """Initialize and start the automated probe sequence for both tools."""
        try:
            self.logger.info("Starting automated probe sequence")
            
            # Reset probe state (probe tracking is already connected in _setup_calibration_step)
            self._reset_probe_state()
            
            # Update UI with detailed progress information
            if self.calibrationLabel:
                self.calibrationLabel.setText(
                    "📍 Starting Tool 0 Calibration\n\n"
                    "• Switching to Tool 0\n"
                    "• Moving to bed center\n"
                    "• Preparing probe accuracy test\n\n"
                    "Status: Initializing Tool 0..."
                )
            
            # Begin with Tool 0
            self.probe_tool(0)
            
        except Exception as e:
            self.logger.error(f"Error starting probe sequence: {e}")
            self._show_error("Probe Sequence Error", str(e))

    def probe_tool(self, tool_number):
        """Probe a specific tool with proper sequencing"""
        try:
            self.logger.info(f"Probing tool {tool_number}")
            self.current_probing_tool = f'tool{tool_number}'
            
            # Update status for current tool being probed
            tool_desc = "Tool 0" if tool_number == 0 else "Tool 1"
            if self.calibrationLabel:
                self.calibrationLabel.setText(f"📍 {tool_desc} Probing in Progress\n\n" +
                                            f"• {tool_desc} selected and positioned\n" +
                                            f"• Running probe accuracy test\n" +
                                            f"• Collecting measurement data\n\n" +
                                            f"Status: Switching to {tool_desc}...")
            
            # Switch to the specified tool
            self.octoprint_client.gcode(command=f'T{tool_number}')
            
            # Calculate bed center position
            build_size = getattr(self.model, 'machineBuildSize', {'X': 300, 'Y': 300}) if self.model else {'X': 300, 'Y': 300}
            center_x = int(build_size.get('X', 300) / 2)  # Center of bed X
            center_y = int(build_size.get('Y', 300) / 2)  # Center of bed Y
            
            self.logger.info(f"Using bed size: {build_size.get('X')}x{build_size.get('Y')}mm, probing at center X{center_x} Y{center_y}")
            
            # Use QTimer for proper sequencing - wait for tool switch to complete
            QTimer.singleShot(3000, lambda: self._move_and_probe(tool_number, center_x, center_y))
            
        except Exception as e:
            self.logger.error(f"Error probing tool {tool_number}: {e}")
            dialog.WarningOk(self, f"Error probing tool {tool_number}: {str(e)}", overlay=True)

    def _move_and_probe(self, tool_number, center_x, center_y):
        """Move to position and start probing after tool switch completes"""
        try:
            self.logger.info(f"Moving tool {tool_number} to probe position")
            
            # Update status
            tool_desc = "Tool 0" if tool_number == 0 else "Tool 1"
            if self.calibrationLabel:
                self.calibrationLabel.setText(f"📍 {tool_desc} Probing in Progress\n\n" +
                                            f"• {tool_desc} selected and positioned\n" +
                                            f"• Moving to probe position\n" +
                                            f"• Collecting measurement data\n\n" +
                                            f"Status: Moving to probe position...")
            
            # Move to center position
            self.octoprint_client.jog(x=center_x, y=center_y, z=5, absolute=True, speed=8000)

            # Start probing after movement delay
            QTimer.singleShot(2000, lambda: self._start_probe_accuracy(tool_number))
            
        except Exception as e:
            self.logger.error(f"Error moving tool {tool_number} to probe position: {e}")
            dialog.WarningOk(self, f"Error moving tool {tool_number}: {str(e)}", overlay=True)

    def _start_probe_accuracy(self, tool_number):
        """Start the probe accuracy test"""
        try:
            self.logger.info(f"Starting probe accuracy test for tool {tool_number}")
            
            # Update status
            tool_desc = "Tool 0" if tool_number == 0 else "Tool 1"
            if self.calibrationLabel:
                self.calibrationLabel.setText(f"📍 {tool_desc} Probing in Progress\n\n" +
                                            f"• {tool_desc} selected and positioned\n" +
                                            f"• Running probe accuracy test\n" +
                                            f"• Collecting measurement data\n\n" +
                                            f"Status: Probing {tool_desc}... Please wait.")
            
            # Run probe accuracy macro with specified speed
            self.logger.info(f"Running PROBE_ACCURACY PROBE_SPEED=3 for tool {tool_number}")
            self.octoprint_client.gcode(command='PROBE_ACCURACY PROBE_SPEED=3')
            
        except Exception as e:
            self.logger.error(f"Error starting probe accuracy for tool {tool_number}: {e}")
            dialog.WarningOk(self, f"Error starting probe for tool {tool_number}: {str(e)}", overlay=True)

    def on_probe_result_received(self, tool_name, probe_data):
        """
        Handle the probe result signal - this replaces the old websocket message handler
        
        Args:
            tool_name (str): "tool0" or "tool1"
            probe_data (dict): Complete probe data with keys: maximum, minimum, range, average, median, standard_deviation
        """
        try:
            self.logger.info(f"Received probe result signal: {tool_name} = {probe_data}")
            
            # Validate we got results for the expected tool
            if self.current_probing_tool != tool_name:
                self.logger.warning(f"Received probe result for {tool_name} but expected {self.current_probing_tool}")
                # Still process it, but log the discrepancy
            
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
                    if self.calibrationLabel:
                        self.calibrationLabel.setText(f"✅ Tool 0 Complete!\n\n" +
                                                    f"• Average: {average_value:.6f}mm\n" +
                                                    f"• Std Dev: {std_dev:.6f}mm\n" +
                                                    f"• Quality: {'Good' if std_dev < 0.02 else 'Acceptable' if std_dev < 0.05 else 'Poor'}\n\n" +
                                                    f"📍 Preparing Tool 1 calibration...")
                    
                    # Use QTimer instead of blocking sleep to start tool 1 probing
                    self.logger.info("Waiting 2 seconds before probing tool 1...")
                    QTimer.singleShot(2000, lambda: self.probe_tool(1))
                    
                elif tool_name == 'tool1':
                    # Both tools done, calculate offset
                    self.logger.info("Tool 1 probing complete via signal, calculating offset")
                    if self.calibrationLabel:
                        self.calibrationLabel.setText(f"✅ Tool 1 Complete!\n\n" +
                                                    f"• Average: {average_value:.6f}mm\n" +
                                                    f"• Std Dev: {std_dev:.6f}mm\n" +
                                                    f"• Quality: {'Good' if std_dev < 0.02 else 'Acceptable' if std_dev < 0.05 else 'Poor'}\n\n" +
                                                    f"🔄 Calculating final Z offset...")
                    # Use QTimer to ensure UI updates before calculation
                    QTimer.singleShot(500, self.calculate_z_offset)
            else:
                self.logger.error(f"Invalid tool_name received: {tool_name}")
                
        except Exception as e:
            self.logger.error(f"Error in on_probe_result_received: {e}")
            # Disconnect probe tracking on error to prevent memory leaks
            self._disconnect_probe_tracking()
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
                raw_z_diff = tool0_avg - tool1_avg
                
                # Get current Z tool offset from printer model
                current_z_offset = self._get_current_z_offset()
                
                # Calculate new Z offset (current + measured difference)
                new_z_offset = round(current_z_offset + raw_z_diff, 6)
                
                # Extract standard deviations for quality assessment
                tool0_std = tool0_data.get('standard_deviation', 0.0)
                tool1_std = tool1_data.get('standard_deviation', 0.0)
                
                self.logger.info(f"Probe results - Tool 0: avg={tool0_avg:.6f}, std={tool0_std:.6f}")
                self.logger.info(f"Probe results - Tool 1: avg={tool1_avg:.6f}, std={tool1_std:.6f}")
                self.logger.info(f"Raw Z difference (T0-T1): {raw_z_diff:.6f}")
                self.logger.info(f"Current Z offset: {current_z_offset:.6f}")
                self.logger.info(f"New Z offset to apply: {new_z_offset:.6f}")
                
                # Determine quality indicators
                tool0_quality = 'Excellent' if tool0_std < 0.01 else 'Good' if tool0_std < 0.02 else 'Acceptable' if tool0_std < 0.05 else 'Poor'
                tool1_quality = 'Excellent' if tool1_std < 0.01 else 'Good' if tool1_std < 0.02 else 'Acceptable' if tool1_std < 0.05 else 'Poor'
                
                # Update UI with comprehensive results including offset information
                self.calibrationLabel.setText(f"🎯 CALIBRATION COMPLETE!\n\n" +
                                            f"📊 PROBE RESULTS:\n" +
                                            f"Tool 0: {tool0_avg:.6f}mm (±{tool0_std:.6f}) [{tool0_quality}]\n" +
                                            f"Tool 1: {tool1_avg:.6f}mm (±{tool1_std:.6f}) [{tool1_quality}]\n\n" +
                                            f"� HEIGHT DIFFERENCE:\n" +
                                            f"Raw Difference (T0-T1): {raw_z_diff:.6f}mm\n\n" +
                                            f"🔧 Z TOOL OFFSETS:\n" +
                                            f"Current Z Offset: {current_z_offset:.6f}mm\n" +
                                            f"New Z Offset: {new_z_offset:.6f}mm\n\n" +
                                            f"✅ Ready to apply new offset to printer configuration.\n" +
                                            f"Click 'Apply Offset' to save and return to menu.")
                
                # Enable the finish button with new text
                if self.nextButton:
                    self.nextButton.setText("Apply Offset")
                    self.nextButton.setEnabled(True)
                
                # Mark data as collected
                self.probe_data_collected = True
                self.logger.info(f"Z offset calculation complete: raw_diff={raw_z_diff:.6f}mm, new_offset={new_z_offset:.6f}mm")
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
        self.logger.info("ZtoolOffsetWizard.finish_calibration started")
        try:
            # Disconnect probe tracking since calibration is complete
            self._disconnect_probe_tracking()
            
            # Update status to show applying offset
            if self.calibrationLabel:
                self.calibrationLabel.setText(
                    "🔧 APPLYING Z OFFSET...\n\n"
                    "• Saving offset to printer configuration\n"
                    "• Writing to EEPROM\n"
                    "• Returning to Tool 0\n"
                    "• Homing axes\n\n"
                    "Please wait..."
                )
            
            # Disable button during application
            if self.nextButton:
                self.nextButton.setEnabled(False)
                self.nextButton.setText("Applying...")
            
            # Apply the calculated Z offset if both tools were probed
            if (self.probe_results.get('tool0') is not None and 
                self.probe_results.get('tool1') is not None):
                
                tool0_avg = self.probe_results['tool0'].get('average', 0.0)
                tool1_avg = self.probe_results['tool1'].get('average', 0.0)
                raw_z_diff = tool0_avg - tool1_avg
                
                # Get current Z tool offset from printer model (similar to camera wizard)
                current_z_offset = self._get_current_z_offset()
                
                # Add the measured difference to the existing offset
                new_z_offset = round(current_z_offset + raw_z_diff, 6)
                
                self.logger.info(f"Current Z offset: {current_z_offset:.6f}mm")
                self.logger.info(f"Measured Z difference: {raw_z_diff:.6f}mm")
                self.logger.info(f"New Z offset to apply: {new_z_offset:.6f}mm")
                
                self.apply_z_offset(new_z_offset)
            else:
                self.logger.warning("Cannot apply Z offset - missing probe data")
            
            # Return to tool 0 and home
            if self.octoprint_client:
                self.octoprint_client.gcode(command='T0')
                self.octoprint_client.home(['x', 'y', 'z'])
            
            # Return to main calibration screen
            if hasattr(self.main_window, 'calibrate_screen'):
                self.main_window.calibrate_screen.show_calibrate_screen()
            
        except Exception as e:
            self.logger.error(f"Error in ZtoolOffsetWizard.finish_calibration: {e}")
            self._show_error("Calibration Finish Error", str(e))

    # ==================== UTILITY AND HELPER METHODS ====================

    def _reset_wizard_state(self):
        """Reset all wizard state variables to initial values."""
        # Disconnect probe tracking if connected
        self._disconnect_probe_tracking()
        
        # Reset to welcome step
        self.goto_step(self.STEP_WELCOME)
        
        # Reset probe data
        self._reset_probe_state()

    def _reset_probe_state(self):
        """Reset probe-related state variables."""
        self.probe_results = {'tool0': None, 'tool1': None}
        self.probe_data_collected = False
        self.current_probing_tool = None

    def _show_error(self, title, message):
        """Show error dialog with consistent styling."""
        self.logger.error(f"{title}: {message}")
        dialog.WarningOk(self, f"{title}\n\n{message}", overlay=True)

    def _get_current_z_offset(self):
        """Get the current Z tool offset from the printer model."""
        try:
            if self.model and hasattr(self.model, 'tool_offsets'):
                current_z_offset = float(self.model.tool_offsets.get('Z', 0))
                self.logger.debug(f"Current Z offset from model: {current_z_offset}")
                return current_z_offset
            else:
                self.logger.warning("No printer model or tool_offsets available, using 0.0")
                return 0.0
        except (ValueError, AttributeError) as e:
            self.logger.warning(f"Error getting current Z offset: {e}, using 0.0")
            return 0.0

    def _connect_probe_tracking(self):
        """Connect probe tracking when needed for receiving probe results."""
        if not self._probe_tracking_connected and self.model:
            try:
                self.model.probe_accuracy_result_received.connect(self.on_probe_result_received)
                self._probe_tracking_connected = True
                self.logger.info("Probe tracking connected successfully")
            except Exception as e:
                self.logger.error(f"Failed to connect probe tracking: {e}")
                raise
    
    def _disconnect_probe_tracking(self):
        """Disconnect probe tracking when no longer needed."""
        if self._probe_tracking_connected and self.model:
            try:
                self.model.probe_accuracy_result_received.disconnect(self.on_probe_result_received)
                self._probe_tracking_connected = False
                self.logger.info("Probe tracking disconnected successfully")
            except (TypeError, AttributeError) as e:
                # Signal was already disconnected or doesn't exist
                self._probe_tracking_connected = False
                self.logger.debug(f"Probe tracking was already disconnected: {e}")
            except Exception as e:
                self.logger.error(f"Error disconnecting probe tracking: {e}")
                self._probe_tracking_connected = False
