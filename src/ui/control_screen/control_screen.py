from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QSpinBox, QTabWidget, QToolButton, QStackedWidget
from utils.helpers import check_ui_elements

class ControlScreen(QWidget):
    def __init__(self, main_window):
        super(ControlScreen, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/control_screen/control_screen.ui', self)
            print("ControlScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ControlScreen UI file: {e}")

        # Find buttons by their object names
        self.controlBackButton = self.findChild(QPushButton, 'controlBackButton')
        self.setFeedRateButton = self.findChild(QPushButton, 'setFeedRateButton')
        self.moveZPBabyStep = self.findChild(QPushButton, 'moveZPBabyStep')
        self.moveZMBabyStep = self.findChild(QPushButton, 'moveZMBabyStep')
        self.cooldownButton = self.findChild(QPushButton, 'cooldownButton')
        self.fanOnButton = self.findChild(QPushButton, 'fanOnButton')
        self.fanOffButton = self.findChild(QPushButton, 'fanOffButton')
        self.toolToggleTemperatureButton = self.findChild(QPushButton, 'toolToggleTemperatureButton')
        self.tool180PreheatButton = self.findChild(QPushButton, 'tool180PreheatButton')
        self.tool250PreheatButton = self.findChild(QPushButton, 'tool250PreheatButton')
        self.setToolTempButton = self.findChild(QPushButton, 'setToolTempButton')
        self.bed60PreheatButton = self.findChild(QPushButton, 'bed60PreheatButton')
        self.bed100PreheatButton = self.findChild(QPushButton, 'bed100PreheatButton')
        self.setBedTempButton = self.findChild(QPushButton, 'setBedTempButton')
        self.moveYPButton = self.findChild(QPushButton, 'moveYPButton')
        self.moveYMButton = self.findChild(QPushButton, 'moveYMButton')
        self.moveXMButton = self.findChild(QPushButton, 'moveXMButton')
        self.moveXPButton = self.findChild(QPushButton, 'moveXPButton')
        self.homeXYButton = self.findChild(QPushButton, 'homeXYButton')
        self.moveZMButton = self.findChild(QPushButton, 'moveZMButton')
        self.moveZPButton = self.findChild(QPushButton, 'moveZPButton')
        self.homeZButton = self.findChild(QPushButton, 'homeZButton')
        self.toolToggleMotionButton = self.findChild(QPushButton, 'toolToggleMotionButton')
        self.extruderButton = self.findChild(QPushButton, 'extruderButton')
        self.retractButton = self.findChild(QPushButton, 'retractButton')
        self.step1mmButton = self.findChild(QPushButton, 'step1mmButton')
        self.step10mmButton = self.findChild(QPushButton, 'step10mmButton')
        self.step100mmButton = self.findChild(QPushButton, 'step100mmButton')
        self.motorOffButton = self.findChild(QPushButton, 'motorOffButton')
        self.changeFilamentButton = self.findChild(QToolButton, 'changeFilamentButton')
        self.toggleFilamentSensorButton = self.findChild(QToolButton, 'toggleFilamentSensorButton')
        self.setFlowRateButton = self.findChild(QPushButton, 'setFlowRateButton')

        # Find spin boxes
        self.feedRateSpinBox = self.findChild(QSpinBox, 'feedRateSpinBox')
        self.toolTempSpinBox = self.findChild(QSpinBox, 'toolTempSpinBox')
        self.bedTempSpinBox = self.findChild(QSpinBox, 'bedTempSpinBox')
        self.flowRateSpinBox = self.findChild(QSpinBox, 'flowRateSpinBox')

        # Find tab widget
        self.controlTabWidget = self.findChild(QTabWidget, 'controlTabWidget')

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
        """Connect buttons with safety checks"""
        # Connect navigation buttons
        if self.controlBackButton:
            self.controlBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        
        # Connect temperature control buttons
        if self.setFeedRateButton:
            self.setFeedRateButton.clicked.connect(self.set_feed_rate)
        if self.moveZPBabyStep:
            self.moveZPBabyStep.clicked.connect(self.move_z_positive)
        if self.moveZMBabyStep:
            self.moveZMBabyStep.clicked.connect(self.move_z_negative)
        if self.cooldownButton:
            self.cooldownButton.clicked.connect(self.cooldown)
        if self.fanOnButton:
            self.fanOnButton.clicked.connect(self.turn_fan_on)
        if self.fanOffButton:
            self.fanOffButton.clicked.connect(self.turn_fan_off)
        
        # Connect change filament button
        if self.changeFilamentButton:
            self.changeFilamentButton.clicked.connect(self.navigate_to_change_filament)
        
        # Add more button connections here as needed...

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

    # def open_change_filament_ui(self):
    #     """Navigate to the change filament UI."""
    #     # Assuming main_window has a QStackedWidget to manage screens
    #     stacked_widget = self.main_window.findChild(QStackedWidget, 'stackedWidget')
    #     if stacked_widget:
    #         stacked_widget.setCurrentIndex(stacked_widget.indexOf(self.main_window.change_filament_screen))