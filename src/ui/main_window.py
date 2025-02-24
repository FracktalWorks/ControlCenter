from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from ui.home_screen.home_screen import HomeScreen
from ui.loading_screen.loading_screen import LoadingScreen
from ui.menu_screen.menu_screen import MenuScreen
from ui.settings_screen.settings_screen import SettingsScreen
import ui.resources.resource_rc  # Ensure resources are loaded
import traceback

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # Load sub UIs based on configuration
        self.load_home_screen()
        self.load_loading_screen()
        self.load_menu_screen()
        self.load_settings_screen()
        self.switch_screen(self.loading_screen)

        # Adjust the size of the main window to fit its contents
        self.adjustSize()

    def load_home_screen(self):
        self.home_screen = HomeScreen(self)
        self.stacked_widget.addWidget(self.home_screen)

    def load_loading_screen(self):
        self.loading_screen = LoadingScreen(self)
        self.stacked_widget.addWidget(self.loading_screen)
    
    def load_menu_screen(self):
        self.menu_screen = MenuScreen(self)
        self.stacked_widget.addWidget(self.menu_screen)

    def load_settings_screen(self):
        self.settings_screen = SettingsScreen(self)
        self.stacked_widget.addWidget(self.settings_screen)

    def switch_screen(self, widget):
        print(f"Switching to screen: {widget}")
        traceback.print_stack()  # Print the call stack
        self.stacked_widget.setCurrentWidget(widget)
#        self.adjustSize()  # Adjust size after switching screens

    def switch_to_home_screen(self):
        self.switch_screen(self.home_screen)

    def switch_to_network_settings(self):
        self.switch_screen(self.network_settings)

