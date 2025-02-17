from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMovie

class LoadingScreen(QWidget):
    def __init__(self, main_window):
        super(LoadingScreen, self).__init__()
        self.main_window = main_window
        uic.loadUi('src/ui/ui_files/loading_screen.ui', self)

        # Set up the loading GIF
        self.loadingGif = self.findChild(QLabel, 'loadingGif')
        self.movie = QMovie(":/Misc/img/loading_animation.gif")
        self.loadingGif.setMovie(self.movie)
        self.movie.start()

        # Set up the timer to switch to the home screen after 20 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.stop_movie_and_switch)
        self.timer.start(20000)  # 20000 milliseconds = 20 seconds

    def stop_movie_and_switch(self):
        self.movie.stop()
        self.main_window.switch_screen(self.main_window.home_screen)