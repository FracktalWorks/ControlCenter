from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QSpinBox, QTabWidget

class ControlScreen(QWidget):
    def __init__(self, main_window):
        super(ControlScreen, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/control_screen/control_screen.ui', self)
            print("UI file loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

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
        self.changeFilamentButton = self.findChild(QPushButton, 'changeFilamentButton')
        self.toggleFilamentSensorButton = self.findChild(QPushButton, 'toggleFilamentSensorButton')
        self.setFlowRateButton = self.findChild(QPushButton, 'setFlowRateButton')



        # Find spin boxes
        self.feedRateSpinBox = self.findChild(QSpinBox, 'feedRateSpinBox')
        self.toolTempSpinBox = self.findChild(QSpinBox, 'toolTempSpinBox')
        self.bedTempSpinBox = self.findChild(QSpinBox, 'bedTempSpinBox')
        self.flowRateSpinBox = self.findChild(QSpinBox, 'flowRateSpinBox')

        # Find tab widget
        self.controlTabWidget = self.findChild(QTabWidget, 'controlTabWidget')

        # Check if all elements are found
        if not all([
            self.controlBackButton, self.setFeedRateButton, self.moveZPBabyStep, self.moveZMBabyStep,
            self.cooldownButton, self.fanOnButton, self.fanOffButton, self.feedRateSpinBox,
            self.toolTempSpinBox, self.bedTempSpinBox, self.controlTabWidget
        ]):
            raise ValueError("One or more UI elements not found in the UI file")

        # Connect buttons to their respective functions
        self.controlBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        self.setFeedRateButton.clicked.connect(self.set_feed_rate)
        self.moveZPBabyStep.clicked.connect(self.move_z_positive)
        self.moveZMBabyStep.clicked.connect(self.move_z_negative)
        self.cooldownButton.clicked.connect(self.cooldown)
        self.fanOnButton.clicked.connect(self.turn_fan_on)
        self.fanOffButton.clicked.connect(self.turn_fan_off)

    def set_feed_rate(self):
        """Set the feed rate based on the spin box value."""
        feed_rate = self.feedRateSpinBox.value()
        print(f"Feed rate set to: {feed_rate}%")

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