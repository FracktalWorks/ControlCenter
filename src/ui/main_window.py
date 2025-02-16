from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QPushButton
from ui.home_screen import HomeScreen
from ui.loading_screen import LoadingScreen
import ui.ui_files.resources.resource_rc  # Ensure resources are loaded

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        #self.setWindowTitle("3D Printer Control Center")
        #self.setGeometry(0, 0, 800, 480)  # Adjust the size as needed for your touchscreen

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # Load sub UIs based on configuration
        self.load_home_screen()
        self.load_loading_screen()
        self.switch_screen(self.loading_screen)

        # Adjust the size of the main window to fit its contents
        self.adjustSize()

    def load_home_screen(self):
        self.home_screen = HomeScreen()
        self.stacked_widget.addWidget(self.home_screen)

    def load_loading_screen(self):
        self.loading_screen = LoadingScreen(self.switch_to_home_screen)
        self.stacked_widget.addWidget(self.loading_screen)

    def switch_screen(self, widget):
        self.stacked_widget.setCurrentWidget(widget)
        self.adjustSize()  # Adjust size after switching screens

    def switch_to_home_screen(self):
        self.switch_screen(self.home_screen)
