---
mode: 'agent'
tools: ['codebase']
description: 'Add enhanced controls to existing ControlCenter screens'
---

# Add Control Screen Features

Your goal is to add enhanced control features to existing screens in the ControlCenter 3D printer interface.

## Requirements

Ask for the specific control type (temperature, motion, status, etc.) and target screen if not provided.

The control feature should include:
* Real-time status monitoring with signal connections
* Safety checks for printer state before operations
* User-friendly error handling with dialog notifications
* Single/dual nozzle configuration support
* Proper logging for all operations

## Common Control Types

### Temperature Controls
* Individual tool temperature controls with spinboxes
* Real-time temperature display updates
* Preset temperature buttons
* Safety validation for temperature ranges

### Motion Controls
* Directional movement buttons with safety checks
* Homing controls (individual axes and all axes)
* Distance selection controls
* Position feedback display

### Status Monitoring
* Real-time printer status updates
* Visual indicators for different states
* Enable/disable controls based on status
* Connection status monitoring

## Implementation Pattern
Follow control enhancement patterns from `.github/instructions.md`:
* Connect to printer model signals for real-time updates
* Implement safety checks using `is_printer_operational()`
* Use proper error handling with `dialog.WarningOk()`
* Include logging for all operations

## Safety Requirements
* Check printer operational state before movements
* Prevent operations during printing
* Validate input ranges and parameters
* Provide clear error messages to user
* Log all operations and errors

## UI Enhancement
* Update existing UI files or create new control groups
* Follow 800x480 design constraints
* Use touch-friendly button sizes
* Provide visual feedback for operations
* Include status indicators

Use the existing codebase patterns and ensure all controls include proper safety validation.
