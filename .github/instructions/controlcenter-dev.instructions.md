---
description: "Use when developing ControlCenter features: PyQt5 screens, wizard dialogs, calibration flows, filament management, settings widgets, OctoPrint API integration, or printer model/signal work. Covers MVP pattern, 800x480 UI constraints, async operations, and dual/single nozzle branching."
applyTo: "octoprint_ControlCenter/**/*.py"
---

# ControlCenter Development Standards

> Full wizard/UI pattern reference: `.github/instructions.md`
> Feature docs: `Documentation/*.md`

## Architecture Rules
- **MVP pattern**: UI widgets are Views, `printer_model.py` is the Model, `main_controller.py` is the Controller
- **No logic in UI files** — UI only calls model/controller methods and reacts to signals
- **One `.ui` file per widget class** — loaded via `uic.loadUi()` at `__init__` time

## Required Coding Patterns

### Logger (every class)
```python
from utils.logger import get_logger
self.logger = get_logger(self.__class__.__name__)
```

### OctoPrint Calls (always try-except)
```python
try:
    self.octoprint_client.gcode(command='G28')
except Exception as e:
    self.logger.error(f"OctoPrint command failed: {e}")
    dialog.WarningOk(self, "Printer communication error.", overlay=True)
```

### Signal Disconnect (always guarded)
```python
try:
    self.model.some_signal.disconnect(self.handler)
except TypeError:
    pass
```

### Dual-Nozzle Branching
```python
from utils.printer_ui_config import is_dual_nozzle_printer, force_single_tool
if is_dual_nozzle_printer(self.main_window):
    # dual-nozzle path
else:
    # single-nozzle path
```

### Async Long Operations
```python
from utils.helpers import run_async

@run_async
def long_operation(self):
    # runs in thread — never touch Qt widgets directly here
    # emit signals to update UI from main thread
```

## UI Standards
- Fixed 800x480: `setMinimumSize(800, 480)` + `setMaximumSize(800, 480)`
- Dark theme: `background-color: rgb(40, 40, 40);` in `.ui` stylesheet
- Touch targets: minimum 44px height for all interactive elements
- Dialogs: `dialog.WarningOk()` for info/errors, `dialog.WarningYesNo()` for confirmations

## Loading UI Files
```python
import os
from PyQt5 import uic

uic.loadUi(os.path.join(os.path.dirname(__file__), "my_screen.ui"), self)
```

## Widget Initialization Pattern
```python
def _init_ui_components(self):
    from utils.helpers import check_ui_elements
    self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
    self.nextButton = self.findChild(QPushButton, "nextButton")
    self.cancelButton = self.findChild(QPushButton, "cancelButton1")
    check_ui_elements(self, [self.stackedWidget, self.nextButton, self.cancelButton], "MyWidget")
```

## Model Signals Reference
```python
self.model.temperature_updated        # (tool0_temp, tool1_temp, bed_temp)
self.model.status_updated             # (status_str)
self.model.current_position_updated   # (x, y, z)
self.model.printer_config_updated     # () — config reloaded from Klipper
self.model.filament_runout_signal     # (tool_index)
self.model.filament_jam_signal        # (tool_index)
```

## OctoPrint Client API
```python
self.octoprint_client.gcode(command='...')              # Send raw G-code
self.octoprint_client.jog(x=10, y=0, absolute=True)    # Move axis
self.octoprint_client.home(['x', 'y', 'z'])             # Home axes
self.octoprint_client.extrude(amount=5, speed=300)      # Extrude filament
self.octoprint_client.set_temperature('tool0', 200)     # Set hotend temp
self.octoprint_client.set_temperature('bed', 60)        # Set bed temp
```

## Printer Config Access
```python
from config import get_printer_config
config = get_printer_config()
cal_pos = config['calibrationPosition']   # {'X1':..., 'Y1':..., 'X2':..., ...}
build_size = config['machineBuildSize']   # {'X':..., 'Y':..., 'Z':...}
is_dual = config['IS_DUAL_NOZZLE']        # bool
```

## Screen Navigation
```python
# Navigate to a screen via main_window
self.main_window.show_screen('calibrate')  # or whatever the method name is
# For calibrate sub-screens:
self.main_window.calibrate_screen.show_calibrate_screen()
```

## Required Imports (standard set for any new widget)
```python
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel
from utils.helpers import check_ui_elements, run_async
from utils.logger import get_logger
from utils.printer_ui_config import is_dual_nozzle_printer, force_single_tool
from utils import dialog
```

## Testing Checklist for Any New Feature
- [ ] Works with single-nozzle printer config
- [ ] Works with dual-nozzle printer config
- [ ] Handles OctoPrint disconnection gracefully
- [ ] No Qt widget access from background threads
- [ ] All signal connections are properly disconnected on close/hide
- [ ] Logging covers key state transitions
- [ ] Error dialogs shown for all failure paths
