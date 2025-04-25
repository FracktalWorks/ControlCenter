from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMovie
from utils.helpers import check_ui_elements

class LoadingScreen(QWidget):
    def __init__(self, main_window):
        super(LoadingScreen, self).__init__()
        self.main_window = main_window
        
        try:
            uic.loadUi('src/ui/loading_screen/loading_screen.ui', self)
            print("LoadingScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load LoadingScreen UI file: {e}")

        # Find UI elements
        self.loadingGif = self.findChild(QLabel, 'loadingGif')
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Only proceed with animation if loadingGif is found
        if self.loadingGif:
            try:
                self.movie = QMovie(":/Misc/img/loading_animation.gif")
                self.loadingGif.setMovie(self.movie)
                self.movie.start()
            except Exception as e:
                print(f"Failed to load or start loading animation: {e}")

        # Set up the timer to switch to the home screen
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.stop_movie_and_switch)
        self.timer.start(1000)  # 1000 milliseconds = 1 second

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        loading_widgets = {
            "loadingGif": self.loadingGif
        }
        
        # Use the helper function to check and report missing widgets
        check_ui_elements(self, loading_widgets, "LoadingScreen")

    def stop_movie_and_switch(self):
        if hasattr(self, 'movie') and self.movie is not None:
            self.movie.stop()
        self.timer.stop()
        self.main_window.switch_screen(self.main_window.home_screen)