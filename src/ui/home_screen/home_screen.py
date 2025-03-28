from PyQt5 import uic
from PyQt5.QtWidgets import (QWidget, QToolButton, QPushButton, QLineEdit, QLabel,
                             QComboBox, QFrame, QProgressBar, QSizePolicy, QVBoxLayout, QFileDialog)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSlot
import numpy as np
import pyqtgraph as pg
from ui.custom_widgets import ImageWidget
from utils.helpers import run_async  # Import the run_async decorator

class HomeScreen(QWidget):
    def __init__(self, main_window):
        super(HomeScreen, self).__init__()
        self.main_window = main_window
        self.is_paused = False  # Add this line to initialize the pause flag

        # Load the UI file
        try:
            uic.loadUi('ui/home_screen/home_screen.ui', self)
            print("HomeScreen UI loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

        # Initialize labels
        self.bedTargetTemperature = self.findChild(QLabel, "bedTargetTemperature")
        self.bedActualTemperature = self.findChild(QLabel, "bedActualTemperature")
        self.chamberTargetTemperature = self.findChild(QLabel, "chamberTargetTemperature")
        self.chamberActualTemperature = self.findChild(QLabel, "chamberActualTemperature")
        self.volumeTargetTemperature = self.findChild(QLabel, "volumeTargetTemperature")
        self.volumeActualTemperature = self.findChild(QLabel, "volumeActualTemperature")
        self.fileInfoLabel = self.findChild(QLabel, "fileInfoLabel")
        self.maxTempLabel = self.findChild(QLabel, "maxTempLabel")  # Find the maxTempLabel

        # Initialize QPushButtons (if any)
        self.stopButton = self.findChild(QPushButton, "stopButton")
        self.playPauseButton = self.findChild(QPushButton, "playPauseButton")
        self.loadFileButton = self.findChild(QPushButton, "loadFileButton")
        self.stopHeatingButton = self.findChild(QPushButton, "stopHeatingButton")
        self.setPIDButton = self.findChild(QPushButton, "setPIDButton")

        # Initialize QLineEdits for PID parameters
        self.p_LineEdit = self.findChild(QLineEdit, "p_LineEdit")
        self.i_LineEdit = self.findChild(QLineEdit, "i_LineEdit")
        self.d_lineEdit = self.findChild(QLineEdit, "d_lineEdit")

        # Initialize QProgressBars
        self.bedTempBar = self.findChild(QProgressBar, "bedTempBar")
        self.printProgressBar = self.findChild(QProgressBar, "printProgressBar")
        self.volumeTempBar = self.findChild(QProgressBar, "volumeTempBar")
        self.chamberTempBar = self.findChild(QProgressBar, "chamberTempBar")

        # Initialize additional widget elements (graph and camera feed areas)
        self.chamberTempGraphWidget = self.findChild(QWidget, "chamberTempGraphWidget")
        self.layerPreviewWidget = self.findChild(QWidget, "layerPreviewWidget")

        # Replace the QWidget with the custom ImageWidget
        thermal_camera_container = self.findChild(QWidget, "thermalCameraWidget")
        self.thermalCameraWidget = ImageWidget(thermal_camera_container)
        layout = QVBoxLayout(thermal_camera_container)
        layout.addWidget(self.thermalCameraWidget)
        self.thermalCameraWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Replace the QWidget with the custom ImageWidget
        rgb_camera_container = self.findChild(QWidget, "rgbCameraWidget")
        self.rgbCameraWidget = ImageWidget(rgb_camera_container)
        layout = QVBoxLayout(rgb_camera_container)
        layout.addWidget(self.rgbCameraWidget)
        self.rgbCameraWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Connect the temperatures_updated signal to the update_thermal_camera_widget slot
        self.main_window.printer_status.temperatures_updated.connect(self.update_thermal_camera_widget)
        self.main_window.printer_status.rgb_frame_updated.connect(self.update_rgb_camera_widget)
        self.main_window.printer_status.maxtemp_updated.connect(self.update_max_temp_label)  # Connect the maxtemp_updated signal

        # Initialize the plot for max temperature
        self.max_temp_plot = pg.PlotWidget()
        self.chamberTempGraphWidget.setLayout(QVBoxLayout())  # Set a layout for chamberTempGraphWidget
        self.chamberTempGraphWidget.layout().addWidget(self.max_temp_plot)
        self.max_temp_curve = self.max_temp_plot.plot(pen='r')
        self.max_temp_data = []

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

    @pyqtSlot(np.ndarray, dict)
    def update_thermal_camera_widget(self, frame, temps):
        if frame is not None:
            image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_BGR888)
            self.thermalCameraWidget.setImage(image)

    @pyqtSlot(np.ndarray)
    def update_rgb_camera_widget(self, frame):
        if frame is not None:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.rgbCameraWidget.setImage(image)

    @pyqtSlot(float)
    def update_max_temp_label(self, max_temp):
        """Slot to update the text of maxTempLabel with the maximum temperature."""
        self.maxTempLabel.setText(f"Max Temp: {max_temp:.2f}°C")
        self.update_max_temp_plot(max_temp)

    def update_max_temp_plot(self, max_temp):
        """Update the max temperature plot with the new value."""
        self.max_temp_data.append(max_temp)
        # Keep only the last 60 entries (assuming 1 entry per second for the last minute)
        if len(self.max_temp_data) > 60:
            self.max_temp_data.pop(0)
        self.max_temp_curve.setData(self.max_temp_data)

    def load_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;EMD Files (*.emd)", options=options)
        if file_path:
            self.main_window.open_scancard_file(file_path)