---
mode: 'agent'
tools: ['codebase']
description: 'Create a new calibration wizard for the ControlCenter project'
---

# Create Calibration Wizard

Your goal is to create a new calibration wizard for the ControlCenter 3D printer interface.

## Requirements

Ask for the wizard name and specific calibration type if not provided.

The calibration wizard should include:
* Multi-step interface using QStackedWidget
* Position control and movement commands
* Temperature monitoring if needed
* Single/dual nozzle support using `is_dual_nozzle_printer()`
* Proper error handling and logging
* Integration with calibrate_screen.py

## File Structure
Create both Python and UI files in: `octoprint_ControlCenter/ui/calibrate_screen/[wizard_name]/`
* `[wizard_name].py` - Python implementation
* `[wizard_name].ui` - Qt Designer UI file

## Implementation Pattern
Follow the calibration wizard pattern from `.github/instructions.md`:
* Inherit from QWidget
* Use MVP architecture pattern
* Load UI with `uic.loadUi()`
* Initialize with `main_window` parameter
* Implement `showEvent()` for reset behavior
* Include `cancel_wizard()` method

## UI Design
Follow UI conventions from instructions:
* Fixed 800x480 resolution with constraints
* Dark theme: `background-color: rgb(40, 40, 40);`
* Proper element naming (camelCase, descriptive suffixes)
* QStackedWidget for multi-step navigation
* Touch-friendly design (44px minimum height)

## Integration Steps
1. Import in `calibrate_screen.py`
2. Add to `_initialize_sub_screens()` method
3. Connect button in `__init__` method
4. Add navigation method
5. Update main calibrate UI with new button

Use the existing codebase patterns and ensure compatibility with both single and dual nozzle printer configurations.
