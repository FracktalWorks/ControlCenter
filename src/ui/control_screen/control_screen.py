from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QSpinBox, QTabWidget, QToolButton
from utils.helpers import check_ui_elements

class ControlScreen(QWidget):
    """
    Control Screen widget that provides printer control functionality:
    - Feed Rate and Bed Height Adjustment (Tab 1)
    - Temperature Control for Tool and Bed (Tab 2)
    - Motion Control for X, Y, Z axes and Extruder (Tab 3)
    - Filament Control including flow rate and filament sensor (Tab 4)
    """
    def __init__(self, main_window):
        super(ControlScreen, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/control_screen/control_screen.ui', self)
            print("ControlScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ControlScreen UI file: {e}")

        # Find tab widget
        self.controlTabWidget = self.findChild(QTabWidget, 'controlTabWidget')

        # Navigation button (global - always visible)
        self.controlBackButton = self.findChild(QPushButton, 'controlBackButton')

        # ----- TAB 1: FEED RATE TAB -----
        # Feed rate control and bed height adjustment during print
        self.feedRateSpinBox = self.findChild(QSpinBox, 'feedRateSpinBox')
        self.setFeedRateButton = self.findChild(QPushButton, 'setFeedRateButton')
        # Z-axis baby stepping for fine bed height adjustment during print
        self.moveZPBabyStep = self.findChild(QPushButton, 'moveZPBabyStep')  # Z+ (baby step)
        self.moveZMBabyStep = self.findChild(QPushButton, 'moveZMBabyStep')  # Z- (baby step)

        # ----- TAB 2: TEMPERATURE TAB -----
        # Fan control
        self.fanOnButton = self.findChild(QPushButton, 'fanOnButton')
        self.fanOffButton = self.findChild(QPushButton, 'fanOffButton') 
        self.cooldownButton = self.findChild(QPushButton, 'cooldownButton')
        # Tool (extruder) temperature control
        self.toolToggleTemperatureButton = self.findChild(QPushButton, 'toolToggleTemperatureButton')  # Switch between tools
        self.tool180PreheatButton = self.findChild(QPushButton, 'tool180PreheatButton')  # PLA preset
        self.tool250PreheatButton = self.findChild(QPushButton, 'tool250PreheatButton')  # ABS/PETG preset
        self.toolTempSpinBox = self.findChild(QSpinBox, 'toolTempSpinBox')
        self.setToolTempButton = self.findChild(QPushButton, 'setToolTempButton')
        # Bed temperature control
        self.bed60PreheatButton = self.findChild(QPushButton, 'bed60PreheatButton')  # PLA preset
        self.bed100PreheatButton = self.findChild(QPushButton, 'bed100PreheatButton')  # ABS preset
        self.bedTempSpinBox = self.findChild(QSpinBox, 'bedTempSpinBox')
        self.setBedTempButton = self.findChild(QPushButton, 'setBedTempButton')

        # ----- TAB 3: MOTION TAB -----
        # Movement increment control
        self.step1mmButton = self.findChild(QPushButton, 'step1mmButton')
        self.step10mmButton = self.findChild(QPushButton, 'step10mmButton')
        self.step100mmButton = self.findChild(QPushButton, 'step100mmButton')
        self.motorOffButton = self.findChild(QPushButton, 'motorOffButton')
        # Tool selection for motion
        self.toolToggleMotionButton = self.findChild(QPushButton, 'toolToggleMotionButton')
        # X/Y movement controls
        self.moveXPButton = self.findChild(QPushButton, 'moveXPButton')  # X+
        self.moveXMButton = self.findChild(QPushButton, 'moveXMButton')  # X-
        self.moveYPButton = self.findChild(QPushButton, 'moveYPButton')  # Y+
        self.moveYMButton = self.findChild(QPushButton, 'moveYMButton')  # Y-
        self.homeXYButton = self.findChild(QPushButton, 'homeXYButton')  # Home X/Y
        # Z movement controls
        self.moveZPButton = self.findChild(QPushButton, 'moveZPButton')  # Z+
        self.moveZMButton = self.findChild(QPushButton, 'moveZMButton')  # Z-
        self.homeZButton = self.findChild(QPushButton, 'homeZButton')    # Home Z
        # Extruder controls
        self.extruderButton = self.findChild(QPushButton, 'extruderButton')  # Extrude
        self.retractButton = self.findChild(QPushButton, 'retractButton')    # Retract

        # ----- TAB 4: FILAMENT TAB -----
        # Flow rate control
        self.flowRateSpinBox = self.findChild(QSpinBox, 'flowRateSpinBox')
        self.setFlowRateButton = self.findChild(QPushButton, 'setFlowRateButton')
        # Filament management
        self.changeFilamentButton = self.findChild(QToolButton, 'changeFilamentButton')
        self.toggleFilamentSensorButton = self.findChild(QToolButton, 'toggleFilamentSensorButton')

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions - with safety checks
        self._connect_buttons()

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Group widgets for better reporting
        navigation_buttons = {
            "controlBackButton": self.controlBackButton
        }
        check_ui_elements(self, navigation_buttons, "ControlScreen - Navigation Buttons")
        
        temperature_buttons = {
            "cooldownButton": self.cooldownButton,
            "fanOnButton": self.fanOnButton,
            "fanOffButton": self.fanOffButton,
            "toolToggleTemperatureButton": self.toolToggleTemperatureButton,
            "tool180PreheatButton": self.tool180PreheatButton,
            "tool250PreheatButton": self.tool250PreheatButton,
            "setToolTempButton": self.setToolTempButton,
            "bed60PreheatButton": self.bed60PreheatButton,
            "bed100PreheatButton": self.bed100PreheatButton,
            "setBedTempButton": self.setBedTempButton
        }
        check_ui_elements(self, temperature_buttons, "ControlScreen - Temperature Controls")
        
        movement_buttons = {
            "moveYPButton": self.moveYPButton,
            "moveYMButton": self.moveYMButton,
            "moveXMButton": self.moveXMButton,
            "moveXPButton": self.moveXPButton,
            "homeXYButton": self.homeXYButton,
            "moveZMButton": self.moveZMButton,
            "moveZPButton": self.moveZPButton,
            "homeZButton": self.homeZButton,
            "moveZPBabyStep": self.moveZPBabyStep,
            "moveZMBabyStep": self.moveZMBabyStep
        }
        check_ui_elements(self, movement_buttons, "ControlScreen - Movement Controls")
        
        extruder_buttons = {
            "toolToggleMotionButton": self.toolToggleMotionButton,
            "extruderButton": self.extruderButton,
            "retractButton": self.retractButton,
            "changeFilamentButton": self.changeFilamentButton,
            "toggleFilamentSensorButton": self.toggleFilamentSensorButton
        }
        check_ui_elements(self, extruder_buttons, "ControlScreen - Extruder Controls")
        
        settings_buttons = {
            "step1mmButton": self.step1mmButton,
            "step10mmButton": self.step10mmButton,
            "step100mmButton": self.step100mmButton,
            "motorOffButton": self.motorOffButton,
            "setFeedRateButton": self.setFeedRateButton,
            "setFlowRateButton": self.setFlowRateButton
        }
        check_ui_elements(self, settings_buttons, "ControlScreen - Settings Controls")
        
        input_widgets = {
            "feedRateSpinBox": self.feedRateSpinBox,
            "toolTempSpinBox": self.toolTempSpinBox,
            "bedTempSpinBox": self.bedTempSpinBox,
            "flowRateSpinBox": self.flowRateSpinBox,
            "controlTabWidget": self.controlTabWidget
        }
        check_ui_elements(self, input_widgets, "ControlScreen - Input Widgets")

    def _connect_buttons(self):
        """Connect buttons to their respective functions with safety checks."""
        # ----- NAVIGATION (GLOBAL) -----
        if self.controlBackButton:
            self.controlBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        
        # ----- TAB 1: FEED RATE TAB -----
        # Feed rate control
        if self.setFeedRateButton:
            self.setFeedRateButton.clicked.connect(self.set_feed_rate)
        # Bed height adjustment during print (baby stepping)
        if self.moveZPBabyStep:
            self.moveZPBabyStep.clicked.connect(self.move_z_positive_baby_step)
        if self.moveZMBabyStep:
            self.moveZMBabyStep.clicked.connect(self.move_z_negative_baby_step)
        
        # ----- TAB 2: TEMPERATURE TAB -----
        # Fan control
        if self.fanOnButton:
            self.fanOnButton.clicked.connect(self.turn_fan_on)
        if self.fanOffButton:
            self.fanOffButton.clicked.connect(self.turn_fan_off)
        # Temperature control
        if self.cooldownButton:
            self.cooldownButton.clicked.connect(self.cooldown)
        if self.setToolTempButton:
            self.setToolTempButton.clicked.connect(self.set_tool_temp)
        if self.setBedTempButton:
            self.setBedTempButton.clicked.connect(self.set_bed_temp)
        # Tool toggle button
        if self.toolToggleTemperatureButton:
            self.toolToggleTemperatureButton.clicked.connect(self.toggle_tool_temperature)
        # Preset temperatures
        if self.tool180PreheatButton:
            self.tool180PreheatButton.clicked.connect(self.preheat_tool_180)
        if self.tool250PreheatButton:
            self.tool250PreheatButton.clicked.connect(self.preheat_tool_250)
        if self.bed60PreheatButton:
            self.bed60PreheatButton.clicked.connect(self.preheat_bed_60)
        if self.bed100PreheatButton:
            self.bed100PreheatButton.clicked.connect(self.preheat_bed_100)
        
        # ----- TAB 3: MOTION TAB -----
        # Movement increment buttons
        if self.step1mmButton:
            self.step1mmButton.clicked.connect(lambda: self.set_move_step(1))
        if self.step10mmButton:
            self.step10mmButton.clicked.connect(lambda: self.set_move_step(10))
        if self.step100mmButton:
            self.step100mmButton.clicked.connect(lambda: self.set_move_step(100))
        # Motor control
        if self.motorOffButton:
            self.motorOffButton.clicked.connect(self.motors_off)
        # Tool selection
        if self.toolToggleMotionButton:
            self.toolToggleMotionButton.clicked.connect(self.toggle_tool_motion)
        # X/Y movement
        if self.moveXPButton:
            self.moveXPButton.clicked.connect(self.move_x_positive)
        if self.moveXMButton:
            self.moveXMButton.clicked.connect(self.move_x_negative)
        if self.moveYPButton:
            self.moveYPButton.clicked.connect(self.move_y_positive)
        if self.moveYMButton:
            self.moveYMButton.clicked.connect(self.move_y_negative)
        if self.homeXYButton:
            self.homeXYButton.clicked.connect(self.home_xy)
        # Z movement
        if self.moveZPButton:
            self.moveZPButton.clicked.connect(self.move_z_positive)
        if self.moveZMButton:
            self.moveZMButton.clicked.connect(self.move_z_negative)
        if self.homeZButton:
            self.homeZButton.clicked.connect(self.home_z)
        # Extruder control
        if self.extruderButton:
            self.extruderButton.clicked.connect(self.extrude)
        if self.retractButton:
            self.retractButton.clicked.connect(self.retract)
            
        # ----- TAB 4: FILAMENT TAB -----
        # Flow rate control
        if self.setFlowRateButton:
            self.setFlowRateButton.clicked.connect(self.set_flow_rate)
        # Filament management
        if self.changeFilamentButton:
            self.changeFilamentButton.clicked.connect(self.navigate_to_change_filament)
        if self.toggleFilamentSensorButton:
            self.toggleFilamentSensorButton.clicked.connect(self.toggle_filament_sensor)

    def navigate_to_change_filament(self):
        """Navigate to the change filament page."""
        if hasattr(self.main_window, 'reset_change_filament_process'):
            self.main_window.reset_change_filament_process()
        self.main_window.switch_to_change_filament_screen()

    def set_feed_rate(self):
        """Set the feed rate based on the spin box value."""
        if self.feedRateSpinBox:
            feed_rate = self.feedRateSpinBox.value()
            print(f"Feed rate set to: {feed_rate}%")
        else:
            print("Feed rate spin box not found")

    def move_z_positive(self):
        """Move the Z-axis in the positive direction."""
        print("Moving Z-axis in the positive direction")

    def move_z_negative(self):
        """Move the Z-axis in the negative direction."""
        print("Moving Z-axis in the negative direction")

    def cooldown(self):
        """Cooldown the printer."""
        print("Cooldown initiated")

    def turn_fan_on(self):
        """Turn the fan on."""
        print("Fan turned on")

    def turn_fan_off(self):
        """Turn the fan off."""
        print("Fan turned off")

    # ----- TAB 1: FEED RATE TAB METHODS -----
    def move_z_positive_baby_step(self):
        """Adjust bed height during print with small Z positive movement (baby step)."""
        print("Baby stepping Z+ for fine bed height adjustment")
        # API call would go here
        
    def move_z_negative_baby_step(self):
        """Adjust bed height during print with small Z negative movement (baby step)."""
        print("Baby stepping Z- for fine bed height adjustment")
        # API call would go here

    # ----- TAB 2: TEMPERATURE TAB METHODS -----
    def set_tool_temp(self):
        """Set the tool temperature based on the spin box value."""
        if self.toolTempSpinBox:
            tool_temp = self.toolTempSpinBox.value()
            print(f"Tool temperature set to: {tool_temp}°C")
            # API call would go here
        
    def set_bed_temp(self):
        """Set the bed temperature based on the spin box value."""
        if self.bedTempSpinBox:
            bed_temp = self.bedTempSpinBox.value()
            print(f"Bed temperature set to: {bed_temp}°C")
            # API call would go here
            
    def toggle_tool_temperature(self):
        """Toggle between extruders for temperature control."""
        is_checked = self.toolToggleTemperatureButton.isChecked()
        print(f"Temperature tool toggled to tool {2 if is_checked else 1}")
        # Update icon or text to indicate which tool is selected
        # API call would go here
        
    def preheat_tool_180(self):
        """Preheat tool to 180°C (PLA preset)."""
        print("Preheating tool to 180°C")
        self.toolTempSpinBox.setValue(180)
        # Optionally auto-apply the temperature
        self.set_tool_temp()
        
    def preheat_tool_250(self):
        """Preheat tool to 250°C (ABS/PETG preset)."""
        print("Preheating tool to 250°C")
        self.toolTempSpinBox.setValue(250)
        # Optionally auto-apply the temperature
        self.set_tool_temp()
        
    def preheat_bed_60(self):
        """Preheat bed to 60°C (PLA preset)."""
        print("Preheating bed to 60°C")
        self.bedTempSpinBox.setValue(60)
        # Optionally auto-apply the temperature
        self.set_bed_temp()
        
    def preheat_bed_100(self):
        """Preheat bed to 100°C (ABS preset)."""
        print("Preheating bed to 100°C")
        self.bedTempSpinBox.setValue(100)
        # Optionally auto-apply the temperature
        self.set_bed_temp()

    # ----- TAB 3: MOTION TAB METHODS -----
    def set_move_step(self, step_size):
        """Set the movement step size in mm."""
        print(f"Movement step size set to {step_size}mm")
        # Update UI to reflect selected step size
        # Store step size for use in movement commands
        
    def motors_off(self):
        """Turn off all stepper motors."""
        print("All motors disabled")
        # API call would go here
        
    def toggle_tool_motion(self):
        """Toggle between extruders for motion control."""
        is_checked = self.toolToggleMotionButton.isChecked()
        print(f"Motion tool toggled to tool {2 if is_checked else 1}")
        # Update icon or text to indicate which tool is selected
        # API call would go here
        
    def move_x_positive(self):
        """Move the X-axis in the positive direction."""
        print("Moving X+")
        # API call would go here
        
    def move_x_negative(self):
        """Move the X-axis in the negative direction."""
        print("Moving X-")
        # API call would go here
        
    def move_y_positive(self):
        """Move the Y-axis in the positive direction."""
        print("Moving Y+")
        # API call would go here
        
    def move_y_negative(self):
        """Move the Y-axis in the negative direction."""
        print("Moving Y-")
        # API call would go here
        
    def home_xy(self):
        """Home the X and Y axes."""
        print("Homing X and Y axes")
        # API call would go here
    
    def home_z(self):
        """Home the Z axis."""
        print("Homing Z axis")
        # API call would go here
        
    def extrude(self):
        """Extrude filament at the current position."""
        print("Extruding filament")
        # API call would go here
        
    def retract(self):
        """Retract filament at the current position."""
        print("Retracting filament")
        # API call would go here

    # ----- TAB 4: FILAMENT TAB METHODS -----
    def set_flow_rate(self):
        """Set the flow rate based on the spin box value."""
        if self.flowRateSpinBox:
            flow_rate = self.flowRateSpinBox.value()
            print(f"Flow rate set to: {flow_rate}%")
            # API call would go here
        
    def toggle_filament_sensor(self):
        """Toggle the filament runout sensor on/off."""
        is_checked = self.toggleFilamentSensorButton.isChecked()
        status = "enabled" if is_checked else "disabled"
        print(f"Filament sensor {status}")
        # Update icon to reflect status
        # API call would go here