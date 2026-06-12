---
description: "Use when debugging 3D printer issues: mechanical faults (skipping, layer issues, CoreXY problems), electronics faults (TMC driver errors, thermal runaway, endstop/sensor issues), Klipper software errors (MCU shutdown, move out of range, failed reset), or ControlCenter application bugs (WebSocket, OctoPrint API, UI freezes, signal errors)."
---

# 3D Printer Debugging Guide

## Step 1 — Identify the Domain

| Symptom | Domain |
|---------|--------|
| Grinding, skipping, belt noise, layer shifts | Mechanical |
| Driver errors, thermal runaway, MCU shutdown | Electronics |
| Klipper errors, macro failures, config parse errors | Klipper Software |
| UI freeze, WebSocket disconnect, API failures | ControlCenter App |

---

## Mechanical Debugging

### Motion / Skipping
1. Check belt tension (both A and B belts on CoreXY must be equal)
2. Inspect all pulley grub screws (2 per pulley, 120° offset recommended)
3. Verify motor run_current — too low causes skipping under load
4. Run `SHAPER_CALIBRATE` (ADXL345) to measure resonance and set `square_corner_velocity`
5. Check linear rail carriages for dirt or stiff points

### Layer Shifts (specific axis)
- X shift only: X endstop, X belt, X motor
- Y shift only: Y endstop, Y belt, Y motor
- Both axes: electrical noise, power supply dropout, USB disconnect

### Z Issues / First Layer
1. Run `Z_TILT_ADJUST` then `BED_MESH_CALIBRATE`
2. Check probe trigger consistency: `PROBE_ACCURACY SAMPLES=10` (stddev < 0.002mm)
3. Verify `position_endstop` in `[stepper_z]` matches physical probe trigger point
4. Check for thermal expansion: set bed/nozzle to print temps before probing

### IDEX (TwinDragon) Specific
1. T0/T1 X-offset calibration: use camera tool offset or manual test print
2. Parking positions in `PRINTER_VARIABLES`: `tool0_pause_position_x/y` and `tool1_pause_position_x/y`
3. Carriage collision check: ensure parking positions have sufficient clearance
4. Purge tower alignment: verify `tool0PurgePosition` and `tool1PurgePosition` in config

---

## Electronics Debugging

### TMC Stepper Driver Diagnostics
```gcode
DUMP_TMC STEPPER=stepper_x        ; Read all TMC registers
SET_TMC_CURRENT STEPPER=stepper_x CURRENT=1.0  ; Temporarily change current
```
Common faults:
- `DRV_STATUS: OTPW` — overtemperature warning, add cooling or reduce current
- `DRV_STATUS: OT` — overtemperature shutdown, reduce current immediately
- `DRV_STATUS: s2ga/s2gb` — short to ground on motor winding (wiring fault)
- `DRV_STATUS: ola/olb` — open load (disconnected motor wire)

### Thermal Runaway
1. Check thermistor type matches config (`sensor_type` in `[extruder]` / `[heater_bed]`)
2. Check wiring polarity of thermistor (not polarized, but check resistance: ~100kΩ at room temp for NTC 100k)
3. Run `PID_CALIBRATE HEATER=extruder TARGET=200` and `SAVE_CONFIG`
4. Check heater wiring continuity and SSR/MOSFET gate signal

### Endstop / Probe Issues
```gcode
QUERY_ENDSTOPS               ; Check all endstop states
QUERY_PROBE                  ; Check probe state (triggered / open)
```
- If inverted: add/remove `!` prefix on `endstop_pin`
- If noisy: add `^` pull-up: `endstop_pin: ^PF2`
- BLTouch/CRTouch: check `samples` and `sample_retract_dist` in `[probe]`

### Filament Sensor Issues
```gcode
QUERY_FILAMENT_SENSOR SENSOR=T0_RUNOUT
QUERY_FILAMENT_SENSOR SENSOR=T0_JAM
```
- `[filament_switch_sensor]`: check `switch_pin` logic level and pull-up
- `[filament_motion_sensor]`: tune `detection_length` (start at 7mm, increase if false positives)
- Ensure `pause_on_runout: False` when custom macros handle the event

---

## Klipper Software Debugging

### Reading klipper.log
Location: `~/klipper.log` on the Raspberry Pi
- Always read the full error context, not just the last line
- Look for the line BEFORE `MCU 'mcu' shutdown:` for the actual cause
- Serial reconnect spam: usually USB power/noise issue

### Common Klipper Errors
| Error | Root Cause | Fix |
|-------|------------|-----|
| `Timer too close` | USB instability, high CPU load | USB isolator, reduce `max_accel` |
| `Move out of range` | Homing failed, wrong `position_min/max` | Check endstops, re-home |
| `Extrude only move too long` | `max_extrude_only_distance` < tube length | Set > PTFE tube length |
| `Heater not heating at expected rate` | Wiring, PID, wrong thermistor | Check wiring, run `PID_CALIBRATE` |
| `TMC stepper_x: Driver error` | Overcurrent / overtemp | Reduce `run_current`, add cooling |
| `Failed automated reset of MCU` | Intentional restart race condition | Use grace-period pattern in app |
| `Config file error` | Syntax error in `.cfg` | Check indentation, missing `gcode:` |

### Intentional Restart MCU Error (ControlCenter specific)
This appears when the app sends a `RESTART` command and the WebSocket sees the MCU disconnect transient.
Fix is already implemented in `controller/main_controller.py` via `restart_klipper_and_wait()`.
See `Documentation/KLIPPER_RESTART_WAIT_UTILITY.md` for full details.

### Macro Debugging
```gcode
SET_GCODE_VARIABLE MACRO=PRINTER_VARIABLES VARIABLE=is_dual_nozzle VALUE=True
M118 Debug: {printer["gcode_macro PRINTER_VARIABLES"].is_dual_nozzle}
```
- Use `RESPOND MSG="value"` or `M118` to print debug values
- Check `~/klipper.log` for `gcode macro ... error` lines

---

## ControlCenter Application Debugging

### WebSocket / OctoPrint Connection Issues
1. Check `octoprint_client/websocket_client.py` reconnect logic
2. Look at `logs/` directory for application logs
3. Verify OctoPrint API key is valid and not expired
4. Check Raspberry Pi WiFi stability: `ping -c 10 <printer-ip>`

### UI Freeze or Non-Responsive Touch
1. Check if a long-running operation is blocking the Qt main thread
2. Long operations must use `@run_async` decorator from `utils/helpers.py`
3. UI updates from non-main threads must use signals, not direct widget calls

### Signal/Slot Errors
```python
# Symptom: RuntimeError: wrapped C++ object deleted
# Fix: disconnect signals before widget destruction

# Symptom: TypeError on disconnect
# Fix: guard disconnect with try/except TypeError
try:
    self.model.some_signal.disconnect(self.handler)
except TypeError:
    pass  # already disconnected
```

### Printer Config Not Loading
1. Check `utils/printer_config_manager.py` — it reads from `/home/pi/*.cfg` first
2. Fallback reads from `octoprint_ControlCenter/firmware/*.cfg`
3. If running locally (dev mode), fallback is always used
4. Check `Documentation/DYNAMIC_PRINTER_CONFIG.md` for config load order

### Dual Nozzle vs Single Nozzle Path Mismatch
- Use `is_dual_nozzle_printer(self.main_window)` to branch logic
- Check `variable_is_dual_nozzle` in the active `PRINTER_<NAME>.cfg`
- The value comes from `PRINTER_VARIABLES` at startup, loaded into `config.IS_DUAL_NOZZLE`
