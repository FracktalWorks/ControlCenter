from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPixmap
from PyQt5.QtCore import Qt

class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.image:
            rect = self.rect()
            scaled_image = self.image.scaled(rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawImage(rect, scaled_image)