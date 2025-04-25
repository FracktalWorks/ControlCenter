from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton

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
        self.backButton = self.findChild(QPushButton, 'backButton')

        # Connect buttons to their respective actions
        self.backButton.clicked.connect(self.main_window.switch_to_previous_screen)