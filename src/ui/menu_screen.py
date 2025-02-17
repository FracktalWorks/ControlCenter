from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

class MenuScreen(QWidget):
    def __init__(self):
        super(MenuScreen, self).__init__()
        uic.loadUi('src/ui/ui_files/menu_screen.ui', self)

    def open_settings(self):
        # Placeholder for open settings logic
        print("Settings button clicked")

    def open_network_settings(self):
        # Placeholder for open network settings logic
        print("Network Settings button clicked")