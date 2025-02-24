from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton

class MenuScreen(QWidget):
    def __init__(self, main_window):
        super(MenuScreen, self).__init__()
        self.main_window = main_window
        uic.loadUi('src/ui/menu_screen/menu_screen.ui', self)

        # Find buttons by their object names
        self.menuPrintButton = self.findChild(QToolButton, 'menuPrintButton')
        self.menuControlButton = self.findChild(QToolButton, 'menuControlButton')
        self.menuCalibrateButton = self.findChild(QToolButton, 'menuCalibrateButton')
        self.menuCartButton = self.findChild(QToolButton, 'menuCartButton')
        self.menuSettingsButton = self.findChild(QToolButton, 'menuSettingsButton')
        self.menuBackButton = self.findChild(QPushButton, 'menuBackButton')

        # Debug prints to check if buttons are found
        print(f"menuPrintButton: {self.menuPrintButton}")
        print(f"menuControlButton: {self.menuControlButton}")
        print(f"menuCalibrateButton: {self.menuCalibrateButton}")
        print(f"menuCartButton: {self.menuCartButton}")
        print(f"menuSettingsButton: {self.menuSettingsButton}")
        print(f"menuBackButton: {self.menuBackButton}")

        # Check if buttons are found
        if not all([self.menuPrintButton, self.menuControlButton, self.menuCalibrateButton, self.menuCartButton, self.menuSettingsButton, self.menuBackButton]):
            raise ValueError("One or more buttons not found in the UI file")

        # Connect buttons to their respective functions
        self.menuPrintButton.clicked.connect(self.open_print)
        self.menuControlButton.clicked.connect(self.open_control)
        self.menuCalibrateButton.clicked.connect(self.open_calibrate)
        self.menuCartButton.clicked.connect(self.open_cart)
        self.menuSettingsButton.clicked.connect(self.open_settings)
        self.menuBackButton.clicked.connect(self.go_back)

    def open_print(self):
        # Placeholder for open print logic
        print("Print button clicked")

    def open_control(self):
        # Placeholder for open control logic
        print("Control button clicked")

    def open_calibrate(self):
        # Placeholder for open calibrate logic
        print("Calibrate button clicked")

    def open_cart(self):
        # Placeholder for open cart logic
        print("Cart button clicked")

    def open_settings(self):
        # Logic to open the settings screen
        self.main_window.switch_screen(self.main_window.settings_screen)
        print("Settings button clicked")

    def go_back(self):
        # Placeholder for go back logic
        print("Back button clicked")