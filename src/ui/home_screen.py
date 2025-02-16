from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

class HomeScreen(QWidget):
    def __init__(self):
        super(HomeScreen, self).__init__()
        uic.loadUi('src/ui/ui_files/home_screen.ui', self)

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
        # Placeholder for open menu logic
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