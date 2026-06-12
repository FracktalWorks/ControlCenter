# ControlCenter — 3D Printer Control Application

## Project Overview
**ControlCenter** is a PyQt5 touchscreen interface for 3D printer control, integrating OctoPrint REST/WebSocket APIs with Klipper firmware. Runs on Raspberry Pi with an 800×480 touchscreen.

## Printer Family
- **Dragon** series: single-nozzle CoreXY, 400/500 build volume
- **TwinDragon** series: dual-nozzle CoreXY (IDEX-style), 400/600 variants
- **Volterra ALF**: single-nozzle variant
- Toolheads: TD-01 (primary), TD-02 (alternate)
- Material Bay (Dragon 400 V2): dual-bay Y-splitter with single nozzle

## Local Resources (always available)
- **Firmware configs**: `octoprint_ControlCenter/firmware/*.cfg`
- **Architecture docs**: `Documentation/*.md`
- **Existing instructions**: `.github/instructions.md` (wizard/UI patterns)
- **Prompt templates**: `.github/prompts/*.prompt.md`

## Key Architecture
- **Pattern**: Model-View-Presenter (MVP)
- **UI**: PyQt5 + Qt Designer (`.ui` files), 800×480 fixed resolution
- **Backend**: OctoPrint REST API + WebSocket (`octoprint_client/`)
- **Firmware**: Klipper with `PRINTER_VARIABLES` macro for dynamic config
- **Config manager**: `utils/printer_config_manager.py` parses active `printer.cfg`
- **Logging**: `utils/logger.py` with `get_logger(self.__class__.__name__)`

## Firmware Config Architecture
```
printer.cfg          ← selector: one [include PRINTER_<NAME>.cfg] uncommented
PRINTER_<NAME>.cfg   ← contains PRINTER_VARIABLES macro + printer-specific settings
BASE_DRAGON.cfg      ← common stepper/motor config for single-nozzle
BASE_TWINDRAGON.cfg  ← common config for dual-nozzle IDEX
CORE_GCODE_MACROS.cfg ← shared macros
TOOLHEADS_TD-01_TOOLHEAD0/1.cfg ← per-toolhead extruder/hotend config
```

## Persistence in Klipper
- `PRINTER_VARIABLES` macro: initial defaults only, resets on restart
- `/home/pi/variables.cfg` (save_variables): runtime state, survives restart

## Critical Coding Rules
- Always use `get_logger(self.__class__.__name__)` for logging
- Wrap OctoPrint calls in try-except; use `dialog.WarningOk()` for user errors
- UI resolution: always 800×480 with min/max constraints
- Dual-nozzle check: `is_dual_nozzle_printer()` from `utils/printer_ui_config.py`
- Signal/slot disconnect must be guarded against `TypeError` (already-disconnected)
