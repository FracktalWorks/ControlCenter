from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton
from utils.helpers import check_ui_elements

class HomeScreen(QWidget):
    def __init__(self, main_window):
        super(HomeScreen, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/home_screen/home_screen.ui', self)
            print("HomeScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load HomeScreen UI file: {e}")

        # Find buttons by their object names
        self.doorLockButton = self.findChild(QToolButton, 'doorLockButton')
        self.menuButton = self.findChild(QPushButton, 'menuButton')
        self.stopButton = self.findChild(QPushButton, 'stopButton')
        self.playPauseButton = self.findChild(QPushButton, 'playPauseButton')
        self.controlButton = self.findChild(QPushButton, 'controlButton')

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions - with safety checks
        self._connect_buttons()

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Group widgets for better reporting
        home_screen_buttons = {
            "doorLockButton": self.doorLockButton,
            "menuButton": self.menuButton,
            "stopButton": self.stopButton,
            "playPauseButton": self.playPauseButton,
            "controlButton": self.controlButton
        }
        
        # Use the helper function to check and report missing widgets
        check_ui_elements(self, home_screen_buttons, "HomeScreen")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        if self.doorLockButton:
            self.doorLockButton.clicked.connect(self.toggle_door_lock)
        
        if self.menuButton:
            self.menuButton.clicked.connect(self.open_menu)
        
        if self.stopButton:
            self.stopButton.clicked.connect(self.stop_print)
        
        if self.playPauseButton:
            self.playPauseButton.clicked.connect(self.play_pause_print)
        
        if self.controlButton:
            self.controlButton.clicked.connect(self.open_control_panel)

    def toggle_door_lock(self):
        # Placeholder for toggle door lock logic
        print("Toggle Door Lock button clicked")
        # This functionality will be connected to OctoPrint API later

    def open_menu(self):
        # Logic to open the menu screen
        self.main_window.switch_to_menu_screen()
        print("Menu button clicked")

    def stop_print(self):
        # Placeholder for stop print logic
        print("Stop Print button clicked")
        # This functionality will be connected to OctoPrint API later

    def play_pause_print(self):
        # Placeholder for play/pause print logic
        print("Play/Pause button clicked")
        # This functionality will be connected to OctoPrint API later

    def open_control_panel(self):
        # Logic to open the control panel screen
        self.main_window.switch_to_control_screen()
        print("Control Panel button clicked")