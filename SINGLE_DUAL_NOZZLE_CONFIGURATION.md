# Single/Dual Nozzle Configuration Guide

This guide explains how to configure new UI elements or pages to work with both single and dual nozzle printer configurations.

## Overview

The ControlCenter project supports both single and dual nozzle printers. The configuration is controlled by:
- **Main Config**: `config.py` - `IS_DUAL_NOZZLE` boolean flag
- **UI Config Module**: `utils/printer_ui_config.py` - Handles UI element hiding and tool forcing

## Quick Setup for New UI Elements

### 1. For New UI Screens/Pages

When adding a new screen that has dual nozzle specific elements:

```python
# In your new screen file (e.g., ui/new_screen/new_screen.py)
from utils.printer_ui_config import apply_nozzle_config_to_screen

class NewScreen(QWidget):
    def __init__(self):
        super().__init__()
        # ... your UI setup code ...
        
        # Apply nozzle configuration (add this line)
        self.apply_nozzle_configuration()
    
    def apply_nozzle_configuration(self):
        """Apply nozzle configuration for this screen"""
        apply_nozzle_config_to_screen(self, 'new_screen')
```

### 2. For Individual UI Elements

If you have specific dual nozzle elements to hide:

```python
# In your UI file
from utils.printer_ui_config import hide_dual_nozzle_elements

# Hide specific elements
dual_elements = ['tool1Button', 'tool1Label', 'tool1Widget']
hide_dual_nozzle_elements(self, dual_elements)
```

### 3. For Custom Single Nozzle Styling

If you need custom styling for single nozzle mode (like border radius):

```python
# In your screen file
from utils.printer_ui_config import is_dual_nozzle_printer

def apply_nozzle_configuration(self):
    """Apply nozzle configuration and styling"""
    apply_nozzle_config_to_screen(self, 'your_screen')
    
    # Apply custom styling for single nozzle mode
    if not is_dual_nozzle_printer():
        self._apply_single_nozzle_styling()

def _apply_single_nozzle_styling(self):
    """Apply custom styling for single nozzle configuration."""
    if hasattr(self, 'someButton') and self.someButton:
        current_style = self.someButton.styleSheet()
        # Create proper CSS structure for QPushButton
        border_style = "QPushButton { border-top-left-radius: 15px; border-top-right-radius: 15px; }"
        # Combine existing style with new border style
        new_style = current_style + " " + border_style if current_style else border_style
        self.someButton.setStyleSheet(new_style)
        
    # Example for spinbox styling
    if hasattr(self, 'someSpinBox') and self.someSpinBox:
        current_style = self.someSpinBox.styleSheet()
        # Create proper CSS structure for QSpinBox
        border_style = "QSpinBox { border-bottom-left-radius: 15px; }"
        # Combine existing style with new border style
        new_style = current_style + " " + border_style if current_style else border_style
        self.someSpinBox.setStyleSheet(new_style)
```

### 4. For Tool Selection Logic

When handling tool selection in wizards or dialogs:

```python
# In wizard/dialog files
from utils.printer_ui_config import force_single_tool, is_dual_nozzle_printer

# Force tool1 to tool0 for single nozzle printers
selected_tool = force_single_tool(requested_tool)

# Check printer configuration
if is_dual_nozzle_printer():
    # Show dual nozzle options
else:
    # Hide or disable dual nozzle features
```

## Configuration Steps

### Step 1: Update Element Dictionary

Add your screen's dual nozzle elements to `utils/printer_ui_config.py`:

```python
DUAL_NOZZLE_ELEMENTS = {
    # ... existing screens ...
    'your_new_screen': [
        'tool1Button',
        'tool1Label', 
        'tool1Frame',
        'tool1TempDisplay',
        # Add all tool1/T1/dual-specific element names
    ]
}
```

### Step 2: Import and Apply Configuration

In your screen file, import and apply the configuration:

```python
from utils.printer_ui_config import apply_nozzle_config_to_screen

# In your __init__ or setup method:
self.apply_nozzle_configuration()

def apply_nozzle_configuration(self):
    """Apply nozzle configuration for this screen"""
    apply_nozzle_config_to_screen(self, 'your_screen_name')
```

## GitHub Copilot Automation Prompts

### For New UI Screens

```
Add single/dual nozzle configuration to this new UI screen. 
1. Import apply_nozzle_config_to_screen from utils.printer_ui_config
2. Add apply_nozzle_configuration() method that calls apply_nozzle_config_to_screen(self, 'screen_name')
3. Call self.apply_nozzle_configuration() in __init__ after UI setup
4. Identify all tool1/T1/dual nozzle UI elements in this screen
```

### For Element Dictionary Updates

```
Update the DUAL_NOZZLE_ELEMENTS dictionary in utils/printer_ui_config.py to include these new dual nozzle elements for 'screen_name': [list of element names that should be hidden for single nozzle printers]. Look for elements with 'tool1', 'T1', or dual-specific naming.
```

### For Custom Single Nozzle Styling

```
Add custom styling for single nozzle mode to this screen:
1. Import is_dual_nozzle_printer from utils.printer_ui_config
2. Modify apply_nozzle_configuration() to check if not is_dual_nozzle_printer() and call _apply_single_nozzle_styling()
3. Create _apply_single_nozzle_styling() method that applies custom CSS styling (like border-radius) to specific UI elements for single nozzle mode
4. Use proper CSS structure with selectors like "QPushButton { property: value; }" or "QSpinBox { property: value; }"
5. Combine existing styles with new styles using string concatenation and conditional logic
```

### For Wizard/Tool Selection Logic

```
Add single nozzle support to this wizard/dialog:
1. Import force_single_tool and is_dual_nozzle_printer from utils.printer_ui_config
2. Use force_single_tool() when selecting tools to convert tool1 to tool0 for single nozzle
3. Use is_dual_nozzle_printer() to conditionally show/hide dual nozzle options
4. Hide tool selection UI for single nozzle configuration
```

### For Finding Missing Elements

```
Search this UI file for any dual nozzle elements (containing 'tool1', 'T1', or dual-specific names) that should be hidden for single nozzle printers. Check both findChild() calls and direct element references. List them in the format needed for DUAL_NOZZLE_ELEMENTS dictionary.
```

## Testing Your Implementation

### Test Single Nozzle Mode
1. Set `IS_DUAL_NOZZLE = False` in `config.py`
2. Launch the application
3. Verify dual nozzle elements are hidden
4. Test tool selection defaults to tool0

### Test Dual Nozzle Mode  
1. Set `IS_DUAL_NOZZLE = True` in `config.py`
2. Launch the application
3. Verify all elements are visible
4. Test tool selection works for both tools

## Common Element Patterns

### UI Elements to Hide (Examples)
- `tool1*` - Any element starting with tool1
- `*T1*` - Any element containing T1
- `*Dual*` - Any element with dual in the name
- `idex*` - IDEX-specific elements
- `toolOffset*` - Tool offset calibration
- `toolToggle*` - Tool toggle buttons

### Elements to Keep Visible
- `tool0*` - Primary tool elements
- `*Bed*` - Bed-related elements
- `*Print*` - Print job elements
- Generic controls and displays

## File Structure

```
octoprint_ControlCenter/
├── config.py                          # Main configuration (IS_DUAL_NOZZLE)
├── utils/
│   └── printer_ui_config.py          # UI configuration module
└── ui/
    ├── main_window.py                 # Uses apply_nozzle_config_to_all_screens()
    ├── home_screen/
    ├── control_screen/
    ├── calibrate_screen/
    ├── filament_management_screen/
    └── your_new_screen/               # Your new screen here
```

## Best Practices

1. **Consistent Naming**: Use `tool1*` prefix for dual nozzle elements
2. **Single Method**: Use `apply_nozzle_config_to_screen()` for simplicity
3. **Complete Lists**: Include all dual nozzle elements in the configuration
4. **Test Both Modes**: Always test with both single and dual nozzle settings
5. **Tool Forcing**: Use `force_single_tool()` in wizards and tool selection logic

## Quick Validation

Run this test to verify your configuration works:

```bash
# Test imports
cd octoprint_ControlCenter
python -c "from utils.printer_ui_config import *; print('✅ Configuration working')"

# Test with single nozzle mode
# Set IS_DUAL_NOZZLE = False in config.py, then run app
```

---

**Need Help?** If you encounter issues:
1. Check that element names in `DUAL_NOZZLE_ELEMENTS` match exactly with `findChild()` calls
2. Verify imports are correct
3. Ensure `apply_nozzle_configuration()` is called after UI setup
4. Test with both `IS_DUAL_NOZZLE = True` and `False`
