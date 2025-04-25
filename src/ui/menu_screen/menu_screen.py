from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton
from utils.helpers import check_ui_elements

class MenuScreen(QWidget):
    def __init__(self, main_window):
        super(MenuScreen, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/menu_screen/menu_screen.ui', self)
            print("MenuScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load MenuScreen UI file: {e}")

        # Find buttons by their object names
        self.menuPrintButton = self.findChild(QToolButton, 'menuPrintButton')
        self.menuControlButton = self.findChild(QToolButton, 'menuControlButton')
        self.menuCalibrateButton = self.findChild(QToolButton, 'menuCalibrateButton')
        self.menuCartButton = self.findChild(QToolButton, 'menuCartButton')
        self.menuSettingsButton = self.findChild(QToolButton, 'menuSettingsButton')
        self.menuBackButton = self.findChild(QPushButton, 'menuBackButton')

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions - with safety checks
        self._connect_buttons()

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Group widgets for better reporting
        menu_screen_buttons = {
            "menuPrintButton": self.menuPrintButton,
            "menuControlButton": self.menuControlButton,
            "menuCalibrateButton": self.menuCalibrateButton,
            "menuCartButton": self.menuCartButton,
            "menuSettingsButton": self.menuSettingsButton,
            "menuBackButton": self.menuBackButton
        }
        
        # Use the helper function to check and report missing widgets
        check_ui_elements(self, menu_screen_buttons, "MenuScreen")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        if self.menuPrintButton:
            self.menuPrintButton.clicked.connect(self.open_print)
        
        if self.menuControlButton:
            self.menuControlButton.clicked.connect(self.open_control)
        
        if self.menuCalibrateButton:
            self.menuCalibrateButton.clicked.connect(self.open_calibrate)
        
        if self.menuCartButton:
            self.menuCartButton.clicked.connect(self.open_cart)
        
        if self.menuSettingsButton:
            self.menuSettingsButton.clicked.connect(self.open_settings)
        
        if self.menuBackButton:
            self.menuBackButton.clicked.connect(self.go_back)

    def open_print(self):
        # Navigate to the print location screen
        self.main_window.switch_to_print_location_screen()
        print("Print button clicked")

    def open_control(self):
        # Navigate to the control screen
        self.main_window.switch_to_control_screen()
        print("Control button clicked")

    def open_calibrate(self):
        # Navigate to the calibrate screen
        self.main_window.switch_to_calibrate_screen()
        print("Calibrate button clicked")

    def open_cart(self):
        # Placeholder for open cart logic
        print("Cart button clicked")
        # This function may not have an implementation yet

    def open_settings(self):
        # Navigate to the settings screen
        self.main_window.switch_to_settings_screen()
        print("Settings button clicked")

    def go_back(self):
        # Go back to the previous screen
        self.main_window.switch_to_home_screen()
        print("Back button clicked")