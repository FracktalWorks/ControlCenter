from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

class ControlScreen(QWidget):
    def __init__(self, main_window, moonraker_api=None):
        super(ControlScreen, self).__init__(main_window)
        self.main_window = main_window
        self.moonraker_api = moonraker_api

        # Load the control screen UI
        try:
            uic.loadUi('src/ui/control_screen/control_screen.ui', self)
            print("ControlScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ControlScreen UI: {e}")

        # Setup any signal-slot connections and additional initialization here