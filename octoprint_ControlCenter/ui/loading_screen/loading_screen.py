import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMovie
from utils.helpers import check_ui_elements
from utils.logger import get_logger
import config


logger = get_logger(__name__)

class LoadingScreen(QWidget):
    def __init__(self, main_window):
        super(LoadingScreen, self).__init__()
        self.main_window = main_window
        # Use centralized logger
        self.logger = get_logger(self.__class__.__name__)
        
        try:
            # Use relative path from the current module's directory
            ui_file_path = os.path.join(os.path.dirname(__file__), "loading_screen.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("LoadingScreen UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load LoadingScreen UI file: {e}")

    

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        loading_widgets = {
            "loadingProgressBar": self.loadingProgressBar,
            "loadingStatusLabel": self.loadingStatusLabel,
        }
        
        # Use the helper function to check and report missing widgets
        check_ui_elements(self, loading_widgets, "LoadingScreen")

    def stop_movie_and_switch(self):
        if hasattr(self, 'movie') and self.movie is not None:
            self.movie.stop()
        self.timer.stop()
        self.logger.info("Switching from loading screen to home screen")
        self.main_window.switch_screen(self.main_window.home_screen)