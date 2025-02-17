from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

class NetworkSettings(QWidget):
    def __init__(self):
        super(NetworkSettings, self).__init__()
        uic.loadUi('src/ui/ui_files/network_settings.ui', self)


    def save_network_settings(self):
        # Placeholder for save network settings logic
        print("Save Network Settings button clicked")

    def cancel_network_settings(self):
        # Placeholder for cancel network settings logic
        print("Cancel Network Settings button clicked")