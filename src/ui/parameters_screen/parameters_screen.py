from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

class ParametersScreen(QWidget):
    def __init__(self, main_window):
        super(ParametersScreen, self).__init__()
        self.main_window = main_window

        try:
            uic.loadUi('src/ui/parameters_screen/parameters_screen.ui', self)
            print("ParametersScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ParametersScreen UI: {e}")
        
        # Additional initialization code here, if needed