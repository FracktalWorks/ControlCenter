---
mode: 'agent'
tools: ['codebase']
description: 'Available prompts for ControlCenter development tasks'
---

# ControlCenter Development Prompts

This is an index of available prompt files for common development tasks in the ControlCenter 3D printer interface project.

## Available Prompts

### Feature Creation
* `/new-calibration-wizard` - Create new calibration wizards for the calibrate screen
* `/new-filament-wizard` - Create filament loading/unloading wizards
* `/new-settings-widget` - Create configuration settings widgets

### Enhancement
* `/add-control-features` - Add temperature, motion, or status controls to screens
* `/add-camera-integration` - Add camera functionality to calibration wizards

### Maintenance
* `/debug-and-fix` - Debug issues and implement fixes

## Usage

Type `/` followed by the prompt name in the chat input field to run a specific prompt.

Example: `/new-calibration-wizard` to create a new calibration wizard

## Project Context

All prompts are designed for the ControlCenter project:
* PyQt5-based touchscreen interface (800x480)
* OctoPrint and Klipper integration
* MVP architecture pattern
* Supports single and dual nozzle 3D printers

Refer to `.github/instructions.md` for detailed project context and coding standards.
