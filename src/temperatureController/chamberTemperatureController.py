from PyQt5.QtCore import QThread, QTimer, pyqtSlot
import numpy as np

class ChamberTemperatureController(QThread):
    def __init__(self, heater_board, printer_status):
        super().__init__()
        self.heater_board = heater_board
        self.printer_status = printer_status

        # Connect to the temperatures_updated signal
        self.printer_status.temperatures_updated.connect(self.control_heater)

        # Timer to run the control_heater method at 30 fps (33 ms interval)
        self.timer = QTimer()
        self.timer.timeout.connect(self.control_heater)
        self.timer.start(33)  # 30 fps

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
        middle_temp = temps.get('middle-center', 0)

        # Simple watermark algorithm to turn on and off heater between power levels of 1 and 99
        bottom_power = self.calculate_power(bottom_temp, setpoint)
        right_power = self.calculate_power(right_temp, setpoint)
        top_power = self.calculate_power(top_temp, setpoint)
        left_power = self.calculate_power(left_temp, setpoint)

        # Proportionally reduce heating power if middle-center temperature exceeds setpoint by more than 4 degrees
        if middle_temp > setpoint:
            overshoot = middle_temp - setpoint
            reduction_factor = 1 - (overshoot / 10)  # Adjust the divisor to control the reduction rate
            reduction_factor = max(reduction_factor, 0.1)  # Ensure the reduction factor does not go below 0.1

            bottom_power = max(int(bottom_power * reduction_factor), 1)
            right_power = max(int(right_power * reduction_factor), 1)
            top_power = max(int(top_power * reduction_factor), 1)
            left_power = max(int(left_power * reduction_factor), 1)

        # Set heater powers
        self.heater_board.setHeaterPowers(bottom_power, bottom_power / 2, right_power, 1, top_power, top_power / 2, left_power, 1)

    def calculate_power(self, temperature, setpoint):
        """Calculate heater power based on temperature and setpoint."""
        if temperature < setpoint - 2:
            return 99  # Turn on heater at full power
        elif temperature > setpoint + 2:
            return 1  # Turn off heater
        else:
            return int((setpoint + 2 - temperature) * 20)  # Scale power between 1 and 99