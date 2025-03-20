from PyQt5 import uic
from PyQt5.QtWidgets import (QWidget, QPushButton, QSpinBox, QProgressBar, QSizePolicy, QVBoxLayout, QMessageBox, QLabel)
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QTimer
from PyQt5.QtGui import QImage
import numpy as np
from ui.custom_widgets import ImageWidget
from utils.helpers import run_async
import time
from processAutomationController.processAutomationController import ProcessAutomationController

def g_codes(self):    

        self.btn_y_plus = QPushButton("Move Y+")
        self.btn_y_plus.clicked.connect(lambda: send_command("N10 G01 Y10 F500", self.output_display))
        grid.addWidget(self.btn_y_plus, 0, 1)
        
        self.btn_x_minus = QPushButton("Move X-")
        self.btn_x_minus.clicked.connect(lambda: send_command("N20 G01 X-10 F500", self.output_display))
        grid.addWidget(self.btn_x_minus, 1, 0)
        
        self.btn_home = QPushButton("Home XYZ")
        self.btn_home.clicked.connect(lambda: send_command("N70 G01 X0 Y0 Z0 F200", self.output_display))
        grid.addWidget(self.btn_home, 1, 1)
        
        self.btn_x_plus = QPushButton("Move X+")
        self.btn_x_plus.clicked.connect(lambda: send_command("N30 G01 X10 F500", self.output_display))
        grid.addWidget(self.btn_x_plus, 1, 2)
        
        self.btn_y_minus = QPushButton("Move Y-")
        self.btn_y_minus.clicked.connect(lambda: send_command("N40 G01 Y-10 F500", self.output_display))
        
 
        
        # Z-Axis Buttons
        self.btn_z_up = QPushButton("Move Z Up")
        self.btn_z_up.clicked.connect(lambda: send_command("N50 G01 Z10 F500", self.output_display))
        
        self.btn_z_down = QPushButton("Move Z Down")
        self.btn_z_down.clicked.connect(lambda: send_command("N60 G01 Z-10 F500", self.output_display))
        
        
        self.btn_z_home = QPushButton("Z Home")
        self.btn_z_down.clicked.connect(lambda: send_command("N60 G01 Z0 F500", self.output_display))
       