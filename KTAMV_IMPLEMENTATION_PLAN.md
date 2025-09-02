# kTAMV Camera Tool Offset Calibration - Analysis & Implementation Plan

## Project Analysis

### **kTAMV Overview**
kTAMV (Klipper Tool Alignment using Machine Vision) is a sophisticated dual-component system for 3D printer tool offset calibration using computer vision. It consists of:

1. **Klipper Extension**: Integrates with Klipper firmware, providing G-code commands and printer control
2. **Flask Web Server**: Handles computer vision processing, camera operations, and mathematical calculations

### **Core Architecture Insights**

#### **1. Two-Phase Calibration Process**
- **Phase 1: Camera Calibration** (`KTAMV_CALIB_CAMERA`)
  - Moves nozzle in 10 predefined positions around center point
  - Maps pixel-to-millimeter relationship
  - Creates transformation matrix for coordinate conversion
  
- **Phase 2: Tool Centering** (`KTAMV_FIND_NOZZLE_CENTER`)
  - Uses calibrated camera to detect nozzle position
  - Iteratively moves tool to center of camera frame
  - Provides precise positioning for offset calculations

#### **2. Computer Vision Pipeline**
- **Multi-Algorithm Detection**: 5 different detector/preprocessor combinations
- **Blob Detection**: Uses OpenCV SimpleBlobDetector with varying sensitivity levels
- **Consistency Validation**: Requires 3 consecutive matching detections
- **Adaptive Processing**: Falls back through algorithms if detection fails

#### **3. Mathematical Framework**
- **Transformation Matrix**: Maps 2D camera coordinates to 3D printer space
- **Pixel-to-MM Conversion**: Calculated from calibration movements
- **Offset Calculation**: Uses matrix algebra for precise positioning

### **Computer Vision Detection Details**

#### **Detection Algorithms (5 Combinations)**
1. **Standard + Preprocessor 0**: YUV color space, Gaussian blur, adaptive threshold
2. **Standard + Preprocessor 1**: Grayscale, triangle threshold, Gaussian blur  
3. **Relaxed + Preprocessor 0**: Same as #1 but relaxed blob parameters
4. **Relaxed + Preprocessor 1**: Same as #2 but relaxed blob parameters
5. **Super-Relaxed + Preprocessor 2**: Median blur on grayscale

#### **Blob Detection Parameters**
- **Standard**: Area 400-900px, Circularity >0.8, Convexity >0.3
- **Relaxed**: Area 600-15000px, Circularity >0.6, Convexity >0.1  
- **Super-Relaxed**: Area >200px, all filters at 0.5 minimum

#### **Detection Validation**
- **Consistency Check**: Same position detected 3 times consecutively
- **Tolerance**: Configurable pixel tolerance (default: 0 pixels)
- **Timeout**: 20-second maximum detection time
- **Closest-to-Center**: If multiple circles found, use nearest to center

### **Workflow Process**

#### **Complete Calibration Sequence**
1. **Setup**: `KTAMV_SEND_SERVER_CFG` - Configure camera URL
2. **Preview**: `KTAMV_START_PREVIEW` - Visual positioning aid
3. **Camera Cal**: `KTAMV_CALIB_CAMERA` - Calibrate pixel-to-mm mapping
4. **Tool Center**: `KTAMV_FIND_NOZZLE_CENTER` - Center first tool
5. **Set Origin**: `KTAMV_SET_ORIGIN` - Mark reference position
6. **Tool Switch**: Change to second tool, repeat center/offset
7. **Get Offset**: `KTAMV_GET_OFFSET` - Calculate tool offset

#### **Camera Calibration Details (10 Points)**
```python
calibration_coordinates = [
    [0, -0.5],      # South
    [0.294, -0.405], # SE 
    [0.476, -0.155], # E-SE
    [0.476, 0.155],  # E-NE
    [0.294, 0.405],  # NE
    [0, 0.5],        # North
    [-0.294, 0.405], # NW
    [-0.476, 0.155], # W-NW
    [-0.476, -0.155],# W-SW
    [-0.294, -0.405] # SW
]
```

### **Key Technical Features**

#### **Robust Error Handling**
- **Nozzle Not Found**: Automatic toolhead wiggling to aid detection
- **Failed Calibration Points**: Skips bad points, requires 75% success rate
- **Statistical Filtering**: Removes outliers >20% from average
- **Boundary Checking**: Prevents moves outside camera frame

#### **Performance Optimizations**
- **Separate Server Process**: Offloads CV processing from Klipper
- **Threaded Operations**: Non-blocking camera operations
- **Frame Rate Control**: 30 FPS capture with 0.3s detection intervals
- **Memory Management**: Careful image copying to prevent segfaults

#### **User Experience Features**
- **Live Preview**: Real-time camera feed with detection overlay
- **Visual Feedback**: Crosshairs, detection circles, algorithm indicators
- **Progress Reporting**: Step-by-step calibration feedback
- **Debug Logging**: Comprehensive logging for troubleshooting

---

## Implementation Plan for ControlCenter

### **Phase 1: Core Computer Vision Module**

#### **1.1 Nozzle Detection System**
```python
class NozzleDetector:
    """OpenCV-based nozzle detection with multiple algorithms"""
    
    def __init__(self):
        self.detectors = self._create_blob_detectors()
        self.algorithms = [
            (self.detectors['standard'], self._preprocess_yuv),
            (self.detectors['standard'], self._preprocess_grayscale),
            (self.detectors['relaxed'], self._preprocess_yuv),
            (self.detectors['relaxed'], self._preprocess_grayscale),
            (self.detectors['super_relaxed'], self._preprocess_median)
        ]
    
    def detect_nozzle(self, frame):
        """Try multiple detection algorithms, return best result"""
        
    def find_nozzle_with_consistency(self, camera_thread, min_matches=3, timeout=20):
        """Detect nozzle with consistency validation"""
```

#### **1.2 Camera Calibration System**
```python
class CameraCalibrator:
    """Handles pixel-to-millimeter calibration"""
    
    def __init__(self, movement_controller):
        self.movement_controller = movement_controller
        self.calibration_points = self._generate_star_pattern()
    
    def calibrate_camera(self, nozzle_detector):
        """Perform 10-point calibration to create transformation matrix"""
        
    def calculate_pixel_to_mm_ratio(self, movements, detections):
        """Calculate mm/pixel from movement and detection data"""
```

#### **1.3 Mathematical Transformation**
```python
class CoordinateTransformer:
    """Handles coordinate transformations between camera and printer space"""
    
    def __init__(self):
        self.transformation_matrix = None
    
    def create_transformation_matrix(self, calibration_data):
        """Create matrix from calibration points using NumPy"""
        
    def camera_to_printer_coordinates(self, camera_x, camera_y):
        """Convert camera coordinates to printer coordinates"""
```

### **Phase 2: UI Integration**

#### **2.1 Enhanced Camera Tool Offset Screen**
- **Multi-Step Wizard**: 
  - Step 1: Camera Preview & Positioning
  - Step 2: Camera Calibration (10-point)
  - Step 3: Tool 1 Centering & Origin Setting
  - Step 4: Tool 2 Centering & Offset Calculation
  - Step 5: Offset Confirmation & Saving

#### **2.2 Real-Time Visual Feedback**
- **Detection Overlay**: Draw detected circles, crosshairs, algorithm indicators
- **Calibration Progress**: Show current calibration point and success rate
- **Live Coordinates**: Display current nozzle position in camera frame
- **Status Messages**: Real-time feedback on detection success/failure

#### **2.3 User Guidance System**
- **Interactive Instructions**: Step-by-step guidance with visual cues
- **Error Recovery**: Automatic suggestions when detection fails
- **Preview Mode**: Help users position nozzle correctly
- **Validation Checks**: Ensure proper setup before calibration

### **Phase 3: Backend Integration**

#### **3.1 OctoPrint Integration**
```python
class ToolOffsetController:
    """Interfaces with OctoPrint for printer control"""
    
    def __init__(self, octoprint_client):
        self.client = octoprint_client
        
    def move_relative(self, x=0, y=0, speed=1800):
        """Execute relative movement"""
        
    def get_current_position(self):
        """Get current toolhead position"""
        
    def save_tool_offset(self, tool_number, x_offset, y_offset):
        """Save calculated offset using M218 command"""
```

#### **3.2 Configuration Management**
- **Camera Settings**: Resolution, exposure, focus settings
- **Detection Parameters**: Sensitivity, timeout, consistency requirements
- **Movement Settings**: Speed, step size, calibration pattern
- **Tool Configuration**: Number of tools, active tool selection

#### **3.3 Data Persistence**
- **Calibration Data**: Save transformation matrix for reuse
- **Tool Offsets**: Store calculated offsets in printer firmware
- **Session Logs**: Detailed logging for troubleshooting
- **User Preferences**: Remember camera and detection settings

### **Phase 4: Advanced Features**

#### **4.1 Adaptive Detection**
- **Lighting Compensation**: Automatic exposure adjustment
- **Nozzle Type Detection**: Different parameters for different nozzle types
- **Background Subtraction**: Improve detection in noisy environments
- **Edge Enhancement**: Sharpen nozzle edges for better detection

#### **4.2 Quality Assurance**
- **Repeatability Testing**: Multiple calibration runs to verify consistency
- **Accuracy Validation**: Compare calculated vs manual measurements
- **Calibration Health**: Monitor calibration quality over time
- **Auto-Recalibration**: Suggest recalibration when accuracy degrades

#### **4.3 User Experience Enhancements**
- **Calibration Templates**: Pre-configured settings for common setups
- **Batch Calibration**: Calibrate multiple tools in sequence
- **Remote Operation**: Control calibration from mobile devices
- **Video Recording**: Record calibration sessions for review

---

## Implementation Priority

### **MVP (Minimum Viable Product)**
1. ✅ Basic camera feed display
2. ✅ Manual movement controls (1mm steps)
3. 🔄 Single-algorithm nozzle detection
4. 🔄 Semi-automatic centering
5. 🔄 Manual offset calculation

### **Enhanced Version** 
1. Multi-algorithm detection with fallbacks
2. Automatic camera calibration (10-point)
3. Full wizard workflow
4. Transformation matrix calculations
5. Automated offset saving

### **Professional Version**
1. Adaptive detection algorithms
2. Quality assurance features  
3. Advanced user interface
4. Integration with multiple printer types
5. Cloud-based AI detection (optional)

---

## Next Steps

1. **Start with Enhanced Nozzle Detection**: Implement the multi-algorithm approach
2. **Add Camera Calibration**: Implement the 10-point calibration system
3. **Create Wizard Workflow**: Build the multi-step UI process
4. **Integrate Mathematical Framework**: Add coordinate transformations
5. **Add Quality Assurance**: Implement validation and error handling

This plan adapts kTAMV's proven methodology while integrating seamlessly with your existing ControlCenter architecture and PyQt5 interface.
