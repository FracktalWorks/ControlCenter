from PyQt5.QtCore import QThread, pyqtSlot
import numpy as np
from simple_pid import PID
from .heaterBoard import HeaterBoard

class ChamberTemperatureController(QThread):
    def __init__(self, printer_status):
        super().__init__()
        self.heater_board = HeaterBoard()
        self.printer_status = printer_status

        # Connect the temperatures_updated signal to the control_heater slot
        self.printer_status.temperatures_updated.connect(self.control_heater)

        # Initialize PID controllers for each side
        self.pid_bottom = PID(15, 0.0001, 0.1, setpoint=0)
        self.pid_right = PID(15, 0.0001, 0.1, setpoint=0)
        self.pid_top = PID(15, 0.0001, 0.1, setpoint=0)
        self.pid_left = PID(15, 0.0001, 0.1, setpoint=0)
        self.pid_middle_center = PID(15, 0.0001, 0.1, setpoint=0)  # New PID for middle-center

    @pyqtSlot(np.ndarray, dict)
    def control_heater(self, frame, chamberTemperatures):
        """Control the heater power based on the setpoint and actual temperatures."""
        setpoint = self.printer_status.chamberTemperatureSetpoint
        temps = chamberTemperatures
        bottom_temp = temps.get('bottom-center', 0)
        right_temp = temps.get('middle-right', 0)
        top_temp = temps.get('top-center', 0)
        left_temp = temps.get('middle-left', 0)
        middle_center_temp = temps.get('middle-center', 0)

        # Update setpoints for each PID controller
        self.pid_bottom.setpoint = setpoint
        self.pid_right.setpoint = setpoint
        self.pid_top.setpoint = setpoint
        self.pid_left.setpoint = setpoint
        self.pid_middle_center.setpoint = setpoint  # Update setpoint for middle-center PID

        # Compute the control values
        control_bottom = self.pid_bottom(bottom_temp)
        control_right = self.pid_right(right_temp)
        control_top = self.pid_top(top_temp)
        control_left = self.pid_left(left_temp)
        control_middle_center = self.pid_middle_center(middle_center_temp)  # Compute control for middle-center

        # If middle-center temperature goes beyond the setpoint, reduce the output of other PIDs
        if middle_center_temp > setpoint:
            reduction_factor = max(0, 1 - control_middle_center / 100)
            control_bottom *= reduction_factor
            control_right *= reduction_factor
            control_top *= reduction_factor
            control_left *= reduction_factor

        # Clamp the control values between 1 and 99
        control_bottom = max(1, min(99, control_bottom))
        control_right = max(1, min(99, control_right))
        control_top = max(1, min(99, control_top))
        control_left = max(1, min(99, control_left))

        # Apply the control values to the heater board
        self.heater_board.setHeaterPowers(control_bottom, control_bottom, control_right, control_right / 2, control_top, control_top, control_left, control_left / 2)