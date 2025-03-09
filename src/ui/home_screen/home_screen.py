from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton

class HomeScreen(QWidget):
    def __init__(self, main_window, moonraker_api=None):
        super(HomeScreen, self).__init__()
        self.main_window = main_window
        self.moonraker_api = moonraker_api

        # Load the .ui file
        try:
            uic.loadUi('src/ui/home_screen/home_screen.ui', self)
            print("UI file loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

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