---
mode: 'agent'
tools: ['codebase']
description: 'Add camera integration features for calibration wizards'
---

# Add Camera Integration

Your goal is to add camera-based functionality to calibration wizards in the ControlCenter 3D printer interface.

## Requirements

Ask for the specific camera integration type (tool offset, bed leveling visualization, etc.) if not provided.

The camera integration should include:
* Camera preview setup and display
* Image capture for calibration analysis
* Integration with existing calibration workflows
* Error handling for camera operations
* User guidance for camera positioning

## Key Features

### Camera Preview
* Real-time camera feed display using QLabel
* Proper image scaling and aspect ratio
* Timer-based updates for smooth preview
* Resource cleanup when done

### Image Capture
* Snapshot capture for analysis
* Image processing for calibration data
* Integration with calibration calculations
* Save/export functionality if needed

### User Interface
* Camera preview area in wizard steps
* Capture buttons and controls
* Visual guides or overlays
* Clear instructions for positioning

## Implementation Pattern
Follow camera integration patterns from `.github/instructions.md`:
* Setup camera preview with QTimer updates
* Implement proper resource management
* Include error handling for camera failures
* Integrate with existing wizard step flow

## Technical Requirements
* Use QPixmap for image display
* Implement proper scaling for 800x480 display
* Handle camera connection errors gracefully
* Provide fallback options if camera unavailable

## UI Integration
* Add camera preview areas to existing wizard UI
* Include capture and control buttons
* Provide visual feedback during operations
* Maintain wizard navigation flow

Use the existing calibration wizard patterns and ensure camera operations don't block the UI thread.
