# Custom Instructions for ControlCenter Development

## Project Context
This project is a PyQt5-based touchscreen interface for 3D printer control, specifically designed for OctoPrint and Klipper firmware integration. The application runs on Raspberry Pi hardware with an 800x480 touchscreen display.

## Architecture
- **Framework**: PyQt5 with Qt Designer for UI files
- **Pattern**: Model-View-Presenter (MVP) architecture
- **Integration**: OctoPrint REST API and WebSocket communication
- **Target Hardware**: Raspberry Pi with 800x480 touchscreen
- **Firmware**: Klipper with dynamic configuration system

## Coding Style
- Use camelCase for UI element names in Qt Designer
- Use PascalCase for class names
- Use snake_case for Python variables and functions
- Always include proper error handling with try-catch blocks
- Use centralized logging with `get_logger(self.__class__.__name__)`
- Prefer descriptive variable names over short abbreviations

## File Structure
- Python files: `[module_name].py`
- UI files: `[module_name].ui` (matching Python class name)
- Place UI files in same directory as Python files
- Use relative paths for loading UI files: `os.path.join(os.path.dirname(__file__), "file.ui")`

## UI Design Standards
- **Fixed Resolution**: Always 800x480 pixels with min/max size constraints
- **Theme**: Dark theme with `background-color: rgb(40, 40, 40);`
- **Touch Targets**: Minimum 44px height for interactive elements
- **Navigation**: Include back/cancel buttons for all screens
- **Wizards**: Use QStackedWidget for multi-step interfaces

## UI Element Naming Conventions
```
QStackedWidget: stackedWidget, [purpose]StackedWidget
QPushButton: backButton, nextButton, cancelButton, [action]Button
QLabel: [content]Label, [purpose]Label, statusLabel
QProgressBar: progressBar, [operation]ProgressBar
QSpinBox: [parameter]SpinBox, temperatureSpinBox
QWidget (pages): mainPage, [step]Page, [purpose]Page
```

## Error Handling
- Wrap all OctoPrint operations in try-catch blocks
- Use `dialog.WarningOk()` for user notifications
- Use `dialog.WarningYesNo()` for confirmations
- Log all errors with appropriate context
- Provide fallback behaviors for failed operations

## Integration Patterns
### Calibrate Screen Integration
1. Import in `octoprint_ControlCenter/ui/calibrate_screen/calibrate_screen.py`
2. Add to `_initialize_sub_screens()` method
3. Connect button in `__init__` method
4. Add navigation method

### Settings Screen Integration
1. Import in `octoprint_ControlCenter/ui/settings_screen/settings_screen.py`
2. Add UI button to `settings_screen.ui`
3. Initialize in `_initialize_sub_screens()`
4. Add navigation method
5. Connect button signal

### Filament Management Integration
1. Import in `octoprint_ControlCenter/ui/filament_management_screen/filamentManagementScreen.py`
2. Add to `_initialize_sub_screens()` method
3. Setup wizard with appropriate parameters

## Printer Configuration
- Support both single and dual nozzle configurations
- Use `is_dual_nozzle_printer()` for conditional logic
- Use `force_single_tool()` for tool parameter validation
- Access configuration via `self.main_window.printer_model`
- Read positions from `calibrationPosition` dictionary

## OctoPrint Communication
```python
# G-code commands
self.octoprint_client.gcode("G28")  # Home all axes
self.octoprint_client.gcode("M104 S200")  # Set temperature

# Movement commands
self.octoprint_client.jog(x=10, y=10, z=1, absolute=True, speed=1500)
self.octoprint_client.home(['x', 'y', 'z'])

# Extrusion
self.octoprint_client.extrude(amount=5, speed=300)
```

## Signal/Slot Patterns
```python
# Connect to model updates
self.main_window.printer_model.temperature_updated.connect(self.on_temperature_updated)
self.main_window.printer_model.status_updated.connect(self.on_status_updated)
self.main_window.printer_model.current_position_updated.connect(self.on_position_updated)

# Button connections
self.backButton.clicked.connect(self.go_back)
self.startButton.clicked.connect(self.start_operation)
```

## Async Operations
```python
from utils.helpers import run_async

@run_async
def continuous_operation(self):
    """Example async operation for long-running tasks."""
    self.operation_active = True
    try:
        while self.operation_active:
            # Perform operation
            time.sleep(1)
    except Exception as e:
        self.logger.error(f"Error in continuous operation: {e}")
    finally:
        self.operation_active = False
```

## Testing
- Test on both single and dual nozzle configurations
- Verify UI responsiveness on 800x480 touchscreen
- Test printer communication with actual hardware
- Validate error handling with disconnected printer
- Check navigation flows between screens

## Required Imports
```python
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel
from utils.helpers import check_ui_elements, run_async
from utils.logger import get_logger
from utils.printer_ui_config import is_dual_nozzle_printer, force_single_tool
from utils import dialog
```

## UI File Template
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>[ClassName]</class>
 <widget class="QWidget" name="[ClassName]">
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
  <!-- Add UI components here -->
 </widget>
</ui>
```
