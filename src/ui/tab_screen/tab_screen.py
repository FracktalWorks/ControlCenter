from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from ui.home_screen.home_screen import HomeScreen
from ui.control_screen.control_screen import ControlScreen


class TabScreen(QWidget):
    def __init__(self, main_window, moonraker_api=None):
        super(TabScreen, self).__init__()
        self.main_window = main_window
        self.moonraker_api = moonraker_api

        # Load the .ui file for tab screen
        try:
            uic.loadUi('src/ui/tab_screen/tab_screen.ui', self)
            print("TabScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load TabScreen UI: {e}")

        # Find the QTabWidget
        self.tabWidget = self.findChild(QTabWidget, 'tabWidget')

        # Populate the tabs using the existing containers in the UI file
        self.load_home_tab()
        self.load_control_tab()

    def load_home_tab(self):
        # Find the existing home tab
        home_tab = self.findChild(QWidget, 'home_tab')
        if home_tab:
            self.home_screen = HomeScreen(self, self.moonraker_api)
            layout = QVBoxLayout(home_tab)
            layout.addWidget(self.home_screen)
            home_tab.setLayout(layout)
        else:
            print("Home tab not found in TabScreen UI")

    def load_control_tab(self):
        # Find the existing control tab by its object name as set in Qt Designer (e.g., "controlTab")
        control_tab = self.findChild(QWidget, 'control_tab')
        if control_tab:
            # Import ControlScreen only when needed
            self.control_screen = ControlScreen(self, self.moonraker_api)
            layout = QVBoxLayout(control_tab)
            layout.addWidget(self.control_screen)
            control_tab.setLayout(layout)
        else:
            print("Control tab not found in TabScreen UI")