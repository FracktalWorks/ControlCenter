from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

class SettingsScreen(QWidget):
    def __init__(self):
        super(SettingsScreen, self).__init__()
        uic.loadUi('src/ui/ui_files/settings_screen.ui', self)

    def save_settings(self):
        # Placeholder for save settings logic
        print("Save Settings button clicked")

    def cancel_settings(self):
        # Placeholder for cancel settings logic
        print("Cancel Settings button clicked")