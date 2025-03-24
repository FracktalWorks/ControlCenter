from PyQt5 import uic
from PyQt5.QtWidgets import (QWidget, QToolButton, QPushButton, QLineEdit, QLabel,
                             QComboBox, QFrame, QProgressBar, QSizePolicy, QVBoxLayout, QFileDialog)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSlot
import numpy as np
import pyqtgraph as pg
from ui.custom_widgets import ImageWidget
from utils.helpers import run_async  # Import the run_async decorator
import processAutomationController  # Import the ProcessAutomationController module

class HomeScreen(QWidget):
    def __init__(self, main_window):
        super(HomeScreen, self).__init__()
        self.main_window = main_window
        self.is_paused = False  # Add this line to initialize the pause flag

        # Load the UI file
        try:
            uic.loadUi('src/ui/home_screen/home_screen.ui', self)
            print("HomeScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

        # Initialize labels

        self.fileInfoLabel = self.findChild(QLabel, "fileInfoLabel")

        # Initialize QPushButtons (if any)
        self.stopButton = self.findChild(QPushButton, "stopButton")
        self.playPauseButton = self.findChild(QPushButton, "playPauseButton")
        self.loadFileButton = self.findChild(QPushButton, "loadFileButton")


        # Initialize QProgressBars
        self.printProgressBar = self.findChild(QProgressBar, "printProgressBar")


        # Replace the QWidget with the custom ImageWidget
        thermal_camera_container = self.findChild(QWidget, "layerPreviewWidget")
        self.thermalCameraWidget = ImageWidget(thermal_camera_container)
        layout = QVBoxLayout(thermal_camera_container)
        layout.addWidget(self.thermalCameraWidget)
        self.thermalCameraWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Replace the QWidget with the custom ImageWidget
        rgb_camera_container = self.findChild(QWidget, "subLayerPreviewWidget")
        self.rgbCameraWidget = ImageWidget(rgb_camera_container)
        layout = QVBoxLayout(rgb_camera_container)
        layout.addWidget(self.rgbCameraWidget)
        self.rgbCameraWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)



        # Connect buttons to their respective slots
        self.playPauseButton.clicked.connect(self.toggle_printing)
        self.stopButton.clicked.connect(self.stop_printing)
        self.loadFileButton.clicked.connect(self.load_file)  # Connect the loadFileButton to the load_file method

    @run_async  # Apply the run_async decorator
    def start_printing_sequence(self):
        self.main_window.process_automation_controller.start_printing_sequence()

    def toggle_printing(self):
        if self.playPauseButton.isChecked():
            if self.is_paused:
                self.is_paused = False
            else:
                self.main_window.process_automation_controller.process_running = True
                self.start_printing_sequence()  # Call the decorated method
        else:
            self.is_paused = True  # Set the pause flag

    def stop_printing(self):
        self.main_window.process_automation_controller.stop_process()


    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open G-code File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            processAutomationController.send_gcode_file(file_path, self.output_display)