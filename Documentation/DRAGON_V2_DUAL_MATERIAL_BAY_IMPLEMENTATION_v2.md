# Dragon 400 V2 - Dual Material Bay Implementation Plan

## Overview

This document outlines the implementation plan for adding dual material bay support to the Dragon 400 V2 printer. This configuration uses two redundant extruder motors (material bays A and B) connected via a Y-splitter to a single nozzle, allowing automatic filament switching between two material sources.

### Key Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Material Bay A │     │  Material Bay B │
│  (extruder_side0)│     │  (extruder_side1)│
│  [35cm PTFE]    │     │  [35cm PTFE]    │
│  [Runout+Jam]   │     │  [Runout+Jam]   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │    ┌─────────────┐   │
         └────┤ Y-Splitter  ├───┘
              └──────┬──────┘
                     │
              [96cm PTFE]
                     │
              ┌──────┴──────┐
              │   Toolhead  │
              │  (extruder) │
              │   Nozzle    │
              └─────────────┘
```

### PTFE Lengths (Dragon 400 V2)
- **Upstream (to Y-splitter)**: 96cm (960mm)
- **Material Bay Branch**: 35cm (350mm) each
- **Total retraction distance**: 131cm (1310mm)

### Important Architecture Note

**The actual filament load/unload process is controlled by Python code in the Control Center UI**, not by Klipper GCode macros. The Klipper firmware provides:
- Low-level motor control and synchronization (`SYNC_EXTRUDER_MOTION`)
- Sensor management (`SET_FILAMENT_SENSOR`)
- State tracking via `PRINTER_VARIABLES`

The Python code (`changeFilamentWizard.py`) orchestrates:
- Heating sequence
- Step-by-step extrusion/retraction with user interaction
- Status updates and persistence
- Load/unload validation based on bay status

---

## Phase 1: Qt UI File Changes (.ui files)

This phase focuses on the visual layout changes in Qt Designer. These can be done independently without code changes.

### 1.1 Update filamentManagementScreen.ui

#### Task 1.1.1: Add Material Bay B UI Elements

**File**: `ui/filament_management_screen/filamentManagementScreen.ui`

Add new UI elements for Material Bay B (mirroring Bay A layout):

**Required UI Elements to Add:**
| Element Name | Type | Description |
|--------------|------|-------------|
| `changeTool0MaterialBayB` | QToolButton | Change filament button for Bay B |
| `tool0MaterialBayBFrame` | QFrame | Container frame for Bay B UI |
| `editTool0MaterialBayB` | QPushButton | Edit Bay B settings button |
| `tool0MaterialBayBStateColor` | QLabel | Status color indicator for Bay B |
| `tool0MaterialBayBStateLabel` | QLabel | Status text label for Bay B |
| `tool0MaterialBayBLabel` | QLabel | "Bay B" label |
| `materialBayActiveIndicatorA` | QLabel | Active indicator dot for Bay A |
| `materialBayActiveIndicatorB` | QLabel | Active indicator dot for Bay B |
| `ySplitterDiagram` | QLabel/QFrame | Visual Y-splitter diagram (optional) |
| `dualBayFilamentPathImage` | QLabel | Image showing dual bay filament path |

**Layout Concept for Dual Material Bay (Dragon V2):**
```
┌──────────────────────────────────────────────────┐
│                    Tool 0                        │
│  ┌─────────────┐         ┌─────────────┐        │
│  │ Bay A [●]   │─────┬───│ Bay B [ ]   │        │
│  │ PLA White   │     │   │ PLA Black   │        │
│  │ [Change]    │     │   │ [Change]    │        │
│  └─────────────┘     │   └─────────────┘        │
│                      │                          │
│                   [Y-Splitter]                  │
│                      │                          │
│                   ┌──┴──┐                       │
│                   │Nozzle│                      │
│                   │ 0.4  │                      │
│                   └─────┘                       │
└──────────────────────────────────────────────────┘
```

**Layout for Standard Single Material Bay (Dragon/TwinDragon - unchanged):**
```
┌──────────────────────────────────────────────────┐
│       Tool 0              │       Tool 1         │
│  ┌─────────────┐         │  ┌─────────────┐     │
│  │ Bay A       │         │  │ Bay X       │     │
│  │ PLA White   │         │  │ PLA Black   │     │
│  │ [Change]    │         │  │ [Change]    │     │
│  └─────────────┘         │  └─────────────┘     │
│       Nozzle 0.4         │       Nozzle 0.4     │
└──────────────────────────────────────────────────┘
```

**Design Notes:**
- Bay B elements should be placed to mirror Bay A on the right side
- Both bays connect to a shared nozzle representation
- Active indicator should be a small colored circle (green = active, gray = inactive)
- All new Bay B elements will be hidden by Python code for non-dual-bay printers

### 1.2 Create Filament Path Images

#### Task 1.2.1: Create New Filament Path Images

**Location**: `ui/resources/img/Filament Paths/`

| Image File | Description |
|------------|-------------|
| `dualBayLeftLoaded.png` | Bay A loaded (active), Bay B empty - shows Y-splitter with left path highlighted |
| `dualBayRightLoaded.png` | Bay A empty, Bay B loaded (active) - shows Y-splitter with right path highlighted |
| `dualBayNoneLoaded.png` | Both bays empty - shows Y-splitter with no paths highlighted |

**Image Requirements:**
- Should visually show the Y-splitter architecture
- Clear indication of which bay is active/loaded
- Consistent style with existing filament path images
- Recommended size: Match existing images (check `singleLoaded.png`, `leftLoaded.png` for reference)

### 1.3 Phase 1 Summary Checklist

| Task | Description | Priority | Status |
|------|-------------|----------|--------|
| 1.1.1 | Add Bay B UI elements to filamentManagementScreen.ui | High | ⬜ |
| 1.2.1 | Create dualBayLeftLoaded.png | Medium | ⬜ |
| 1.2.2 | Create dualBayRightLoaded.png | Medium | ⬜ |
| 1.2.3 | Create dualBayNoneLoaded.png | Medium | ⬜ |

---

## Phase 2: Klipper Firmware Changes

This phase creates the firmware configuration files for the Dragon 400 V2 printer.

### 2.1 Verify BASE_DRAGON.cfg has extruder_side0

**Status**: ✅ Already exists in BASE_DRAGON.cfg

The `extruder_side0` stepper is already defined in BASE_DRAGON.cfg:
```properties
[extruder_stepper extruder_side0]
extruder: extruder
step_pin:  PG9
dir_pin: PD7
enable_pin: !PG11
microsteps: 16
rotation_distance: 7.710
```

### 2.2 Create PRINTER_DRAGON_400_V2.cfg

#### Task 2.2.1: Create New Printer Configuration File

**File**: `octoprint_ControlCenter/firmware/PRINTER_DRAGON_400_V2.cfg`

```properties
########################################
# PRINTERS_DRAGON_400_V2.cfg
# Printer specific configurations for Dragon 400 V2
# with Dual Material Bay (Y-splitter) configuration
# Author: [Your Name]
# Version: 1
########################################

########################################
# Core Configs, Common to all printers
[include CORE_GCODE_MACROS.cfg]
########################################

########################################
# Base Configuration - Inherits extruder_side0 from BASE_DRAGON
[include BASE_DRAGON.cfg]
########################################

########################################
# Dual Material Bay Control Macros
[include DUAL_MATERIAL_BAY_MACROS.cfg]
########################################

########################################
# Filament Sensors - Material Bay A (T0)
#----------------------------------------
[include T0_FILAMENT_RUNOUT_SENSOR.cfg]
[include T0_FILAMENT_JAM_SENSOR.cfg]
########################################

########################################
# Filament Sensors - Material Bay B (New)
#----------------------------------------
[include MATERIAL_BAY_B_FILAMENT_RUNOUT_SENSOR.cfg]
# Note: Bay B jam sensor defined inline below
########################################

########################################
# Other Add Ons:
#----------------------------------------
[include MAG_DOOR.cfg]
[include ELECTRONICS_CHAMBER_COOLING.cfg]
########################################

########################################
# Toolhead Configuration (Single Nozzle)
[include TOOLHEADS_TD-01_TOOLHEAD0.cfg]
########################################

########################################
# Redundant Extruder - Material Bay B (extruder_side1)
# Note: Material Bay A (extruder_side0) inherited from BASE_DRAGON.cfg
########################################

[extruder_stepper extruder_side1]
extruder:                           # Not synced by default - controlled via SYNC_MATERIAL_BAY
step_pin: PD4
dir_pin: PD3
enable_pin: !PD6 
microsteps: 16
rotation_distance: 7.710

[tmc5160 extruder_stepper extruder_side1]
cs_pin: PD5
spi_software_mosi_pin: PG6
spi_software_miso_pin: PG7
spi_software_sclk_pin: PG8
hold_current: 0.40
run_current: 1.00
interpolate: False
sense_resistor: 0.075

########################################
# PRINTER_VARIABLES - Dragon 400 V2 Specific
########################################

[gcode_macro PRINTER_VARIABLES]
# Offset coordinates (single carriage, no dual_carriage offsets needed)
variable_offset_x: 0
variable_offset_y: 0
variable_offset_z: 0
# Autopark parameters
variable_autopark: 1
variable_z_hop: 0.6
variable_movespeed: 300
variable_feedrate: 8000
# HeatBed size (same as Dragon 400)
variable_bed_x_min: 0
variable_bed_x_max: 430
variable_bed_y_min: 0
variable_bed_y_max: 400
variable_bed_z_min: 0
variable_bed_z_max: 418
# Print cooling fans names
variable_fan0: 'extruder_CF'
# Pause Positions
variable_tool0_pause_position_x: -20
variable_tool0_pause_position_y: -20
# Printer Configuration - CRITICAL NEW VARIABLES
variable_is_dual_nozzle: 0              # Single nozzle configuration
variable_has_dual_material_bay: 1       # NEW: Indicates dual material bay setup
variable_active_material_bay: 'A'       # NEW: Currently active bay (A or B)
# PTFE Tube Lengths (Dragon 400 V2 specific)
variable_ptfe_tube_length: 960          # Upstream PTFE (Y-splitter to nozzle) in mm
variable_ptfe_bay_branch_length: 350    # NEW: Branch PTFE (bay to Y-splitter) in mm
variable_ptfe_total_retract: 1310       # NEW: Total retraction distance (960 + 350)
# Bed Calibration Positions
variable_bed_calibration_x1: 25
variable_bed_calibration_y1: 75
variable_bed_calibration_x2: 375
variable_bed_calibration_y2: 75
variable_bed_calibration_x3: 200
variable_bed_calibration_y3: 280
variable_bed_calibration_x4: 224
variable_bed_calibration_y4: 236
gcode:
    G90

########################################
# Printer Kinematics (same as Dragon 400)
########################################

[printer]
kinematics: fracktal_hybrid_corexy
max_velocity: 600
max_accel: 6500
minimum_cruise_ratio: 0
square_corner_velocity: 100
max_z_velocity: 20
max_z_accel: 100

########################################
# X Axis (inherited positions from DRAGON_400)
########################################

[stepper_x]
position_endstop: -21
position_min: -21
position_max: 430

########################################
# Y Axis
########################################

[stepper_y]
position_endstop: 420
position_max: 420
position_min: -45

########################################
# Z Axis
########################################

[stepper_z]
position_endstop: 417
position_max: 417
position_min: -6

########################################
# Bed Mesh
########################################

[bed_mesh]
mesh_min: 25, 50
mesh_max: 400, 380
probe_count: 5,5
speed: 200

########################################
# Material Bay B Jam Sensor (Inline)
# Defined here instead of separate include file
########################################

[filament_motion_sensor motion_sensor_bay_b]
switch_pin: ^PA0                    # Use appropriate pin for Bay B jam sensor
detection_length: 15.0
extruder: extruder
pause_on_runout: False
runout_gcode:
    {% set printer_vars = printer["gcode_macro PRINTER_VARIABLES"] %}
    {% if printer.toolhead.homed_axes == "xyz" and printer_vars.active_material_bay|default('A') == 'B' %}
        RESPOND TYPE=echo MSG="Filament Jam detected on Material Bay B"
        PAUSE
    {% endif %}
insert_gcode:
    RESPOND TYPE=echo MSG="Filament motion restored on Material Bay B"

[delayed_gcode SET_BAY_B_JAM_SENSOR_STARTUP]
initial_duration: 1
gcode:
    SET_FILAMENT_SENSOR SENSOR=motion_sensor_bay_b ENABLE=0
```

### 2.3 Create Dual Material Bay Control Macros (Separate Include File)

#### Task 2.3.1: Create DUAL_MATERIAL_BAY_MACROS.cfg

**File**: `octoprint_ControlCenter/firmware/DUAL_MATERIAL_BAY_MACROS.cfg`

This file contains **only the low-level Klipper macros** for motor synchronization and sensor control. The actual load/unload workflow is handled by the Python UI code.

```properties
########################################
# DUAL_MATERIAL_BAY_MACROS.cfg
# Low-level macros for dual material bay motor sync and sensor control
# NOTE: Actual load/unload workflow is controlled by Python UI code
# Author: [Your Name]
# Version: 1
########################################

########################################
# Core Bay Synchronization
########################################

[gcode_macro SYNC_MATERIAL_BAY]
description: Sync a specific material bay extruder motor to the toolhead
gcode:
    {% set bay = params.BAY|default('A')|upper %}
    {% set printer_vars = printer["gcode_macro PRINTER_VARIABLES"] %}
    
    {% if printer_vars.has_dual_material_bay|default(0) != 1 %}
        RESPOND TYPE=error MSG="Dual material bay not configured for this printer"
    {% else %}
        {% if bay == 'A' %}
            # Unsync bay B, sync bay A
            SYNC_EXTRUDER_MOTION EXTRUDER=extruder_side1 MOTION_QUEUE=
            SYNC_EXTRUDER_MOTION EXTRUDER=extruder_side0 MOTION_QUEUE=extruder
            SET_GCODE_VARIABLE MACRO=PRINTER_VARIABLES VARIABLE=active_material_bay VALUE="'A'"
            # Enable Bay A sensors, disable Bay B sensors
            _SET_BAY_SENSORS BAY=A
            RESPOND TYPE=echo MSG="Material Bay A activated and synced to toolhead"
        {% elif bay == 'B' %}
            # Unsync bay A, sync bay B
            SYNC_EXTRUDER_MOTION EXTRUDER=extruder_side0 MOTION_QUEUE=
            SYNC_EXTRUDER_MOTION EXTRUDER=extruder_side1 MOTION_QUEUE=extruder
            SET_GCODE_VARIABLE MACRO=PRINTER_VARIABLES VARIABLE=active_material_bay VALUE="'B'"
            # Enable Bay B sensors, disable Bay A sensors
            _SET_BAY_SENSORS BAY=B
            RESPOND TYPE=echo MSG="Material Bay B activated and synced to toolhead"
        {% else %}
            RESPOND TYPE=error MSG="Invalid material bay '{bay}'. Use 'A' or 'B'"
        {% endif %}
    {% endif %}

[gcode_macro _SET_BAY_SENSORS]
description: Internal macro to enable/disable sensors based on active bay
gcode:
    {% set bay = params.BAY|default('A')|upper %}
    {% if bay == 'A' %}
        # Enable Bay A (T0) sensors
        SET_FILAMENT_SENSOR SENSOR=switch_sensor_T0 ENABLE=1
        SET_FILAMENT_SENSOR SENSOR=motion_sensor_T0 ENABLE=1
        # Disable Bay B sensors
        SET_FILAMENT_SENSOR SENSOR=switch_sensor_bay_b ENABLE=0
        SET_FILAMENT_SENSOR SENSOR=motion_sensor_bay_b ENABLE=0
    {% elif bay == 'B' %}
        # Disable Bay A (T0) sensors
        SET_FILAMENT_SENSOR SENSOR=switch_sensor_T0 ENABLE=0
        SET_FILAMENT_SENSOR SENSOR=motion_sensor_T0 ENABLE=0
        # Enable Bay B sensors
        SET_FILAMENT_SENSOR SENSOR=switch_sensor_bay_b ENABLE=1
        SET_FILAMENT_SENSOR SENSOR=motion_sensor_bay_b ENABLE=1
    {% endif %}

[gcode_macro GET_ACTIVE_MATERIAL_BAY]
description: Report which material bay is currently active
gcode:
    {% set printer_vars = printer["gcode_macro PRINTER_VARIABLES"] %}
    {% if printer_vars.has_dual_material_bay|default(0) == 1 %}
        RESPOND TYPE=echo MSG="Active Material Bay: {printer_vars.active_material_bay|default('A')}"
    {% else %}
        RESPOND TYPE=echo MSG="Single material bay configuration"
    {% endif %}

[gcode_macro UNSYNC_ALL_MATERIAL_BAYS]
description: Unsync all material bay extruders (for manual/debug control)
gcode:
    SYNC_EXTRUDER_MOTION EXTRUDER=extruder_side0 MOTION_QUEUE=
    SYNC_EXTRUDER_MOTION EXTRUDER=extruder_side1 MOTION_QUEUE=
    RESPOND TYPE=echo MSG="All material bays unsynced"

########################################
# Persistence
########################################

[gcode_macro SAVE_ACTIVE_BAY]
description: Save current active bay to persistent storage
gcode:
    {% set printer_vars = printer["gcode_macro PRINTER_VARIABLES"] %}
    SAVE_VARIABLE VARIABLE=active_material_bay VALUE="'{printer_vars.active_material_bay|default('A')}'"
    RESPOND TYPE=echo MSG="Active bay saved: {printer_vars.active_material_bay|default('A')}"

########################################
# Startup Configuration
########################################

[delayed_gcode DUAL_BAY_STARTUP]
initial_duration: 2
gcode:
    {% set printer_vars = printer["gcode_macro PRINTER_VARIABLES"] %}
    {% if printer_vars.has_dual_material_bay|default(0) == 1 %}
        # Restore last active material bay from saved variables
        {% set saved_bay = printer.save_variables.variables.active_material_bay|default('A') %}
        SYNC_MATERIAL_BAY BAY={saved_bay}
        RESPOND TYPE=echo MSG="Dual material bay initialized: Bay {saved_bay} active"
    {% endif %}
```

### 2.4 Create Filament Sensor Configuration for Material Bay B

#### Task 2.4.1: Create MATERIAL_BAY_B_FILAMENT_RUNOUT_SENSOR.cfg

**File**: `octoprint_ControlCenter/firmware/MATERIAL_BAY_B_FILAMENT_RUNOUT_SENSOR.cfg`

```properties
########################################
# MATERIAL_BAY_B_FILAMENT_RUNOUT_SENSOR.cfg
# Filament Runout Sensor for Material Bay B (Dragon V2)
# Author: [Your Name]
# Version: 1
########################################

[filament_switch_sensor switch_sensor_bay_b]
switch_pin: ^PF0                    # Use appropriate pin for Bay B sensor
pause_on_runout: False
runout_gcode:
    {% set printer_vars = printer["gcode_macro PRINTER_VARIABLES"] %}
    {% if printer.toolhead.homed_axes == "xyz" and printer_vars.active_material_bay|default('A') == 'B' %}
        RESPOND TYPE=echo MSG="Filament Runout detected on Material Bay B"
    {% endif %}
insert_gcode:
    RESPOND TYPE=echo MSG="Filament inserted in Material Bay B"

[delayed_gcode SET_BAY_B_RUNOUT_SENSOR_STARTUP]
initial_duration: 1
gcode:
    SET_FILAMENT_SENSOR SENSOR=switch_sensor_bay_b ENABLE=0
```

### 2.5 Phase 2 Summary Checklist

| Task | Description | Priority | Status |
|------|-------------|----------|--------|
| 2.2.1 | Create PRINTER_DRAGON_400_V2.cfg (includes Bay B jam sensor inline) | High | ⬜ |
| 2.3.1 | Create DUAL_MATERIAL_BAY_MACROS.cfg (separate include file) | High | ⬜ |
| 2.4.1 | Create MATERIAL_BAY_B_FILAMENT_RUNOUT_SENSOR.cfg | High | ⬜ |

---

## Phase 3: Python Code Changes

This phase implements the logic to support dual material bay in the Control Center application.

### 3.1 Configuration Detection and Variables

#### Task 3.1.1: Update printer_config_manager.py

Add parsing for new PRINTER_VARIABLES:

```python
# In parse_printer_variables_from_file() method, add:
'hasDualMaterialBay': variables.get('has_dual_material_bay', 0),
'activeMaterialBay': variables.get('active_material_bay', 'A'),
'ptfeBayBranchLength': variables.get('ptfe_bay_branch_length', 350),
'ptfeTotalRetract': variables.get('ptfe_total_retract', 1310),
```

#### Task 3.1.2: Update config.py

Add new global configuration variables:

```python
# Add to config.py
HAS_DUAL_MATERIAL_BAY = False
ACTIVE_MATERIAL_BAY = 'A'
PTFE_BAY_BRANCH_LENGTH = 350
PTFE_TOTAL_RETRACT = 1310
```

### 3.2 Printer Model Updates

#### Task 3.2.1: Update printer_model.py

Add signals and state management for dual material bay:

```python
# New signals
active_material_bay_changed = pyqtSignal(str)  # 'A' or 'B'

# New properties
self.has_dual_material_bay = False
self.active_material_bay = 'A'
self.ptfe_bay_branch_length = 350
self.ptfe_total_retract = 1310

# Update get_default_bay to support dual material bay
def get_default_bay(self, tool: str, bay_override: str = None) -> str:
    """Get default bay for a tool.
    
    For dual material bay printers (Dragon V2), tool0 can have material_bay_a or material_bay_b.
    For standard printers, tool0 uses material_bay_a, tool1 uses material_bay_x.
    """
    if bay_override:
        return f"material_bay_{bay_override.lower()}"
    if tool == "tool0":
        return "material_bay_a"  # Default primary bay
    return "material_bay_x"

def get_all_bays_for_tool(self, tool: str) -> list:
    """Get all available bays for a tool based on printer config."""
    if tool == "tool0" and self.has_dual_material_bay:
        return ["material_bay_a", "material_bay_b"]
    elif tool == "tool0":
        return ["material_bay_a"]
    elif tool == "tool1":
        return ["material_bay_x"]
    return []
```

### 3.3 Printer Preference Store Updates

#### Task 3.3.1: Update DEFAULT_STATE in printer_preference_store.py

```python
DEFAULT_STATE = {
    "version": 2,  # Increment version for schema change
    "tools": {
        "tool0": {
            "material_bay_a": {"filament": None, "status": "Unknown", "nozzle": "Unknown"},
            "material_bay_b": {"filament": None, "status": "Unknown", "nozzle": "Unknown"}  # NEW
        },
        "tool1": {
            "material_bay_x": {"filament": None, "status": "Unknown", "nozzle": "Unknown"}
        },
    },
    "active_material_bay": "A",  # NEW: Persist last active bay for dual material bay printers
    "preferences": { ... }
}
```

#### Task 3.3.2: Add methods for active bay persistence

```python
def get_active_material_bay(self) -> str:
    """Get the currently active material bay (A or B) for dual bay printers."""
    return self.load_full().get("active_material_bay", "A")

def set_active_material_bay(self, bay: str) -> None:
    """Set the active material bay (A or B)."""
    with self._lock:
        data = self.load_full()
        if data.get("active_material_bay") != bay:
            data["active_material_bay"] = bay
            self._dirty = True
            if self._batch_depth == 0:
                self.save()
```

### 3.4 UI Configuration Updates

#### Task 3.4.1: Update printer_ui_config.py

Add new element visibility rules for dual material bay:

```python
# Add new configuration check
def is_dual_material_bay_printer():
    """Check if the printer has dual material bay configuration."""
    return config.HAS_DUAL_MATERIAL_BAY

# Elements to show ONLY for dual material bay printers (hidden for single bay)
DUAL_MATERIAL_BAY_ONLY_ELEMENTS = {
    'filament_management_screen': [
        'changeTool0MaterialBayB', 'tool0MaterialBayBFrame', 'editTool0MaterialBayB',
        'tool0MaterialBayBStateColor', 'tool0MaterialBayBStateLabel',
        'tool0MaterialBayBLabel', 'materialBayActiveIndicatorA', 'materialBayActiveIndicatorB',
        'ySplitterDiagram', 'dualBayFilamentPathImage'
    ]
}

def hide_dual_material_bay_elements(widget, element_names):
    """Hide dual material bay elements for single bay printers."""
    if not is_dual_material_bay_printer():
        for element_name in element_names:
            element = getattr(widget, element_name, None)
            if element:
                try:
                    element.hide()
                except Exception as e:
                    logger.error(f"Error hiding element {element_name}: {e}")

def apply_material_bay_config_to_screen(widget, screen_name):
    """Apply material bay configuration to a specific screen widget."""
    hide_dual_material_bay_elements(widget, DUAL_MATERIAL_BAY_ONLY_ELEMENTS.get(screen_name, []))
```

### 3.5 Filament Management Screen Python Updates

#### Task 3.5.1: Update filamentManagementScreen.py

```python
# Add new UI element bindings
self.changeTool0MaterialBayB = self.findChild(QToolButton, "changeTool0MaterialBayB")
self.tool0MaterialBayBLabel = self.findChild(QLabel, "tool0MaterialBayBLabel")
self.tool0MaterialBayBStateLabel = self.findChild(QLabel, "tool0MaterialBayBStateLabel")
self.tool0MaterialBayBStateColor = self.findChild(QLabel, "tool0MaterialBayBStateColor")
self.editTool0MaterialBayB = self.findChild(QPushButton, "editTool0MaterialBayB")
self.materialBayActiveIndicatorA = self.findChild(QLabel, "materialBayActiveIndicatorA")
self.materialBayActiveIndicatorB = self.findChild(QLabel, "materialBayActiveIndicatorB")

# Connect Bay B button with bay parameter
if self.changeTool0MaterialBayB:
    self.changeTool0MaterialBayB.clicked.connect(
        lambda: self.show_material_nozzle_screen(
            target_screen="filament_change", 
            params={"tool": "tool0", "bay": "B"}
        )
    )

# Update Bay A button to include bay parameter
self.changeTool0MaterialBayA.clicked.connect(
    lambda: self.show_material_nozzle_screen(
        target_screen="filament_change", 
        params={"tool": "tool0", "bay": "A"}
    )
)

# Add method to update active bay indicator
def update_active_bay_indicator(self, active_bay: str):
    """Update visual indicators showing which bay is active."""
    if not config.HAS_DUAL_MATERIAL_BAY:
        return
    if active_bay == 'A':
        self.materialBayActiveIndicatorA.setStyleSheet("background-color: #4CAF50;")  # Green
        self.materialBayActiveIndicatorB.setStyleSheet("background-color: #757575;")  # Gray
    else:
        self.materialBayActiveIndicatorA.setStyleSheet("background-color: #757575;")
        self.materialBayActiveIndicatorB.setStyleSheet("background-color: #4CAF50;")

# Add method to update filament path image based on bay states
def update_dual_bay_filament_path_image(self):
    """Update filament path image based on which bay has filament loaded.
    
    Images:
    - dualBayLeftLoaded.png: Bay A loaded
    - dualBayRightLoaded.png: Bay B loaded  
    - dualBayNoneLoaded.png: Both bays empty
    """
    if not config.HAS_DUAL_MATERIAL_BAY:
        return
    
    bay_a_state = self.model.get_bay_state("tool0", "material_bay_a")
    bay_b_state = self.model.get_bay_state("tool0", "material_bay_b")
    
    bay_a_loaded = bay_a_state.get("status") == "Loaded"
    bay_b_loaded = bay_b_state.get("status") == "Loaded"
    
    if bay_a_loaded:
        image_path = ":/img/Filament Paths/dualBayLeftLoaded.png"
    elif bay_b_loaded:
        image_path = ":/img/Filament Paths/dualBayRightLoaded.png"
    else:
        image_path = ":/img/Filament Paths/dualBayNoneLoaded.png"
    
    if hasattr(self, 'dualBayFilamentPathImage') and self.dualBayFilamentPathImage:
        self.dualBayFilamentPathImage.setPixmap(QPixmap(image_path))

# Update _apply_tool_ui to handle both bays
def _apply_tool_ui(self, tool: str, bay: str, data: dict):
    """Apply UI state for a specific tool and bay."""
    filament = data.get("filament") or "Unknown"
    status = data.get("status", "Unknown")
    display_filament = "-" if status == "Empty" else str(filament)
    nozzle = data.get("nozzle", "Unknown")
    
    if tool == "tool0" and bay == "material_bay_a":
        if self.changeTool0MaterialBayA:
            self.changeTool0MaterialBayA.setText(display_filament)
        if self.tool0MaterialBayAStateLabel:
            self.tool0MaterialBayAStateLabel.setText(str(status))
        if self.tool0MaterialBayAStateColor:
            self.tool0MaterialBayAStateColor.setStyleSheet(self._status_to_style(status))
    elif tool == "tool0" and bay == "material_bay_b":
        if self.changeTool0MaterialBayB:
            self.changeTool0MaterialBayB.setText(display_filament)
        if self.tool0MaterialBayBStateLabel:
            self.tool0MaterialBayBStateLabel.setText(str(status))
        if self.tool0MaterialBayBStateColor:
            self.tool0MaterialBayBStateColor.setStyleSheet(self._status_to_style(status))
    # ... existing tool1 handling

# Apply dual material bay configuration on init
def apply_material_bay_configuration(self):
    """Hide dual material bay elements for single bay configuration."""
    apply_material_bay_config_to_screen(self, 'filament_management_screen')

# Call this when screen is shown/refreshed to update filament path image
def refresh_dual_bay_ui(self):
    """Refresh all dual material bay UI elements based on current state."""
    if config.HAS_DUAL_MATERIAL_BAY:
        active_bay = self.preference_store.get_active_material_bay()
        self.update_active_bay_indicator(active_bay)
        self.update_dual_bay_filament_path_image()
```

### 3.6 Change Filament Wizard Updates (Core Logic)

#### Task 3.6.1: Update changeFilamentWizard.py - Setup and Bay Handling

```python
class ChangeFilamentWizard(QWidget):
    def __init__(self, main_window):
        # ... existing init ...
        self.activeBay = 'A'  # NEW: Track which bay we're operating on
        self.hasDualMaterialBay = False  # Set from config during setup

    def setup(self, params=None):
        """Prepare and open the wizard for a specific tool and bay."""
        try:
            if isinstance(params, str):
                params = {'tool': params}
            elif params is None:
                params = {}
            elif not isinstance(params, dict):
                params = {}

            # Get tool
            tool = params.get('tool', 'tool0')
            tool = force_single_tool(tool)
            nozzle_index = int(tool.replace('tool', ''))
            self.setActiveExtruder(nozzle_index)
            
            # NEW: Get bay parameter for dual material bay printers
            self.hasDualMaterialBay = config.HAS_DUAL_MATERIAL_BAY
            if self.hasDualMaterialBay and tool == 'tool0':
                self.activeBay = params.get('bay', 'A').upper()
                # Sync the material bay motor before starting
                self.octoprint_client.gcode(f"SYNC_MATERIAL_BAY BAY={self.activeBay}")
            else:
                self.activeBay = None  # Not applicable for non-dual-bay printers
            
            self.changeFilament()
        except Exception as e:
            logger.error(f"Error in ChangeFilament.setup: {e}", exc_info=True)
```

#### Task 3.6.2: Update Load/Unload Distance Calculation

```python
def _get_extrusion_distance(self) -> int:
    """Get the total extrusion distance based on printer config.
    
    For dual material bay printers, this is the total PTFE length from bay to nozzle.
    """
    if self.hasDualMaterialBay:
        return config.PTFE_TOTAL_RETRACT  # 1310mm (960 + 350)
    return self.model.ptfeTubeLength  # Standard distance

def _get_retraction_distance(self) -> int:
    """Get the total retraction distance based on printer config."""
    return self._get_extrusion_distance()
```

#### Task 3.6.3: Update changeFilamentExtrudePageFunction (Load to Nozzle)

```python
@run_async
def changeFilamentExtrudePageFunction(self, *args, **kwargs):
    """After loading, extrude until filament reaches nozzle and purges reliably."""
    logger.info("ChangeFilament.changeFilamentExtrudePageFunction started")
    try:
        self.logger.debug("Entered extrusion loop to reach nozzle")
        self.stackedWidget.setCurrentWidget(self.changeFilamentExtrudePage)
        self._start_inactivity_timer()
        
        # Use appropriate distance for dual material bay or standard
        extrusion_distance = self._get_extrusion_distance()
        
        for i in range(int(extrusion_distance / 150)):
            self.octoprint_client.gcode("G91")
            self.octoprint_client.gcode("G1 E150 F1500")
            self.octoprint_client.gcode("G90")
            time.sleep(self.calcExtrudeTime(150, 1500))
            if self.stackedWidget.currentWidget() is not self.changeFilamentExtrudePage:
                self.logger.debug("Extrude page left; stopping initial extrusion steps")
                break
        
        # Continue with purge loop (unchanged)
        self.logger.debug("Initial extrusion steps done; entering continuous purge loop")
        while self.stackedWidget.currentWidget() == self.changeFilamentExtrudePage:
            feed = 200 if self.changeFilamentComboBox.currentText() == TPU_MATERIAL_NAME else 400
            self.octoprint_client.gcode("G91")
            self.octoprint_client.gcode(f"G1 E20 F{feed}")
            self.octoprint_client.gcode("G90")
            time.sleep(self.calcExtrudeTime(20, feed))
    except Exception as e:
        logger.error(f"Error in ChangeFilament.changeFilamentExtrudePageFunction: {e}")
    finally:
        self._stop_inactivity_timer()
```

#### Task 3.6.4: Update changeFilamentRetractFunction (Unload)

```python
@run_async
def changeFilamentRetractFunction(self):
    """After heating (Unload): tip-shape and retract filament through the tube."""
    logger.info("ChangeFilament.changeFilamentRetractFunction started")
    try:
        self.logger.debug("Entered retraction loop")
        self.stackedWidget.setCurrentWidget(self.changeFilamentRetractPage)
        self._start_inactivity_timer()
        
        # Tip shaping (same for all)
        feed = 300 if self.changeFilamentComboBox.currentText() == TPU_MATERIAL_NAME else 600
        self.octoprint_client.gcode("G91")
        self.octoprint_client.gcode(f"G1 E10 F{feed}")
        time.sleep(self.calcExtrudeTime(10, feed))
        self.octoprint_client.gcode("G1 E-25 F6000")
        time.sleep(self.calcExtrudeTime(20, 6000))
        time.sleep(8)  # wait for filament to cool inside the nozzle
        self.octoprint_client.gcode("G1 E-150 F5000")
        time.sleep(self.calcExtrudeTime(150, 5000))
        self.octoprint_client.gcode("G90")
        
        # Use appropriate distance for dual material bay or standard
        retraction_distance = self._get_retraction_distance()
        
        for _ in range(int(retraction_distance / 150)):
            self.octoprint_client.gcode("G91")
            self.octoprint_client.gcode("G1 E-150 F2000")
            self.octoprint_client.gcode("G90")
            time.sleep(self.calcExtrudeTime(150, 2000))
            if self.stackedWidget.currentWidget() is not self.changeFilamentRetractPage:
                self.logger.debug("Retract page left; stopping tube retraction steps")
                break
        
        # Continue slow retract loop (unchanged)
        while self.stackedWidget.currentWidget() == self.changeFilamentRetractPage:
            self.octoprint_client.gcode("G91")
            self.octoprint_client.gcode("G1 E-5 F1000")
            self.octoprint_client.gcode("G90")
            time.sleep(self.calcExtrudeTime(5, 1000))
    except Exception as e:
        logger.error(f"Error in ChangeFilament.changeFilamentRetractFunction: {e}")
    finally:
        self._stop_inactivity_timer()
```

#### Task 3.6.5: Update changeFilamentDone - Save Bay-Specific State

```python
def changeFilamentDone(self):
    """Finalize the operation, persist tool state, and return to main screen."""
    logger.info("ChangeFilament.changeFilamentDone started")
    try:
        self._stop_inactivity_timer()
        
        if self.loadFlag is not None:
            try:
                tool_key = f"tool{int(self.activeExtruder)}"
                
                # NEW: Determine correct bay for dual material bay printers
                if self.hasDualMaterialBay and self.activeBay:
                    bay = f"material_bay_{self.activeBay.lower()}"
                else:
                    bay = self.main_window.printer_model.get_default_bay(tool_key)
                
                # Determine selected filament name
                selected = None
                try:
                    selected_text = self.changeFilamentComboBox.currentText()
                    if selected_text and selected_text != "Loaded Filament":
                        selected = selected_text
                except Exception:
                    selected = None

                if bool(self.loadFlag):
                    # Loading: status Loaded
                    self.model.update_tool_bay_state(tool_key, bay=bay, filament=selected, status="Loaded", persist=True)
                    # Save active bay to Klipper for persistence across restarts
                    if self.hasDualMaterialBay:
                        self.octoprint_client.gcode("SAVE_ACTIVE_BAY")
                else:
                    # Unloading: status Empty
                    self.model.update_tool_bay_state(tool_key, bay=bay, filament=None, status="Empty", persist=True)
            except Exception as e:
                logger.warning(f"Failed to persist tool state on filament change done: {e}")

        self._disconnect_temperature_signal()
        self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
        self.main_window.filament_management_screen.show_material_nozzle_screen()
        self.changeFilamentHeatingFlag = False
        self.loadFlag = None
    except Exception as e:
        logger.error(f"Error in ChangeFilament.changeFilamentDone: {e}")
```

### 3.7 Multi-Bay Loading Validation Logic

#### Task 3.7.1: Add validation for dual material bay load/unload operations

The key validation rules for dual material bay printers:
1. **Cannot load into a bay if another bay has filament loaded** (must unload first)
2. **Can unload from any loaded bay**
3. **Must sync correct bay before any operation**

```python
# Add to changeFilamentWizard.py

def _validate_bay_operation(self, is_load: bool) -> tuple[bool, str]:
    """Validate if the current bay operation is allowed.
    
    For dual material bay printers:
    - Load: Cannot load if ANY bay has status "Loaded" (must unload first)
    - Unload: Can only unload if current bay has status "Loaded"
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not self.hasDualMaterialBay:
        return True, ""
    
    tool_key = "tool0"  # Dual material bay is only on tool0
    bay_a_state = self.model.get_bay_state(tool_key, "material_bay_a")
    bay_b_state = self.model.get_bay_state(tool_key, "material_bay_b")
    current_bay = f"material_bay_{self.activeBay.lower()}"
    current_state = self.model.get_bay_state(tool_key, current_bay)
    other_bay = "material_bay_b" if self.activeBay == 'A' else "material_bay_a"
    other_state = self.model.get_bay_state(tool_key, other_bay)
    
    if is_load:
        # Check if current bay already has filament
        if current_state.get("status") == "Loaded":
            return False, f"Bay {self.activeBay} already has filament loaded. Please unload first."
        
        # Check if OTHER bay has filament loaded (shared Y-splitter)
        if other_state.get("status") == "Loaded":
            other_bay_letter = 'B' if self.activeBay == 'A' else 'A'
            return False, f"Bay {other_bay_letter} has filament loaded. Please unload Bay {other_bay_letter} before loading into Bay {self.activeBay}."
        
        return True, ""
    else:
        # Unload: Check if current bay actually has filament
        if current_state.get("status") != "Loaded":
            return False, f"Bay {self.activeBay} has no filament to unload."
        return True, ""
```

#### Task 3.7.2: Update loadFilament with validation

```python
def loadFilament(self):
    """Begin Load flow with validation for dual material bay."""
    logger.info("changeFilament.loadFilament started")
    try:
        # NEW: Validate operation for dual material bay
        is_valid, error_msg = self._validate_bay_operation(is_load=True)
        if not is_valid:
            dialog.WarningOk(self, error_msg, overlay=True)
            return
        
        self._jog_to_purge_position()
        self.logger.debug("Jogging to purge position done")
        if self.changeFilamentComboBox.findText(LOADED_FILAMENT_LABEL) == -1:
            self._set_tool_temperature()
        self.stackedWidget.setCurrentWidget(self.changeFilamentProgressPage)
        self.model.temperatures_updated.connect(self.updateTemperature)
        self.changeFilamentStatus.setText(f"Heating Tool {self.activeExtruder}, Please Wait...")
        
        # NEW: Show bay info for dual material bay
        bay_info = f" (Bay {self.activeBay})" if self.hasDualMaterialBay else ""
        self.changeFilamentNameOperation.setText(f"Loading {self.changeFilamentComboBox.currentText()}{bay_info}")
        
        self.changeFilamentHeatingFlag = True
        self.loadFlag = True
    except Exception as e:
        self.loadFlag = None
        self.changeFilamentHeatingFlag = False
        logger.error(f"Error in changeFilament.loadFilament: {e}")
        dialog.WarningOk(self, f"Error in changeFilament.loadFilament: {e}", overlay=True)
```

#### Task 3.7.3: Update unloadFilament with validation

```python
def unloadFilament(self):
    """Begin Unload flow with validation for dual material bay."""
    logger.info("changeFilament.unloadFilament started")
    try:
        # NEW: Validate operation for dual material bay
        is_valid, error_msg = self._validate_bay_operation(is_load=False)
        if not is_valid:
            dialog.WarningOk(self, error_msg, overlay=True)
            return
        
        self._jog_to_purge_position()
        if self.changeFilamentComboBox.findText(LOADED_FILAMENT_LABEL) == -1:
            self._set_tool_temperature()
        self.stackedWidget.setCurrentWidget(self.changeFilamentProgressPage)
        self.model.temperatures_updated.connect(self.updateTemperature)
        self.changeFilamentStatus.setText(f"Heating Tool {self.activeExtruder}, Please Wait...")
        
        # NEW: Show bay info for dual material bay
        bay_info = f" (Bay {self.activeBay})" if self.hasDualMaterialBay else ""
        self.changeFilamentNameOperation.setText(f"Unloading {self.changeFilamentComboBox.currentText()}{bay_info}")
        
        self.changeFilamentHeatingFlag = True
        self.loadFlag = False
    except Exception as e:
        self.loadFlag = None
        self.changeFilamentHeatingFlag = False
        logger.error(f"Error in changeFilament.unloadFilament: {e}")
        dialog.WarningOk(self, f"Error in changeFilament.unloadFilament: {e}", overlay=True)
```

### 3.8 Phase 3 Summary Checklist

| Task | Description | Priority | Status |
|------|-------------|----------|--------|
| 3.1.1 | Update printer_config_manager.py - parse new variables | High | ⬜ |
| 3.1.2 | Update config.py - add new config variables | High | ⬜ |
| 3.2.1 | Update printer_model.py - add dual bay support | High | ⬜ |
| 3.2.2 | Update printer_model.py - add `has_dual_material_bay` property | High | ⬜ |
| 3.2.3 | Update printer_model.py - add `material_bay_b` to initial tools dict | High | ⬜ |
| 3.3.1 | Update printer_preference_store.py - add bay_b to DEFAULT_STATE | High | ⬜ |
| 3.3.2 | Add active_material_bay persistence methods | Medium | ⬜ |
| 3.4.1 | Update printer_ui_config.py - add dual bay visibility rules | High | ⬜ |
| 3.5.1 | Update filamentManagementScreen.py - wire Bay B buttons & state | High | ⬜ |
| 3.5.2 | Update `_apply_tool_ui` to accept bay parameter | High | ⬜ |
| 3.5.3 | Update `_on_tool_state_changed` to handle both bays | High | ⬜ |
| 3.5.4 | Update `_on_tool_states_loaded` to load both bays | High | ⬜ |
| 3.5.5 | Update `_open_edit_dialog` to accept bay parameter | Medium | ⬜ |
| 3.6.1 | Update changeFilamentWizard.py - setup with bay parameter | High | ⬜ |
| 3.6.2 | Add _get_extrusion_distance method | High | ⬜ |
| 3.6.3 | Update changeFilamentExtrudePageFunction | High | ⬜ |
| 3.6.4 | Update changeFilamentRetractFunction | High | ⬜ |
| 3.6.5 | Update changeFilamentDone - bay-specific persistence | High | ⬜ |
| 3.7.1 | Add _validate_bay_operation method | High | ⬜ |
| 3.7.2 | Update loadFilament with validation | High | ⬜ |
| 3.7.3 | Update unloadFilament with validation | High | ⬜ |

---

## Testing Plan

### Phase 1 Testing (Qt UI Files)

1. **Visual verification:**
   - Load filamentManagementScreen.ui in Qt Designer
   - Verify Bay B elements are positioned correctly
   - Verify element naming follows conventions
   - Verify all widgets have appropriate object names

2. **Image verification:**
   - Verify new filament path images display correctly
   - Verify image sizes match existing images

### Phase 2 Testing (Firmware)

1. **SYNC_MATERIAL_BAY macro tests:**
   - Verify `SYNC_MATERIAL_BAY BAY=A` syncs extruder_side0 to extruder motion queue
   - Verify `SYNC_MATERIAL_BAY BAY=B` syncs extruder_side1 to extruder motion queue
   - Verify sensor enable/disable on bay switch (correct sensors active)
   - Verify error handling for invalid bay parameter
   - Verify `GET_ACTIVE_MATERIAL_BAY` reports correct state

2. **Persistence tests:**
   - Verify active bay survives printer restart via `SAVE_ACTIVE_BAY`
   - Test `DUAL_BAY_STARTUP` restores correct bay on boot

3. **Sensor tests:**
   - Verify Bay A sensors (switch_sensor_T0, motion_sensor_T0) function correctly
   - Verify Bay B sensors (switch_sensor_bay_b, motion_sensor_bay_b) function correctly
   - Verify sensor toggling based on active bay

### Phase 3 Testing (Python)

1. **Configuration detection:**
   - Verify Dragon 400 V2 is recognized as dual material bay (`HAS_DUAL_MATERIAL_BAY = True`)
   - Verify Dragon 400 (V1) continues to work as single bay (`HAS_DUAL_MATERIAL_BAY = False`)
   - Verify TwinDragon continues to work with dual nozzle (no dual material bay)
   - Verify PTFE distances are correctly loaded (960mm upstream, 350mm branch, 1310mm total)

2. **UI visibility tests:**
   - Verify Bay B elements visible only for Dragon 400 V2
   - Verify Bay B elements hidden for Dragon 400 V1 and TwinDragon
   - Verify active indicator updates correctly on bay operations

3. **Filament change workflow tests - Dual Material Bay:**
   - Test load into Bay A when both bays empty → Should succeed
   - Test load into Bay B when both bays empty → Should succeed
   - Test load into Bay A when Bay B has filament → Should FAIL with error message
   - Test load into Bay B when Bay A has filament → Should FAIL with error message
   - Test unload from Bay A when Bay A is loaded → Should succeed
   - Test unload from Bay B when Bay B is loaded → Should succeed
   - Test unload from Bay A when Bay A is empty → Should FAIL with error message

4. **Extrusion distance tests:**
   - Verify Dragon 400 V2 uses 1310mm for load/unload operations
   - Verify Dragon 400 V1 uses standard ptfeTubeLength (1500mm)
   - Verify TwinDragon uses standard ptfeTubeLength (2250mm)

5. **State persistence tests:**
   - Verify bay states saved to preference store correctly
   - Verify correct bay restored on screen refresh
   - Verify active bay indicator matches stored state

6. **End-to-end filament change tests:**
   - Full load workflow: Heat → Pull-in → Extrude to nozzle → Done
   - Full unload workflow: Heat → Prime → Tip-shape → Retract → Done
   - Verify state updates after successful load/unload

---

## Implementation Order

### Recommended Sequence:

**Phase 1: Qt UI Files (Can be done first by UI/Designer)**
1. **Task 1.1.1**: Add Bay B UI elements to filamentManagementScreen.ui
2. **Task 1.2.1-1.2.3**: Create filament path images
3. **Visual verification** in Qt Designer

**Phase 2: Firmware (Can be done independently)**
1. **Task 2.4.1**: Create MATERIAL_BAY_B_FILAMENT_RUNOUT_SENSOR.cfg
2. **Task 2.3.1**: Create DUAL_MATERIAL_BAY_MACROS.cfg
3. **Task 2.2.1**: Create PRINTER_DRAGON_400_V2.cfg
4. **Test firmware** on hardware - verify motor sync, sensor switching

**Phase 3: Python Code (Requires Phase 1 UI to be complete)**
1. **Task 3.1.1-3.1.2**: Update config modules (printer_config_manager, config.py)
2. **Task 3.2.1**: Update printer_model.py
3. **Task 3.3.1-3.3.2**: Update printer_preference_store.py
4. **Task 3.4.1**: Update printer_ui_config.py
5. **Task 3.5.1**: Update filamentManagementScreen.py
6. **Task 3.6.1-3.6.5**: Update changeFilamentWizard.py (core logic)
7. **Task 3.7.1-3.7.3**: Add validation logic
8. **Integration testing** (requires Phase 2 firmware on printer)

---

## Identified Complications and Gaps

After reviewing the current codebase architecture, the following items need attention:

### Issue 1: `_on_tool_state_changed` Only Updates Primary Bay UI

**File**: [filamentManagementScreen.py](octoprint_ControlCenter/ui/filament_management_screen/filamentManagementScreen.py#L300-L304)

**Problem**: The current signal handler only updates UI for the "default" bay:
```python
def _on_tool_state_changed(self, tool: str, bay: str, data: dict):
    # For now, reflect only primary bay changes on screen
    if bay == self.main_window.printer_model.get_default_bay(tool):
        self._apply_tool_ui(tool, data)
```

**Solution Required**: Update to handle both `material_bay_a` and `material_bay_b` for tool0:
```python
def _on_tool_state_changed(self, tool: str, bay: str, data: dict):
    if tool == "tool0":
        if bay == "material_bay_a":
            self._apply_tool_ui(tool, "material_bay_a", data)
        elif bay == "material_bay_b" and config.HAS_DUAL_MATERIAL_BAY:
            self._apply_tool_ui(tool, "material_bay_b", data)
    elif tool == "tool1" and bay == "material_bay_x":
        self._apply_tool_ui(tool, "material_bay_x", data)
```

### Issue 2: `_apply_tool_ui` Method Signature Needs Bay Parameter

**File**: [filamentManagementScreen.py](octoprint_ControlCenter/ui/filament_management_screen/filamentManagementScreen.py#L265-L290)

**Problem**: Current method takes only `(tool, data)` - doesn't know which bay to update.

**Solution Required**: Add bay parameter and handle both Bay A and Bay B UI elements.

### Issue 3: `_on_tool_states_loaded` Uses Default Bay Only

**File**: [filamentManagementScreen.py](octoprint_ControlCenter/ui/filament_management_screen/filamentManagementScreen.py#L293-L298)

**Problem**: Only loads state for default bay, won't load Bay B state on screen init.

**Solution Required**: Load both bays for dual material bay printers:
```python
def _on_tool_states_loaded(self, states: dict):
    m = self.main_window.printer_model
    t0_a = m.get_bay_state("tool0", "material_bay_a")
    self._apply_tool_ui("tool0", "material_bay_a", t0_a)
    if config.HAS_DUAL_MATERIAL_BAY:
        t0_b = m.get_bay_state("tool0", "material_bay_b")
        self._apply_tool_ui("tool0", "material_bay_b", t0_b)
    t1 = m.get_bay_state("tool1", "material_bay_x")
    self._apply_tool_ui("tool1", "material_bay_x", t1)
```

### Issue 4: `printer_config_manager.py` Doesn't Parse New Variables

**File**: [printer_config_manager.py](octoprint_ControlCenter/utils/printer_config_manager.py#L300-L360)

**Problem**: `extract_printer_configuration()` only extracts existing variables, doesn't include:
- `has_dual_material_bay`
- `active_material_bay`
- `ptfe_bay_branch_length`
- `ptfe_total_retract`

**Solution Required**: Add these to the extraction:
```python
config = {
    # ... existing ...
    'hasDualMaterialBay': bool(variables.get('has_dual_material_bay', 0)),
    'activeMaterialBay': variables.get('active_material_bay', 'A'),
    'ptfeBayBranchLength': variables.get('ptfe_bay_branch_length', 350),
    'ptfeTotalRetract': variables.get('ptfe_total_retract', 1310),
}
```

### Issue 5: `config.py` Needs to Load and Expose New Variables

**File**: [config.py](octoprint_ControlCenter/config.py#L68-L105)

**Problem**: `load_printer_config_from_klipper()` doesn't handle the new dual material bay variables.

**Solution Required**: Add globals and loading for:
```python
# Add defaults
DEFAULT_HAS_DUAL_MATERIAL_BAY = False
DEFAULT_PTFE_BAY_BRANCH_LENGTH = 350
DEFAULT_PTFE_TOTAL_RETRACT = 1310

# Add runtime variables
HAS_DUAL_MATERIAL_BAY = DEFAULT_HAS_DUAL_MATERIAL_BAY
PTFE_BAY_BRANCH_LENGTH = DEFAULT_PTFE_BAY_BRANCH_LENGTH
PTFE_TOTAL_RETRACT = DEFAULT_PTFE_TOTAL_RETRACT

# In load_printer_config_from_klipper():
global HAS_DUAL_MATERIAL_BAY, PTFE_BAY_BRANCH_LENGTH, PTFE_TOTAL_RETRACT
if 'hasDualMaterialBay' in config:
    HAS_DUAL_MATERIAL_BAY = config['hasDualMaterialBay']
# ... etc
```

### Issue 6: `printer_model.py` `_load_printer_configuration` Needs New Properties

**File**: [printer_model.py](octoprint_ControlCenter/models/printer_model.py#L520-L545)

**Problem**: Model's `_load_printer_configuration()` doesn't copy new variables from config module.

**Solution Required**: Add:
```python
self.has_dual_material_bay = config.HAS_DUAL_MATERIAL_BAY
self.ptfe_bay_branch_length = config.PTFE_BAY_BRANCH_LENGTH
self.ptfe_total_retract = config.PTFE_TOTAL_RETRACT
```

### Issue 7: `printer_model.py` `get_default_bay` Needs Dual Bay Awareness

**File**: [printer_model.py](octoprint_ControlCenter/models/printer_model.py#L500)

**Problem**: Current implementation always returns `material_bay_a` for tool0:
```python
def get_default_bay(self, tool: str) -> str:
    return "material_bay_a" if tool == "tool0" else "material_bay_x"
```

This is fine for initial display, but need to add `get_all_bays_for_tool()` as planned.

### Issue 8: `printer_model.py` Initial `tools` Dict Needs Bay B

**File**: [printer_model.py](octoprint_ControlCenter/models/printer_model.py#L91-L98)

**Problem**: Initial tools dict doesn't include `material_bay_b`:
```python
self.tools = {
    "tool0": {
        "material_bay_a": {"filament": None, "status": "Unknown", "nozzle": "Unknown"}
    },
    # ... material_bay_b missing
}
```

**Solution Required**: Conditionally add bay_b or always include it (hidden for non-dual-bay printers).

### Issue 9: Edit Dialog Only Handles Default Bay

**File**: [filamentManagementScreen.py](octoprint_ControlCenter/ui/filament_management_screen/filamentManagementScreen.py#L307-L400)

**Problem**: `_open_edit_dialog(tool)` only edits the default bay.

**Solution Required**: Add bay parameter support:
```python
def _open_edit_dialog(self, tool: str, bay: str = None):
    bay = bay or model.get_default_bay(tool)
    # ... rest of logic uses specific bay
```

And wire Bay B edit button:
```python
if self.editTool0MaterialBayB:
    self.editTool0MaterialBayB.clicked.connect(
        lambda: self._open_edit_dialog("tool0", "material_bay_b")
    )
```

### Issue 10: `changeFilamentWizard.setup()` Bay Param Already Partially Structured

**File**: [changeFilamentWizard.py](octoprint_ControlCenter/ui/filament_management_screen/changeFilamentWizard/changeFilamentWizard.py#L489-L515)

**Good News**: The existing `setup()` method already accepts params dict, making it easy to add bay handling:
```python
def setup(self, params=None):
    # Normalize params to a dict
    if isinstance(params, str):
        params = {'tool': params}
    # ... can add bay = params.get('bay', 'A') easily
```

### Issue 11: Home Screen May Need Dual Bay Status Display

**Current Plan**: Focuses on filamentManagementScreen only.

**Question**: Does the home screen need to show which bay is active or loaded status for both bays? Currently shows single filament per tool.

**Recommendation**: Add to Phase 1/3 if home screen needs dual bay indicators.

### Issue 12: GCode Response Handling for Bay Sync Confirmation

**Problem**: When sending `SYNC_MATERIAL_BAY BAY=A`, how does the UI confirm the command succeeded?

**Options**:
1. Fire-and-forget (current approach in plan)
2. Query `GET_ACTIVE_MATERIAL_BAY` after and parse response
3. Use websocket to listen for `RESPOND` messages

**Recommendation**: Start with fire-and-forget, add confirmation in a later iteration if needed.

### Issue 13: What Happens If User Switches Printer Config?

**Scenario**: User on Dragon 400 V2, has Bay B loaded, switches to Dragon 400 V1.

**Problem**: Bay B state persists in preference store, but new printer doesn't support it.

**Solution**: On printer config change, either:
1. Ignore Bay B state for non-dual-bay printers (cleanest)
2. Clear Bay B state on config switch

**Recommendation**: Option 1 - just hide Bay B UI, state is harmless.

### Issue 14: Testing Environment Consideration

**Problem**: Development/testing may not have actual Dragon 400 V2 hardware.

**Recommendation**: Add a debug flag in config.py to simulate dual material bay mode:
```python
DEBUG_FORCE_DUAL_MATERIAL_BAY = False  # Set True for UI testing without hardware
```

---

## Notes and Considerations

### Hardware Pin Assignments
The sensor pin assignments (PF0, PA0) in the Bay B sensor configs are **placeholders**. These must be verified against the actual hardware configuration of the Dragon 400 V2 mainboard before deployment.

### Backward Compatibility
All changes are designed to be backward compatible:
- Existing printers (Dragon 400, TwinDragon) will continue to work unchanged
- New `has_dual_material_bay` variable defaults to 0/False
- UI conditionally shows/hides elements based on printer type
- Python code falls back to standard behavior when dual bay is not configured

### Key Design Principle: Separation of Concerns
- **Qt UI files** handle: Visual layout and element placement
- **Klipper firmware** handles: Motor synchronization, sensor management, state variables
- **Python UI code** handles: User workflow, heating, step-by-step extrusion/retraction, validation, persistence

### Validation Rules for Dual Material Bay
1. **Cannot have filament loaded in both bays simultaneously** - The Y-splitter means only one filament path can be active
2. **Must unload before loading into different bay** - Prevents filament collision
3. **Bay sync must happen before any extrusion** - Ensures correct motor is active

### Future Enhancements (Out of Scope for This Implementation)
- Mid-print filament switching via M600 (would require slicer integration)
- Automatic material detection per bay
- Multi-color/multi-material printing using bay switching during print

---

## File Change Summary

### New Files to Create:
| File | Phase | Description |
|------|-------|-------------|
| `ui/resources/img/Filament Paths/dualBayLeftLoaded.png` | 1 | Bay A loaded image |
| `ui/resources/img/Filament Paths/dualBayRightLoaded.png` | 1 | Bay B loaded image |
| `ui/resources/img/Filament Paths/dualBayNoneLoaded.png` | 1 | Both bays empty image |
| `firmware/PRINTER_DRAGON_400_V2.cfg` | 2 | Main printer config (includes Bay B jam sensor inline) |
| `firmware/DUAL_MATERIAL_BAY_MACROS.cfg` | 2 | GCode macros for bay sync and sensor control |
| `firmware/MATERIAL_BAY_B_FILAMENT_RUNOUT_SENSOR.cfg` | 2 | Bay B runout sensor config |

### Files to Modify:
| File | Phase | Changes |
|------|-------|---------|
| `ui/filament_management_screen/filamentManagementScreen.ui` | 1 | Add Bay B UI elements |
| `utils/printer_config_manager.py` | 3 | Parse new PRINTER_VARIABLES |
| `utils/printer_preference_store.py` | 3 | Add material_bay_b to DEFAULT_STATE, add active bay methods |
| `utils/printer_ui_config.py` | 3 | Add dual material bay visibility rules |
| `config.py` | 3 | Add HAS_DUAL_MATERIAL_BAY, PTFE config variables |
| `models/printer_model.py` | 3 | Add dual bay support, get_all_bays_for_tool method |
| `ui/filament_management_screen/filamentManagementScreen.py` | 3 | Add Bay B UI bindings, active indicator |
| `ui/filament_management_screen/changeFilamentWizard/changeFilamentWizard.py` | 3 | Add bay handling, validation, updated distances |

---

## Appendix: GCode Command Reference

### SYNC_MATERIAL_BAY
```
SYNC_MATERIAL_BAY BAY=<A|B>
```
Syncs the specified material bay's extruder motor to the toolhead. Also enables that bay's filament sensors and disables the other bay's sensors.

### GET_ACTIVE_MATERIAL_BAY
```
GET_ACTIVE_MATERIAL_BAY
```
Reports which material bay is currently active (A or B).

### UNSYNC_ALL_MATERIAL_BAYS
```
UNSYNC_ALL_MATERIAL_BAYS
```
Unsyncs all material bay motors. Useful for debugging or manual control.

### SAVE_ACTIVE_BAY
```
SAVE_ACTIVE_BAY
```
Saves the current active bay to Klipper's persistent variables for restoration after restart.
