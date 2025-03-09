from PyQt5.QtCore import QThread, QTimer, pyqtSlot
import numpy as np
from simple_pid import PID

class ChamberTemperatureController(QThread):
    def __init__(self, heater_board, printer_status):
        super().__init__()
        self.heater_board = heater_board
        self.printer_status = printer_status

        self.printer_status.temperatures_updated.connect(self.control_heater)

        # Timer to run the control_heater method at 30 fps (33 ms interval)
        self.timer = QTimer()
        self.timer.timeout.connect(self.control_heater)
        self.timer.start(33)  # 30 fps

        # Initialize PID controllers for each side
        self.pid_bottom = PID(5, 0.1, 0.05, setpoint=0)
        self.pid_right = PID(5, 0.1, 0.05, setpoint=0)
        self.pid_top = PID(5, 0.1, 0.05, setpoint=0)
        self.pid_left = PID(5, 0.1, 0.05, setpoint=0)

    def run(self):
        """Start the thread and the timer."""
        self.exec_()

    @pyqtSlot()
    def control_heater(self):
        """Control the heater power based on the setpoint and actual temperatures."""
        setpoint = self.printer_status.chamberTemperatureSetpoint
        temps = self.printer_status.chamberTemperatures
        bottom_temp = temps.get('bottom-center', 0)
        right_temp = temps.get('middle-right', 0)
        top_temp = temps.get('top-center', 0)
        left_temp = temps.get('middle-left', 0)

        # Update setpoints for each PID controller
        self.pid_bottom.setpoint = setpoint
        self.pid_right.setpoint = setpoint
        self.pid_top.setpoint = setpoint
        self.pid_left.setpoint = setpoint

        # Compute the control values
        control_bottom = self.pid_bottom(bottom_temp)
        control_right = self.pid_right(right_temp)
        control_top = self.pid_top(top_temp)
        control_left = self.pid_left(left_temp)

        # Clamp the control values between 1 and 99
        control_bottom = max(1, min(99, control_bottom))
        control_right = max(1, min(99, control_right))
        control_top = max(1, min(99, control_top))
        control_left = max(1, min(99, control_left))

        # Apply the control values to the heater board
        self.heater_board.setHeaterPowers(control_bottom, control_bottom , control_right, control_right, control_top, control_top, control_left, control_left)


