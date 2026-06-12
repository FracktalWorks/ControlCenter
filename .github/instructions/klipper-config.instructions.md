---
description: "Use when writing or editing Klipper firmware configuration files (.cfg) for Dragon, TwinDragon, or Volterra 3D printers. Covers PRINTER_VARIABLES, TMC5160 driver config, CoreXY kinematics, extruder/toolhead config, macro development, filament sensors, and save_variables persistence."
applyTo: "octoprint_ControlCenter/firmware/**/*.cfg"
---

# Klipper Configuration Standards

## Config File Architecture

```
printer.cfg          <- SELECTOR ONLY — one [include PRINTER_<NAME>.cfg] uncommented
PRINTER_<NAME>.cfg   <- PRINTER_VARIABLES macro + printer-specific [include] list
BASE_DRAGON.cfg      <- stepper/TMC config for single-nozzle CoreXY
BASE_TWINDRAGON.cfg  <- stepper/TMC config for IDEX dual-nozzle
CORE_GCODE_MACROS.cfg <- shared G-code macros (all printers)
TOOLHEADS_TD-01_TOOLHEAD0.cfg <- T0 extruder + hotend
TOOLHEADS_TD-01_TOOLHEAD1.cfg <- T1 extruder + hotend (IDEX only)
```

## PRINTER_VARIABLES Macro Rules
- **Location**: ONLY in `PRINTER_<NAME>.cfg`, NEVER in `printer.cfg`
- **Purpose**: Initial default values only — resets to these defaults on every Klipper restart
- **Runtime state**: Use `SAVE_VARIABLE` to `/home/pi/variables.cfg` for anything that must persist
- Required variables for all printers:

```cfg
[gcode_macro PRINTER_VARIABLES]
variable_is_dual_nozzle: False          # True for TwinDragon, False for Dragon/Volterra
variable_bed_x_min: 0
variable_bed_x_max: 400                 # machine X build dimension
variable_bed_y_min: 0
variable_bed_y_max: 400                 # machine Y build dimension
variable_bed_z_min: 0
variable_bed_z_max: 400                 # machine Z build dimension
variable_bed_calibration_x1: 110       # calibration point 1 X
variable_bed_calibration_y1: 18        # calibration point 1 Y
variable_bed_calibration_x2: 510       # calibration point 2 X (dual-nozzle)
variable_bed_calibration_y2: 18
variable_tool0_pause_position_x: -30
variable_tool0_pause_position_y: -77
variable_ptfe_tube_length: 1500
gcode:
```

## save_variables Persistence Pattern

```cfg
# In Klipper config
[save_variables]
filename: /home/pi/variables.cfg
```

```cfg
# In macros — reading persisted state
[gcode_macro EXAMPLE_MACRO]
gcode:
    {% set saved = printer.save_variables.variables %}
    {% set active_bay = saved.active_material_bay|default('A') %}
    # Use PRINTER_VARIABLES only for initial config, NOT runtime state
    {% set pvars = printer["gcode_macro PRINTER_VARIABLES"] %}
```

## TMC5160 Driver Config Pattern (all axes use SPI bus)

```cfg
[tmc5160 stepper_x]
cs_pin: PC13
spi_software_sclk_pin: PG8        # shared SPI bus
spi_software_mosi_pin: PG6
spi_software_miso_pin: PG7
interpolate: False                  # always False for precision
run_current: 1.20                   # XY: 1.0-1.5A typical
hold_current: 0.60                  # 50% of run_current
sense_resistor: 0.075               # all boards use 0.075
```

## Extruder Config Pattern (TD-01 Toolhead)

```cfg
[extruder]
step_pin: toolboard0: PD0
dir_pin: toolboard0: PD1
enable_pin: !toolboard0: PD2
microsteps: 16
rotation_distance: 7.710            # calibrate per-toolhead
nozzle_diameter: 0.400
filament_diameter: 1.750
heater_pin: toolboard0: PB13
sensor_type: ATC Semitec 104NT-4-R025H42G
sensor_pin: toolboard0: PA3
min_temp: 0
max_temp: 300
max_extrude_only_distance: 2000     # must be > PTFE tube length for loading
```

## Filament Sensor Patterns

```cfg
# Switch sensor (runout only)
[filament_switch_sensor T0_RUNOUT]
switch_pin: ^PC5
pause_on_runout: False              # let macros handle it
runout_gcode: FILAMENT_RUNOUT_T0
insert_gcode: FILAMENT_INSERT_T0

# Motion sensor (jam detection)
[filament_motion_sensor T0_JAM]
detection_length: 7.0               # mm of filament expected per measurement cycle
extruder: extruder
switch_pin: ^PC4
pause_on_runout: False
runout_gcode: FILAMENT_JAM_T0
```

## Dual Material Bay (Dragon 400 V2) Pattern

```cfg
# Second extruder motor (not synced by default)
[extruder_stepper extruder_side1]
extruder:                           # empty = not synced at startup
step_pin: PD4
dir_pin: PD3
enable_pin: !PD6
microsteps: 16
rotation_distance: 7.710
```

Motor sync during load/unload:
```cfg
SYNC_EXTRUDER_MOTION EXTRUDER=extruder_side1 MOTION_QUEUE=extruder   # sync
SYNC_EXTRUDER_MOTION EXTRUDER=extruder_side1 MOTION_QUEUE=            # unsync
```

## Macro Writing Rules
- Always guard moves: `{% if printer.idle_timeout.state != "Printing" %}`
- Use `M400` before reading temperatures or positions (waits for move queue)
- Local variables with `{% set var = value %}`
- Conditional includes: use `{% if pvars.is_dual_nozzle %}` style checks
- Support `DRY_RUN=1` parameter for testing macros without motion

## Common Mistakes to Avoid
- Do NOT define `PRINTER_VARIABLES` in `printer.cfg`
- Do NOT use `printer["gcode_macro PRINTER_VARIABLES"]` for runtime state
- Do NOT set `hold_current` above 60% of `run_current`
- Do NOT omit `max_extrude_only_distance` when PTFE tube is long
- Do NOT use `pause_on_runout: True` if custom runout macros are defined
