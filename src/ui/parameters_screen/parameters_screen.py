from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QLineEdit

class ParametersScreen(QWidget):
    def __init__(self, main_window):
        super(ParametersScreen, self).__init__()
        self.main_window = main_window

        try:
            uic.loadUi('src/ui/parameters_screen/parameters_screen.ui', self)
            print("ParametersScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ParametersScreen UI: {e}")

        # Initialize all QLineEdit widgets
        self.layerHeightLineEdit = self.findChild(QLineEdit, "layerHeightLineEdit")
        self.initialLevellingHeightLineEdit = self.findChild(QLineEdit, "initialLevellingHeightLineEdit")
        self.heatedBufferHeightLineEdit = self.findChild(QLineEdit, "heatedBufferHeightLineEdit")
        self.powderLoadingExtraHeightGapLineEdit = self.findChild(QLineEdit, "powderLoadingExtraHeightGapLineEdit")
        self.bedTemperatureLineEdit = self.findChild(QLineEdit, "bedTemperatureLineEdit")
        self.volumeTemberatureLineEdit = self.findChild(QLineEdit, "volumeTemberatureLineEdit")
        self.chamberTemperatureLineEdit = self.findChild(QLineEdit, "chamberTemperatureLineEdit")
        self.pLineEdit = self.findChild(QLineEdit, "pLineEdit")
        self.iLineEdit = self.findChild(QLineEdit, "iLineEdit")
        self.dLineEdit = self.findChild(QLineEdit, "dLineEdit")

        # Additional initialization code here, if needed