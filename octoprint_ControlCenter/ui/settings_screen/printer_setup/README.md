# Printer Setup Settings

This module provides the user interface for configuring printer types in the Control Center application.

## Files

- `printer_setup.py` - Main printer setup widget class
- `printer_setup.ui` - Qt Designer UI file defining the interface layout
- `README.md` - This documentation file

## Features

- Display current active printer configuration
- Dropdown selection of available printer types from firmware folder
- Cancel and Set buttons for applying changes
- Integration with printer configuration storage
- Automatic MCU configuration preservation
- User confirmation dialogs

## Dependencies

- `utils.printer_setup_utils` - Utility functions for parsing and modifying printer.cfg
- `utils.printer_config_store` - Persistent storage for printer configuration
- `utils.dialog` - Dialog utilities for user interaction

## Usage

The printer setup screen is accessed from the main settings menu and allows users to select between different printer configurations available in the firmware folder.
