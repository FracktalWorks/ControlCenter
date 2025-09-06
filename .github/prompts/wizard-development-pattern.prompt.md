---
mode: 'reference'
description: 'Comprehensive wizard development pattern and template for ControlCenter'
---

# Wizard Development Pattern

This document provides the complete template and pattern for creating wizards in the ControlCenter project, based on proven implementations like ZtoolOffsetWizard and cameraToolOffsetCalibration.

## Complete Wizard Template

```python
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils import dialog
import time


class WizardName(QWidget):
    """
    Brief description of wizard purpose.
    
    This wizard uses a N-step process:
    1. Welcome - Introduction and preparation
    2. Operation - Main wizard operation
    ...
    
    Uses MVP architecture - receives data via model signals from printer_model.
    Properly handles existing configurations by adding/updating current values.
    """

    # Step indices for clarity and maintainability
    STEP_WELCOME = 0
    STEP_OPERATION = 1
    TOTAL_STEPS = 2

    def __init__(self, main_window):
        """Initialize the Wizard with UI and connections."""
        super().__init__()
        self.main_window = main_window
        self.model = main_window.printer_model
        self.octoprint_client = main_window.octoprint_client
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing Wizard")

        # Initialize state variables
        self._init_state_variables()
        
        # Load UI and initialize components
        self._load_ui()
        self._init_ui_components()
        self._connect_signals()

        self.logger.info("Wizard initialized successfully")

    def _init_state_variables(self):
        """Initialize all state tracking variables."""
        # Data storage
        self.wizard_data = {}
        self.operation_complete = False

        # Signal connection tracking
        self._signal_tracking_connected = False

        # Wizard navigation state
        self._current_step = 0

    def _load_ui(self):
        """Load the UI file with proper error handling."""
        try:
            ui_file_path = os.path.join(os.path.dirname(__file__), "WizardName.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("WizardName UI loaded successfully")
        except Exception as e:
            self.logger.exception(f"Failed to load WizardName UI file: {e}")
            raise

    def _init_ui_components(self):
        """Initialize and validate all UI components."""
        # Main navigation components
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.welcomePage = self.findChild(QWidget, "welcomePage")
        self.operationPage = self.findChild(QWidget, "operationPage")
        
        # Labels for user feedback
        self.stepLabel = self.findChild(QLabel, "stepLabel")
        self.statusLabel = self.findChild(QLabel, "statusLabel")

        # Navigation buttons
        self.nextButton = self.findChild(QPushButton, "nextButton")
        self.cancelButton = self.findChild(QPushButton, "cancelButton1")  # Often cancelButton1

        # Validate all required UI components exist
        required_components = [
            self.stackedWidget, self.welcomePage, self.operationPage,
            self.nextButton, self.cancelButton, self.stepLabel, self.statusLabel
        ]
        check_ui_elements(self, required_components, "WizardName")

    def _connect_signals(self):
        """Connect all signal handlers."""
        # Button connections
        if self.nextButton:
            self.nextButton.clicked.connect(self.on_next_clicked)
        if self.cancelButton:
            self.cancelButton.clicked.connect(self.on_cancel_clicked)

        # Note: Model signals are connected only when needed
        # during operations, similar to how cameraToolOffsetCalibration 
        # handles current_position_updated

    # ==================== WIZARD NAVIGATION METHODS ====================

    def showEvent(self, event):
        """Reset wizard state when widget is shown."""
        super().showEvent(event)
        try:
            # Reset to welcome step
            self.goto_step(self.STEP_WELCOME)
            
            self.logger.info("Wizard started - getting latest configuration")
            
            # Get latest configuration from printer (similar to camera wizard)
            if self.octoprint_client:
                self.octoprint_client.gcode(command='M503')
                
            # Initialize printer state if needed
            if self.octoprint_client:
                self.octoprint_client.home(['x', 'y', 'z'])
            
        except Exception as e:
            self.logger.error(f"Error in showEvent: {e}")

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
            elif index == self.STEP_OPERATION:
                self.stackedWidget.setCurrentWidget(self.operationPage)
        
        # Update step indicator
        self._update_step_label()

        # Execute step-specific setup
        if index == self.STEP_WELCOME:
            self._setup_welcome_step()
        elif index == self.STEP_OPERATION:
            self._setup_operation_step()

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
                self.nextButton.setText("Start Operation")
                self.nextButton.setEnabled(True)
        except Exception as e:
            self.logger.error(f"Error setting up welcome step: {e}")

    def _setup_operation_step(self):
        """Configure UI and start the main operation."""
        try:
            # Update button to processing state
            if self.nextButton:
                self.nextButton.setText("Processing...")
                self.nextButton.setEnabled(False)
            
            # Show initial status
            if self.statusLabel:
                self.statusLabel.setText("Starting operation...")
            
            self.logger.info("Starting main operation")
            # Begin the main operation
            self.start_operation()
            
        except Exception as e:
            self.logger.error(f"Error setting up operation step: {e}")
            self._show_error("Error starting operation", str(e))

    # ==================== BUTTON HANDLERS ====================

    def on_next_clicked(self):
        """Handle next button clicks with step-based navigation."""
        self.logger.info("Next button clicked")
        try:
            if self._current_step == self.STEP_WELCOME:
                # Move to operation step
                self.goto_step(self.STEP_OPERATION)
            elif self._current_step == self.STEP_OPERATION:
                # Only allow finishing if operation is complete
                if self.operation_complete:
                    self.finish_wizard()
                else:
                    dialog.WarningOk(self, "Please wait for operation to complete.", overlay=True)
                    
        except Exception as e:
            self.logger.error(f"Error in on_next_clicked: {e}")
            self._show_error("Navigation Error", str(e))

    def on_cancel_clicked(self):
        """Handle cancel button - reset wizard and return to main screen."""
        self.logger.info("Cancel button clicked")
        try:
            # Reset wizard state
            self._reset_wizard_state()
            
            # Return to safe state
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

    # ==================== OPERATION METHODS ====================

    def start_operation(self):
        """Initialize and start the main operation."""
        try:
            self.logger.info("Starting main operation")
            
            # Connect signal tracking for this operation
            self._connect_tracking()
            
            # Reset operation state
            self._reset_operation_state()
            
            # Update UI with progress information
            if self.statusLabel:
                self.statusLabel.setText("Operation in progress...")
            
            # Begin the operation
            self.perform_operation()
            
        except Exception as e:
            self.logger.error(f"Error starting operation: {e}")
            self._show_error("Operation Error", str(e))

    def perform_operation(self):
        """Perform the main wizard operation."""
        try:
            # Use machineBuildSize for bed center calculations
            build_size = getattr(self.model, 'machineBuildSize', {'X': 300, 'Y': 300}) if self.model else {'X': 300, 'Y': 300}
            center_x = int(build_size.get('X', 300) / 2)  # Center of bed X
            center_y = int(build_size.get('Y', 300) / 2)  # Center of bed Y
            
            self.logger.info(f"Using bed size: {build_size.get('X')}x{build_size.get('Y')}mm, operating at center X{center_x} Y{center_y}")
            
            # Move to center position
            self.octoprint_client.jog(x=center_x, y=center_y, absolute=True, speed=5000)
            
            # Perform operation-specific tasks
            # ... operation implementation here ...
            
        except Exception as e:
            self.logger.error(f"Error performing operation: {e}")
            dialog.WarningOk(self, f"Error performing operation: {str(e)}", overlay=True)

    def on_signal_received(self, data):
        """
        Handle signals from the printer model.
        
        Args:
            data: Signal data from printer_model
        """
        try:
            self.logger.info(f"Received signal: {data}")
            
            # Process the signal data
            self.wizard_data.update(data)
            
            # Update UI and proceed based on signal
            self.process_signal_data(data)
            
        except Exception as e:
            self.logger.error(f"Error processing signal: {e}")
            # Disconnect tracking on error to prevent memory leaks
            self._disconnect_tracking()
            dialog.WarningOk(self, f"Error processing signal: {str(e)}", overlay=True)

    def process_signal_data(self, data):
        """Process received signal data and update wizard state."""
        try:
            # Process data and update UI
            if self.statusLabel:
                self.statusLabel.setText("Operation complete!")
            
            # Enable finish button
            if self.nextButton:
                self.nextButton.setText("Finish")
                self.nextButton.setEnabled(True)
            
            # Mark operation as complete
            self.operation_complete = True
            self.logger.info("Operation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error processing signal data: {e}")

    def finish_wizard(self):
        """Finish the wizard and return to main screen."""
        self.logger.info("Wizard finishing")
        try:
            # Disconnect tracking since operation is complete
            self._disconnect_tracking()
            
            # Update status to show completion
            if self.statusLabel:
                self.statusLabel.setText("Applying changes...")
            
            # Disable button during completion
            if self.nextButton:
                self.nextButton.setEnabled(False)
                self.nextButton.setText("Finishing...")
            
            # Apply any necessary changes
            self.apply_changes()
            
            # Return to safe state
            if self.octoprint_client:
                self.octoprint_client.gcode(command='T0')
                self.octoprint_client.home(['x', 'y', 'z'])
            
            # Return to main calibration screen
            if hasattr(self.main_window, 'calibrate_screen'):
                self.main_window.calibrate_screen.show_calibrate_screen()
            
        except Exception as e:
            self.logger.error(f"Error finishing wizard: {e}")
            self._show_error("Wizard Finish Error", str(e))

    def apply_changes(self):
        """Apply the wizard results to printer configuration."""
        try:
            self.logger.info("Applying wizard changes")
            
            # Apply configuration changes
            # Example: self.octoprint_client.gcode(command='M218 T1 X{value}')
            # Example: self.octoprint_client.gcode(command='M500')  # Save to EEPROM
            
            self.logger.info("Wizard changes applied successfully")
            
        except Exception as e:
            self.logger.error(f"Error applying changes: {e}")
            dialog.WarningOk(self, f"Error applying changes: {str(e)}", overlay=True)

    # ==================== UTILITY AND HELPER METHODS ====================

    def _reset_wizard_state(self):
        """Reset all wizard state variables to initial values."""
        # Disconnect tracking if connected
        self._disconnect_tracking()
        
        # Reset to welcome step
        self.goto_step(self.STEP_WELCOME)
        
        # Reset data
        self._reset_operation_state()

    def _reset_operation_state(self):
        """Reset operation-specific state variables."""
        self.wizard_data = {}
        self.operation_complete = False

    def _show_error(self, title, message):
        """Show error dialog with consistent styling."""
        self.logger.error(f"{title}: {message}")
        dialog.WarningOk(self, f"{title}\n\n{message}", overlay=True)

    def _get_current_config_value(self, key, default=0.0):
        """Get current configuration value from printer model."""
        try:
            if self.model and hasattr(self.model, 'tool_offsets'):
                value = float(self.model.tool_offsets.get(key, default))
                self.logger.debug(f"Current {key} from model: {value}")
                return value
            else:
                self.logger.warning(f"No printer model or config available for {key}, using {default}")
                return default
        except (ValueError, AttributeError) as e:
            self.logger.warning(f"Error getting {key}: {e}, using {default}")
            return default

    def _connect_tracking(self):
        """Connect tracking when needed for receiving signals."""
        if not self._signal_tracking_connected and self.model:
            self.model.signal_name.connect(self.on_signal_received)
            self._signal_tracking_connected = True
            self.logger.debug("Signal tracking connected")
    
    def _disconnect_tracking(self):
        """Disconnect tracking when no longer needed."""
        if self._signal_tracking_connected and self.model:
            try:
                self.model.signal_name.disconnect(self.on_signal_received)
                self._signal_tracking_connected = False
                self.logger.debug("Signal tracking disconnected")
            except TypeError:
                # Signal was already disconnected
                self._signal_tracking_connected = False
```

## UI File Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>WizardName</class>
 <widget class="QWidget" name="WizardName">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>800</width>
    <height>480</height>
   </rect>
  </property>
  <property name="minimumSize">
   <size>
    <width>800</width>
    <height>480</height>
   </size>
  </property>
  <property name="maximumSize">
   <size>
    <width>800</width>
    <height>480</height>
   </size>
  </property>
  <property name="styleSheet">
   <string notr="true">background-color: rgb(40, 40, 40);</string>
  </property>
  <layout class="QVBoxLayout" name="verticalLayout">
   <item>
    <widget class="QLabel" name="stepLabel">
     <property name="text">
      <string>Step 1/2</string>
     </property>
    </widget>
   </item>
   <item>
    <widget class="QStackedWidget" name="stackedWidget">
     <property name="currentIndex">
      <number>0</number>
     </property>
     <widget class="QWidget" name="welcomePage">
      <layout class="QVBoxLayout" name="welcomeLayout">
       <item>
        <widget class="QLabel" name="welcomeLabel">
         <property name="text">
          <string>Welcome to Wizard</string>
         </property>
        </widget>
       </item>
      </layout>
     </widget>
     <widget class="QWidget" name="operationPage">
      <layout class="QVBoxLayout" name="operationLayout">
       <item>
        <widget class="QLabel" name="statusLabel">
         <property name="text">
          <string>Operation Status</string>
         </property>
        </widget>
       </item>
      </layout>
     </widget>
    </widget>
   </item>
   <item>
    <layout class="QHBoxLayout" name="buttonLayout">
     <item>
      <widget class="QPushButton" name="cancelButton1">
       <property name="text">
        <string>Cancel</string>
       </property>
      </widget>
     </item>
     <item>
      <widget class="QPushButton" name="nextButton">
       <property name="text">
        <string>Next</string>
       </property>
      </widget>
     </item>
    </layout>
   </item>
  </layout>
 </widget>
</ui>
```

## Key Pattern Points

1. **Step Constants**: Use STEP_NAME = index pattern with TOTAL_STEPS
2. **goto_step Method**: Central navigation with bounds checking and step setup
3. **Signal Management**: Dynamic connection/disconnection pattern
4. **M503 Integration**: Send M503 on showEvent for latest configuration
5. **machineBuildSize**: Use for bed center calculations, not calibrationPosition
6. **Error Handling**: Consistent _show_error method and try-catch blocks
7. **State Management**: Proper reset methods and state tracking
8. **UI Validation**: Use check_ui_elements for component validation
9. **Button Naming**: Often "cancelButton1" in UI files, not "cancelButton"
10. **Resource Cleanup**: Disconnect signals on errors and completion

This pattern ensures consistency, maintainability, and reliability across all wizards in the ControlCenter project.
