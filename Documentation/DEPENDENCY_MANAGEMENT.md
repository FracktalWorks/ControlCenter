# Dependency Management System

## Overview
The dependency management system provides automatic installation of required Python packages during application startup, with progress feedback shown on the loading screen. This ensures a smooth user experience by handling dependencies transparently.

## Architecture

### Components

1. **`DependencyInstaller`** - Main dependency manager for startup
   - Runs during application loading
   - Provides progress feedback to loading screen
   - Handles bulk dependency installation

2. **`SimplifiedDependencyChecker`** - Lightweight checker for individual modules
   - Used by specific modules that need dependencies
   - Provides emergency installation if needed
   - Graceful fallback when dependencies unavailable

### Integration Points

- **Loading Screen**: Displays installation progress
- **Main Controller**: Orchestrates dependency checking during startup
- **Individual Modules**: Use simplified checker for specific needs

## Implementation Details

### Startup Flow
```
Application Start
    ↓
Dependency Check (0-50% progress)
    ↓
Connection Check (50-90% progress)  
    ↓
UI Initialization (90-100% progress)
```

### Dependencies Managed
- **PyYAML**: Configuration file parsing
- **OpenCV**: Camera functionality for tool offset calibration

### Progress Reporting
The system reports progress through Qt signals:
- `progress_signal(int, str)`: Progress percentage and status message
- `installation_complete_signal(bool)`: Success/failure notification

## Usage Examples

### In Application Startup (Main Controller)
```python
# Initialize dependency installer
self.dependency_installer = DependencyInstaller()
self.dependency_installer.progress_signal.connect(self.updateLoadingProgress)
self.dependency_installer.installation_complete_signal.connect(self.handleDependencyInstallation)

# Start dependency check
self.dependency_installer.check_and_install_dependencies()
```

### In Individual Modules
```python
from utils.dependency_manager import SimplifiedDependencyChecker

# Import with automatic installation fallback
cv2 = SimplifiedDependencyChecker.import_with_install(
    'cv2', 
    'opencv-python', 
    'Computer vision library for camera functionality'
)

# Check availability without installation
if SimplifiedDependencyChecker.is_available('yaml'):
    # Use YAML functionality
    pass
```

## Error Handling

### Installation Failures
- Continues application startup even if some dependencies fail
- Shows user-friendly error messages
- Disables features that require missing dependencies

### Fallback Strategies
1. Try standard pip installation
2. Attempt sudo pip installation (Linux/macOS)
3. Log error and continue without dependency
4. Disable affected features gracefully

## User Experience

### Loading Screen Messages
- "Checking dependencies..."
- "Installing PyYAML - YAML parser for configuration files"
- "Installing OpenCV - Computer vision library for camera functionality"
- "✓ All dependencies installed successfully"

### Progress Indicators
- Real-time progress bar updates
- Descriptive status messages
- Clear success/failure feedback

## Configuration

### Timeout Settings
- Installation timeout: 5 minutes per package
- Total dependency check: Part of overall startup timeout

### Package Specifications
Dependencies are defined in `DependencyInstaller.check_and_install_dependencies()`:
```python
dependencies = [
    {
        'name': 'PyYAML',
        'import_name': 'yaml',
        'package_name': 'PyYAML',
        'description': 'YAML parser for configuration files'
    },
    {
        'name': 'OpenCV',
        'import_name': 'cv2',
        'package_name': 'opencv-python',
        'description': 'Computer vision library for camera functionality'
    }
]
```

## Files Modified

### New Files
- `utils/dependency_manager.py` - Core dependency management logic

### Modified Files
- `controller/main_controller.py` - Integration with startup process
- `ui/calibrate_screen/cameraToolOffsetCalibration/cameraToolOffsetCalibration.py` - Updated to use new system
- `utils/printer_config_manager.py` - Updated to use new system

### Removed Dependencies
- Removed `opencv-python` from `setup.py` requirements
- Replaced inline installation code with centralized system

## Benefits

### For Users
- Automatic dependency resolution
- Clear progress feedback
- Graceful handling of installation failures
- No manual intervention required

### For Developers
- Centralized dependency management
- Consistent error handling
- Easy addition of new dependencies
- Clean separation of concerns

### For System Administrators
- Predictable installation behavior
- Comprehensive logging
- Fallback mechanisms for restricted environments
- No breaking changes to existing functionality

## Future Enhancements

### Planned Features
- Dependency caching to avoid repeated installations
- Version checking and updates
- Offline dependency packages
- Custom package repositories

### Potential Integrations
- Package managers (apt, yum, brew)
- Virtual environment management
- Docker container preparation
- CI/CD pipeline integration
