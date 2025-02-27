from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton

class HomeScreen(QWidget):
    def __init__(self, main_window):
        super(HomeScreen, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/home_screen/home_screen.ui', self)
            print("UI file loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

        # Find buttons by their object names
        self.doorLockButton = self.findChild(QToolButton, 'doorLockButton')
        self.menuButton = self.findChild(QPushButton, 'menuButton')
        self.stopButton = self.findChild(QPushButton, 'stopButton')
        self.playPauseButton = self.findChild(QPushButton, 'playPauseButton')
        self.controlButton = self.findChild(QPushButton, 'controlButton')

        # Debug prints to check if buttons are found
        # print(f"doorLockButton: {self.doorLockButton}")
        # print(f"menuButton: {self.menuButton}")
        # print(f"stopButton: {self.stopButton}")
        # print(f"playPauseButton: {self.playPauseButton}")
        # print(f"controlButton: {self.controlButton}")

        # Check if buttons are found
        if not all([self.doorLockButton, self.menuButton, self.stopButton, self.playPauseButton, self.controlButton]):
            raise ValueError("One or more buttons not found in the UI file")

        # Connect buttons to their respective functions
        self.doorLockButton.clicked.connect(self.toggle_door_lock)
        self.menuButton.clicked.connect(self.open_menu)
        self.stopButton.clicked.connect(self.stop_print)
        self.playPauseButton.clicked.connect(self.play_pause_print)
        self.controlButton.clicked.connect(self.open_control_panel)

    def toggle_door_lock(self):
        # Placeholder for toggle door lock logic
        print("Toggle Door Lock button clicked")

    def open_menu(self):
        # Logic to open the menu screen
        self.main_window.switch_screen(self.main_window.menu_screen)
        print("Menu button clicked")

    def stop_print(self):
        # Placeholder for stop print logic
        print("Stop Print button clicked")

    def play_pause_print(self):
        # Placeholder for play/pause print logic
        print("Play/Pause button clicked")

    def open_control_panel(self):
        # Placeholder for open control panel logic
        print("Control Panel button clicked")