# Dynamic Printer Configuration System

## Overview

This implementation creates a dynamic printer configuration system that extracts printer-specific settings from Klipper's `PRINTER_VARIABLES` macro instead of using hardcoded values in `config.py`. The system correctly follows Klipper's architecture where the main `printer.cfg` acts as a selector file that includes specific printer configurations, and the `PRINTER_VARIABLES` macro is defined in the individual `PRINTER_<NAME>.cfg` files.

## Architecture

### Configuration File Structure

```
/home/pi/                           # Klipper config directory
├── printer.cfg                    # Main selector file (no PRINTER_VARIABLES)
│   ├── [include PRINTER_DRAGON_400.cfg]     # Only one uncommented
│   ├── # [include PRINTER_DRAGON_500.cfg]   # Others commented out
│   └── # [include PRINTER_TWINDRAGON_600.cfg]
├── PRINTER_DRAGON_400.cfg         # Contains PRINTER_VARIABLES macro
├── PRINTER_DRAGON_500.cfg         # Contains PRINTER_VARIABLES macro
├── PRINTER_TWINDRAGON_600.cfg     # Contains PRINTER_VARIABLES macro
└── [other config files...]
```

### PRINTER_VARIABLES Location

- **❌ NOT in `printer.cfg`** - The main printer.cfg is a selector file only
- **✅ IN `PRINTER_<NAME>.cfg`** - Each printer configuration contains its own PRINTER_VARIABLES macro
- **✅ Copied to `/home/pi/`** - Files are deployed from firmware directory to Klipper config directory

## Key Changes

### 1. New Klipper Variables Parser (`utils/klipper_variables_parser.py`)

**Purpose**: Extracts and parses `PRINTER_VARIABLES` from the active printer configuration file.

**Key Functions**:
- `parse_printer_variables_from_file()` - Parses variables from a specific config file
- `get_printer_variables_from_active_config()` - Determines active printer and gets its variables
- `extract_printer_configuration()` - Converts raw variables to application configuration
- `get_printer_config_from_klipper()` - Main entry point for getting complete config

**Parser Logic**:
1. **Determine Active Printer**: Parse `printer.cfg` to find which `PRINTER_<NAME>.cfg` is active
2. **Look in Klipper Directory**: First try `/home/pi/PRINTER_<NAME>.cfg` (deployed location)
3. **Fallback to Firmware Directory**: If not found, try local firmware directory
4. **Extract Variables**: Parse the `PRINTER_VARIABLES` macro from the active printer file

**Extracted Configuration**:
- `machineBuildSize` - Calculated from `bed_x_min/max`, `bed_y_min/max`
- `calibrationPosition` - From explicit `variable_bed_calibration_**` variables or calculated fallback
- `tool0PurgePosition` - From `tool0_pause_position_x/y`
- `tool1PurgePosition` - From `tool1_pause_position_x/y` (only for dual nozzle printers)
- `ptfeTubeLength` - Calculated based on machine X dimension
- `IS_DUAL_NOZZLE` - From explicit `variable_is_dual_nozzle` or fan1 detection fallback

### 2. Updated Configuration System (`config.py`)

**Changes**:
- Moved printer-specific configs to "Default/fallback" section
- Added dynamic configuration variables that are updated at runtime
- Added `load_printer_config_from_klipper()` function
- Added `get_printer_config()` helper function

**Fallback Strategy**: System uses default values if Klipper configuration cannot be read, ensuring robust operation.

### 3. Enhanced Printer Model (`models/printer_model.py`)

**New Features**:
- `_load_printer_configuration()` - Loads config from Klipper during initialization
- `reload_printer_configuration()` - Public method to refresh configuration
- `get_printer_configuration()` - Returns current configuration as dictionary
- `printer_config_updated` signal - Notifies when configuration changes

**Integration**: Configuration is automatically loaded during:
- Printer model initialization
- WebSocket connection establishment
- Printer type changes

### 4. Updated Main Controller (`controller/main_controller.py`)

**Enhancement**: Added configuration reload in `onWebSocketConnected()` to ensure latest settings are loaded after Klipper connection is established.

### 5. Updated Printer Setup (`ui/settings_screen/printer_setup/printer_setup.py`)

**Enhancement**: Added configuration reload when printer type is changed to immediately update settings for the new printer.

## Configuration Mapping

### PRINTER_VARIABLES Structure

Each `PRINTER_<NAME>.cfg` file contains a `PRINTER_VARIABLES` macro with printer-specific settings:

```gcode
[gcode_macro PRINTER_VARIABLES]
# Printer Configuration
variable_is_dual_nozzle: 0  # 0 for single nozzle, 1 for dual nozzle

# Bed Calibration Positions (explicit coordinates)
variable_bed_calibration_x1: 77
variable_bed_calibration_y1: 24
variable_bed_calibration_x2: 365
variable_bed_calibration_y2: 24
variable_bed_calibration_x3: 224
variable_bed_calibration_y3: 376
variable_bed_calibration_x4: 224
variable_bed_calibration_y4: 236

# HeatBed size
variable_bed_x_min: 0
variable_bed_x_max: 430
variable_bed_y_min: 0
variable_bed_y_max: 400

# Pause/Purge Positions
variable_tool0_pause_position_x: -20
variable_tool0_pause_position_y: -20
# tool1 variables only exist for dual nozzle printers

# Print cooling fans names
variable_fan0: 'extruder_CF'
variable_fan1: 'extruder1_CF'  # Only for dual nozzle printers

# [other printer-specific variables...]
gcode:
```

### From PRINTER_VARIABLES to Application Config

| PRINTER_VARIABLES | Application Config | Priority/Source |
|------------------|-------------------|-----------------|
| `bed_x_min`, `bed_x_max` | `machineBuildSize.X` | `max - min` |
| `bed_y_min`, `bed_y_max` | `machineBuildSize.Y` | `max - min` |
| `bed_calibration_x1-4`, `bed_calibration_y1-4` | `calibrationPosition` | **Explicit values (preferred)** |
| Bed dimensions | `calibrationPosition` | Calculated fallback if explicit unavailable |
| `tool0_pause_position_x/y` | `tool0PurgePosition` | Direct mapping |
| `tool1_pause_position_x/y` | `tool1PurgePosition` | Direct mapping (dual nozzle only) |
| `is_dual_nozzle` | `IS_DUAL_NOZZLE` | **Explicit boolean (preferred)** |
| `fan1` presence | `IS_DUAL_NOZZLE` | Fallback detection if explicit unavailable |
| X dimension | `ptfeTubeLength` | `round(X * 2.5 / 300) * 300` |

### Calibration Position Strategy

The system uses a **explicit-first, calculated-fallback** approach:

1. **Preferred**: Use explicit `variable_bed_calibration_**` coordinates
2. **Fallback**: Calculate from bed dimensions if explicit values unavailable

**Explicit Coordinates** (used when available):
- Direct mapping from `bed_calibration_x1-4` and `bed_calibration_y1-4`

**Calculated Fallback** (backwards compatibility):
- **X1, Y1**: 18% from left, 6% from front (front-left)
- **X2, Y2**: 85% from left, 6% from front (front-right)
- **X3, Y3**: 52% from left, 94% from front (back-center)
- **X4, Y4**: 52% from left, 59% from front (center)

## Usage

### For Developers

```python
# Get current printer configuration
config = printer_model.get_printer_configuration()
print(f"Build size: {config['machineBuildSize']}")
print(f"Dual nozzle: {config['IS_DUAL_NOZZLE']}")
print(f"Calibration positions: {config['calibrationPosition']}")

# Reload configuration after changes
printer_model.reload_printer_configuration()

# Listen for configuration changes
printer_model.printer_config_updated.connect(on_config_changed)
```

### Configuration File Management

The system follows Klipper's standard architecture:

1. **Development**: Edit files in `firmware/` directory
2. **Deployment**: Use `copy_firmware_files()` to deploy to `/home/pi/`
3. **Selection**: Update `printer.cfg` to activate specific printer configuration
4. **Automatic**: Parser automatically finds and loads active configuration

### Example Printer Setup

```python
from utils.printer_setup_utils import copy_firmware_files

# Deploy all firmware files and activate DRAGON_400
success = copy_firmware_files("DRAGON_400")

# This will:
# 1. Copy all .cfg files to /home/pi/
# 2. Update printer.cfg to include PRINTER_DRAGON_400.cfg
# 3. Parser will automatically find PRINTER_VARIABLES in PRINTER_DRAGON_400.cfg
```

## Benefits

1. **Correct Architecture**: Follows Klipper's intended configuration structure
2. **Automatic Configuration**: UI settings automatically match the active printer
3. **Explicit Configuration**: Uses explicit calibration positions and dual nozzle settings
4. **Reduced Maintenance**: No need to manually update multiple configuration files
5. **Consistency**: Single source of truth for printer specifications
6. **Flexibility**: Easy to add new printer variants by creating new PRINTER_*.cfg files
7. **Robustness**: Graceful fallback to defaults and calculated values if needed
8. **Backwards Compatibility**: Supports both new explicit variables and old calculated values

## Testing

Multiple test scripts are provided to verify functionality:

```bash
# Test individual printer configuration parsing
python test_printer_config.py

# Test architecture and PRINTER_VARIABLES location
python test_config_architecture.py
```

These validate:
- All printer configurations can be properly parsed
- PRINTER_VARIABLES are in the correct location (PRINTER_<NAME>.cfg, not printer.cfg)
- Explicit bed calibration coordinates are used
- Dual nozzle detection works correctly
- Fallback behavior for missing variables

## Implementation Details

### Variable Naming Conventions

- **New**: `variable_bed_calibration_x1` - Clear, descriptive naming
- **Old**: `variable_calibration_x1` - Supported for backwards compatibility
- **Explicit**: `variable_is_dual_nozzle` - Direct boolean setting
- **Fallback**: Fan detection - Used if explicit setting unavailable

### Parser Priority Order

1. **Active Printer Detection**: Parse `printer.cfg` to find included printer file
2. **Klipper Directory**: Look for variables in `/home/pi/PRINTER_<NAME>.cfg`
3. **Firmware Directory**: Fallback to local `firmware/PRINTER_<NAME>.cfg`
4. **Explicit Variables**: Use `bed_calibration_**` and `is_dual_nozzle` if available
5. **Calculated Fallback**: Calculate positions and detect dual nozzle from other variables
6. **Default Values**: Use hardcoded defaults if all else fails

## Backwards Compatibility

The system maintains robust backwards compatibility through multiple fallback layers:

### Variable Name Compatibility
- **New naming**: `variable_bed_calibration_**` (preferred)
- **Old naming**: `variable_calibration_**` (still supported)
- **Dual nozzle**: Explicit `variable_is_dual_nozzle` preferred, fan detection fallback

### Configuration Sources
1. **Primary**: Explicit variables in active printer configuration
2. **Secondary**: Calculated values from bed dimensions and hardware detection
3. **Tertiary**: Hardcoded defaults in `config.py`

### API Compatibility
- Same variable names in `config.py` maintained
- Existing code accessing configuration variables continues to work
- No breaking changes to external interfaces

## Current Status

### ✅ Completed Features

1. **PRINTER_VARIABLES Consolidation**
   - Unified macro replacing IDEX_VARIABLES and DRAGON_VARIABLES
   - Consistent structure across all printer types

2. **Explicit Configuration Values**
   - `variable_bed_calibration_x1-4`, `variable_bed_calibration_y1-4`
   - `variable_is_dual_nozzle` with proper boolean values
   - Clear variable naming with `bed_calibration_**` prefix

3. **Architecture-Correct Parser**
   - Looks for PRINTER_VARIABLES in active `PRINTER_<NAME>.cfg`, not main `printer.cfg`
   - Searches Klipper directory first, firmware directory fallback
   - Proper active printer detection from include statements

4. **Dual Nozzle Handling**
   - Single nozzle printers: `is_dual_nozzle: 0`, no tool1 variables
   - Dual nozzle printers: `is_dual_nozzle: 1`, full tool1 configuration
   - Clean separation of single vs dual nozzle configurations

5. **Comprehensive Testing**
   - Test scripts validate all printer configurations
   - Architecture verification confirms correct PRINTER_VARIABLES location
   - Parser testing ensures robust variable extraction

### 📋 Printer Configuration Status

| Printer | Type | is_dual_nozzle | Bed Calibration | Status |
|---------|------|----------------|-----------------|---------|
| DRAGON_400 | Single | 0 | Explicit coordinates | ✅ Complete |
| DRAGON_500 | Single | 0 | Explicit coordinates | ✅ Complete |
| TWINDRAGON_600 | Dual | 1 | Explicit coordinates | ✅ Complete |
| TWINDRAGON_600x300 | Dual | 1 | Explicit coordinates | ✅ Complete |

## Future Enhancements

Potential improvements for future development:
- **Z-axis height extraction** from stepper configuration
- **Real-time configuration updates** when Klipper config changes
- **Configuration validation** and error reporting
- **Additional printer-specific settings** (temperatures, speeds, etc.)
- **Dynamic macro variable** support for runtime configuration changes
