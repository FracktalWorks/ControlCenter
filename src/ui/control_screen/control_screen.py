from PyQt5 import uic
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QWidget, QPushButton, QSpinBox, QTabWidget, QToolButton
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

class ControlScreen(QWidget):
    def __init__(self, main_window):
        super(ControlScreen, self).__init__()
        self.main_window = main_window
        
        # Setup logger for this screen
        self.logger = setup_logger('control_screen')
        
        # Current movement step size
        self.step_size = 10  # Default to 10mm
        
        # Load UI and initialize elements
        self._load_ui()
        self._initialize_widgets()
        self._check_widgets_existence()
        self._connect_buttons()
        
        # Default to tab 0
        if self.controlTabWidget:
            self.controlTabWidget.setCurrentIndex(0)
            
    def _load_ui(self):
        """Load the UI file with error handling"""
        try:
            uic.loadUi('src/ui/control_screen/control_screen.ui', self)
            self.logger.info("ControlScreen UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load ControlScreen UI file: {e}")

    def _initialize_widgets(self):
        """Find and initialize all UI elements using a dictionary-based approach"""
        # Find tab widget with type information
        self.tab_components = {
            "controlTabWidget": {"type": QTabWidget, "instance": None}
        }
        
        # Navigation button (global - always visible)
        self.navigation_buttons = {
            "controlBackButton": {"type": QPushButton, "instance": None}
        }

        # ----- TAB 1: FEED RATE TAB ----- 
        # Feed rate control and bed height adjustment during print
        self.feed_rate_controls = {
            "feedRateSpinBox": {"type": QSpinBox, "instance": None},
            "setFeedRateButton": {"type": QPushButton, "instance": None},
            "moveZPBabyStep": {"type": QPushButton, "instance": None},
            "moveZMBabyStep": {"type": QPushButton, "instance": None}
        }

        # ----- TAB 2: TEMPERATURE TAB -----
        self.temperature_controls = {
            # Fan control
            "fanOnButton": {"type": QPushButton, "instance": None},
            "fanOffButton": {"type": QPushButton, "instance": None},
            "cooldownButton": {"type": QPushButton, "instance": None},
            # Tool (extruder) temperature control
            "toolToggleTemperatureButton": {"type": QPushButton, "instance": None},
            "tool180PreheatButton": {"type": QPushButton, "instance": None},
            "tool250PreheatButton": {"type": QPushButton, "instance": None},
            "toolTempSpinBox": {"type": QSpinBox, "instance": None},
            "setToolTempButton": {"type": QPushButton, "instance": None},
            # Bed temperature control
            "bed60PreheatButton": {"type": QPushButton, "instance": None},
            "bed100PreheatButton": {"type": QPushButton, "instance": None},
            "bedTempSpinBox": {"type": QSpinBox, "instance": None},
            "setBedTempButton": {"type": QPushButton, "instance": None}
        }

        # ----- TAB 3: MOTION TAB -----
        self.motion_controls = {
            # Movement increment control
            "step1mmButton": {"type": QPushButton, "instance": None},
            "step10mmButton": {"type": QPushButton, "instance": None},
            "step100mmButton": {"type": QPushButton, "instance": None},
            "motorOffButton": {"type": QPushButton, "instance": None},
            # Tool selection for motion
            "toolToggleMotionButton": {"type": QPushButton, "instance": None},
            # X/Y movement controls
            "moveXPButton": {"type": QPushButton, "instance": None},
            "moveXMButton": {"type": QPushButton, "instance": None},
            "moveYPButton": {"type": QPushButton, "instance": None},
            "moveYMButton": {"type": QPushButton, "instance": None},
            "homeXYButton": {"type": QPushButton, "instance": None},
            # Z movement controls
            "moveZPButton": {"type": QPushButton, "instance": None},
            "moveZMButton": {"type": QPushButton, "instance": None},
            "homeZButton": {"type": QPushButton, "instance": None},
            # Extruder controls
            "extruderButton": {"type": QPushButton, "instance": None},
            "retractButton": {"type": QPushButton, "instance": None}
        }

        # ----- TAB 4: FILAMENT TAB -----
        self.filament_controls = {
            # Flow rate control
            "flowRateSpinBox": {"type": QSpinBox, "instance": None},
            "setFlowRateButton": {"type": QPushButton, "instance": None},
            # Filament management
            "changeFilamentButton": {"type": QToolButton, "instance": None},
            "toggleFilamentSensorButton": {"type": QToolButton, "instance": None}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.tab_components)
        self.all_components.update(self.navigation_buttons)
        self.all_components.update(self.feed_rate_controls)
        self.all_components.update(self.temperature_controls)
        self.all_components.update(self.motion_controls)
        self.all_components.update(self.filament_controls)
        
        # Find all components using the dictionary
        self._find_components()
        
        # Store reference to controlTabWidget for easy access
        self.controlTabWidget = self.tab_components.get("controlTabWidget").get("instance")
        
        # Log initialization status
        self.logger.info("Control Screen widgets initialized")

        # Apply readonly, disabled, and palette settings to all spinboxes
        self._configure_spinboxes()

    def _configure_spinboxes(self):
        """Configure all spinboxes to be readonly, disabled, and styled."""
        spinboxes = [
            self.feed_rate_controls["feedRateSpinBox"].get("instance"),
            self.temperature_controls["toolTempSpinBox"].get("instance"),
            self.temperature_controls["bedTempSpinBox"].get("instance"),
            self.filament_controls["flowRateSpinBox"].get("instance")
        ]

        for spinbox in spinboxes:
            if spinbox:
                spinbox.lineEdit().setReadOnly(True)
                spinbox.lineEdit().setDisabled(True)
                palette = QPalette()
                palette.setColor(QPalette.Highlight, QColor(40, 40, 40))
                spinbox.lineEdit().setPalette(palette)

    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_type = component_info["type"]
            component = self.findChild(component_type, name)
            component_info["instance"] = component
            
            # Store a direct reference for easy access
            setattr(self, name, component)
            
            # Debug output
            if component:
                self.logger.debug(f"Found {component_type.__name__} '{name}'")
            else:
                self.logger.warning(f"Could not find {component_type.__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create mappings of component categories for reporting
        component_groups = {
            "ControlScreen - Tab Widget": {name: info["instance"] for name, info in self.tab_components.items()},
            "ControlScreen - Navigation Buttons": {name: info["instance"] for name, info in self.navigation_buttons.items()},
            "ControlScreen - Feed Rate Controls": {name: info["instance"] for name, info in self.feed_rate_controls.items()},
            "ControlScreen - Temperature Controls": {name: info["instance"] for name, info in self.temperature_controls.items()},
            "ControlScreen - Motion Controls": {name: info["instance"] for name, info in self.motion_controls.items()},
            "ControlScreen - Filament Controls": {name: info["instance"] for name, info in self.filament_controls.items()}
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)

    def _connect_buttons(self):
        """Connect buttons to their respective functions with safety checks"""
        # Navigation button
        self._connect_button(self.navigation_buttons, "controlBackButton", self._go_back)
        
        # ----- TAB 1: FEED RATE TAB -----
        self._connect_button(self.feed_rate_controls, "setFeedRateButton", self.set_feed_rate)
        self._connect_button(self.feed_rate_controls, "moveZPBabyStep", self.move_z_positive_baby_step)
        self._connect_button(self.feed_rate_controls, "moveZMBabyStep", self.move_z_negative_baby_step)
        
        # ----- TAB 2: TEMPERATURE TAB -----
        # Fan control
        self._connect_button(self.temperature_controls, "fanOnButton", self.turn_fan_on)
        self._connect_button(self.temperature_controls, "fanOffButton", self.turn_fan_off)
        self._connect_button(self.temperature_controls, "cooldownButton", self.cooldown)
        
        # Temperature control
        self._connect_button(self.temperature_controls, "setToolTempButton", self.set_tool_temp)
        self._connect_button(self.temperature_controls, "setBedTempButton", self.set_bed_temp)
        self._connect_button(self.temperature_controls, "toolToggleTemperatureButton", self.toggle_tool_temperature)
        self._connect_button(self.temperature_controls, "tool180PreheatButton", self.preheat_tool_180)
        self._connect_button(self.temperature_controls, "tool250PreheatButton", self.preheat_tool_250)
        self._connect_button(self.temperature_controls, "bed60PreheatButton", self.preheat_bed_60)
        self._connect_button(self.temperature_controls, "bed100PreheatButton", self.preheat_bed_100)
        
        # ----- TAB 3: MOTION TAB -----
        # Movement increment buttons
        self._connect_button(self.motion_controls, "step1mmButton", lambda: self.set_move_step(1))
        self._connect_button(self.motion_controls, "step10mmButton", lambda: self.set_move_step(10))
        self._connect_button(self.motion_controls, "step100mmButton", lambda: self.set_move_step(100))
        self._connect_button(self.motion_controls, "motorOffButton", self.motors_off)
        
        # Tool selection
        self._connect_button(self.motion_controls, "toolToggleMotionButton", self.toggle_tool_motion)
        
        # Movement controls
        self._connect_button(self.motion_controls, "moveXPButton", self.move_x_positive)
        self._connect_button(self.motion_controls, "moveXMButton", self.move_x_negative)
        self._connect_button(self.motion_controls, "moveYPButton", self.move_y_positive)
        self._connect_button(self.motion_controls, "moveYMButton", self.move_y_negative)
        self._connect_button(self.motion_controls, "homeXYButton", self.home_xy)
        self._connect_button(self.motion_controls, "moveZPButton", self.move_z_positive)
        self._connect_button(self.motion_controls, "moveZMButton", self.move_z_negative)
        self._connect_button(self.motion_controls, "homeZButton", self.home_z)
        
        # Extruder controls
        self._connect_button(self.motion_controls, "extruderButton", self.extrude)
        self._connect_button(self.motion_controls, "retractButton", self.retract)
        
        # ----- TAB 4: FILAMENT TAB -----
        self._connect_button(self.filament_controls, "setFlowRateButton", self.set_flow_rate)
        self._connect_button(self.filament_controls, "changeFilamentButton", self.navigate_to_change_filament)
        self._connect_button(self.filament_controls, "toggleFilamentSensorButton", self.toggle_filament_sensor)

    def _connect_button(self, button_dict, button_name, handler_function):
        """Helper method to safely connect a button to its handler"""
        if button_name in button_dict:
            button = button_dict[button_name]["instance"]
            if button:
                button.clicked.connect(handler_function)
                self.logger.debug(f"Connected {button_name} to handler")
            else:
                self.logger.warning(f"Could not connect {button_name} - button not found")
    
    # ===== NAVIGATION FUNCTIONS =====
    def _go_back(self):
        """Handle back button - return to previous screen"""
        self.main_window.switch_to_previous_screen()
        self.logger.info("Control Screen: returning to previous screen")
    
    # ===== TAB 1: FEED RATE FUNCTIONS =====
    def set_feed_rate(self):
        """Set the feed rate"""
        spinbox = self.feed_rate_controls["feedRateSpinBox"]["instance"]
        if spinbox:
            value = spinbox.value()
            self.logger.info(f"Setting feed rate to {value}%")
            # Add implementation to control the printer
            
    def move_z_positive_baby_step(self):
        """Fine Z adjustment - move up slightly during print"""
        self.logger.info("Moving Z up slightly (baby step)")
        # Add implementation to control the printer
        
    def move_z_negative_baby_step(self):
        """Fine Z adjustment - move down slightly during print"""
        self.logger.info("Moving Z down slightly (baby step)")
        # Add implementation to control the printer
    
    # ===== TAB 2: TEMPERATURE FUNCTIONS =====
    def turn_fan_on(self):
        """Turn the cooling fan on"""
        self.logger.info("Turning fan ON")
        # Add implementation to control the printer
        
    def turn_fan_off(self):
        """Turn the cooling fan off"""
        self.logger.info("Turning fan OFF")
        # Add implementation to control the printer
        
    def cooldown(self):
        """Cool down all heaters"""
        self.logger.info("Cooling down all heaters")
        # Add implementation to control the printer
    
    def set_tool_temp(self):
        """Set the tool temperature to the specified value"""
        spinbox = self.temperature_controls["toolTempSpinBox"]["instance"]
        if spinbox:
            value = spinbox.value()
            is_tool1 = self.get_active_tool_temp()
            tool_name = "Tool 1" if is_tool1 else "Tool 0"
            self.logger.info(f"Setting {tool_name} temperature to {value}°C")
            # Add implementation to control the printer
    
    def set_bed_temp(self):
        """Set the bed temperature to the specified value"""
        spinbox = self.temperature_controls["bedTempSpinBox"]["instance"]
        if spinbox:
            value = spinbox.value()
            self.logger.info(f"Setting bed temperature to {value}°C")
            # Add implementation to control the printer
    
    def toggle_tool_temperature(self):
        """Toggle between tool 0 and tool 1 for temperature control"""
        is_tool1 = self.get_active_tool_temp()
        self.logger.info(f"Toggled to Tool {1 if is_tool1 else 0} for temperature control")
        # Add implementation to update UI if needed
    
    def get_active_tool_temp(self):
        """Get the currently active tool for temperature control"""
        button = self.temperature_controls.get("toolToggleTemperatureButton", {}).get("instance")
        return button and button.isChecked()
    
    def preheat_tool_180(self):
        """Preheat tool to 180°C (PLA preset)"""
        is_tool1 = self.get_active_tool_temp()
        tool_name = "Tool 1" if is_tool1 else "Tool 0"
        self.logger.info(f"Preheating {tool_name} to 180°C")
        # Add implementation to control the printer
    
    def preheat_tool_250(self):
        """Preheat tool to 250°C (ABS/PETG preset)"""
        is_tool1 = self.get_active_tool_temp()
        tool_name = "Tool 1" if is_tool1 else "Tool 0"
        self.logger.info(f"Preheating {tool_name} to 250°C")
        # Add implementation to control the printer
    
    def preheat_bed_60(self):
        """Preheat bed to 60°C (PLA preset)"""
        self.logger.info("Preheating bed to 60°C")
        # Add implementation to control the printer
    
    def preheat_bed_100(self):
        """Preheat bed to 100°C (ABS preset)"""
        self.logger.info("Preheating bed to 100°C")
        # Add implementation to control the printer
    
    # ===== TAB 3: MOTION FUNCTIONS =====
    def set_move_step(self, step):
        """Set the movement step size"""
        self.step_size = step
        self.logger.info(f"Set movement step size to {step}mm")
        # Highlight the selected button and unhighlight others
        for button_name, step_value in [("step1mmButton", 1), ("step10mmButton", 10), ("step100mmButton", 100)]:
            button = self.motion_controls.get(button_name, {}).get("instance")
            if button:
                button.setFlat(step == step_value)
    
    def motors_off(self):
        """Turn off all stepper motors"""
        self.logger.info("Turning off all motors")
        # Add implementation to control the printer
    
    def toggle_tool_motion(self):
        """Toggle between tool 0 and tool 1 for motion control"""
        button = self.motion_controls.get("toolToggleMotionButton", {}).get("instance")
        is_tool1 = button and button.isChecked()
        self.logger.info(f"Toggled to Tool {1 if is_tool1 else 0} for motion control")
        # Add implementation to update UI if needed
    
    def move_x_positive(self):
        """Move X axis in positive direction"""
        self.logger.info(f"Moving X+ by {self.step_size}mm")
        # Add implementation to control the printer
    
    def move_x_negative(self):
        """Move X axis in negative direction"""
        self.logger.info(f"Moving X- by {self.step_size}mm")
        # Add implementation to control the printer
    
    def move_y_positive(self):
        """Move Y axis in positive direction"""
        self.logger.info(f"Moving Y+ by {self.step_size}mm")
        # Add implementation to control the printer
    
    def move_y_negative(self):
        """Move Y axis in negative direction"""
        self.logger.info(f"Moving Y- by {self.step_size}mm")
        # Add implementation to control the printer
    
    def home_xy(self):
        """Home X and Y axes"""
        self.logger.info("Homing X and Y axes")
        # Add implementation to control the printer
    
    def move_z_positive(self):
        """Move Z axis in positive direction"""
        self.logger.info(f"Moving Z+ by {self.step_size}mm")
        # Add implementation to control the printer
    
    def move_z_negative(self):
        """Move Z axis in negative direction"""
        self.logger.info(f"Moving Z- by {self.step_size}mm")
        # Add implementation to control the printer
    
    def home_z(self):
        """Home Z axis"""
        self.logger.info("Homing Z axis")
        # Add implementation to control the printer
    
    def extrude(self):
        """Extrude filament"""
        self.logger.info(f"Extruding filament by {self.step_size}mm")
        # Add implementation to control the printer
    
    def retract(self):
        """Retract filament"""
        self.logger.info(f"Retracting filament by {self.step_size}mm")
        # Add implementation to control the printer
    
    # ===== TAB 4: FILAMENT FUNCTIONS =====
    def set_flow_rate(self):
        """Set the flow rate"""
        spinbox = self.filament_controls["flowRateSpinBox"]["instance"]
        if spinbox:
            value = spinbox.value()
            self.logger.info(f"Setting flow rate to {value}%")
            # Add implementation to control the printer
    
    def navigate_to_change_filament(self):
        """Open the change filament screen and reset the wizard."""
        self.logger.info("Navigating to change filament screen")
        self.main_window.change_filament_screen.reset_wizard()
        self.main_window.switch_to_change_filament_screen()
    
    def toggle_filament_sensor(self):
        """Toggle the filament sensor on/off"""
        button = self.filament_controls.get("toggleFilamentSensorButton", {}).get("instance")
        is_on = button and button.isChecked()
        status = "ON" if is_on else "OFF"
        self.logger.info(f"Toggling filament sensor {status}")
        # Add implementation to control the printer
        
        # Update the button icon based on status
        if button:
            icon_name = "filamentSensorOn" if is_on else "filamentSensorOff"
            # Update icon if needed