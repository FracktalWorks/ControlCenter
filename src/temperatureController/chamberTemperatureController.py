from PyQt5.QtCore import QThread, QTimer, pyqtSlot
import numpy as np

class ChamberTemperatureController(QThread):
    def __init__(self, heater_board, printer_status):
        super().__init__()
        self.heater_board = heater_board
        self.printer_status = printer_status

        # Timer to run the control_heater method at 30 fps (33 ms interval)
        self.timer = QTimer()
        self.timer.timeout.connect(self.control_heater)

    def run(self):
        """Start the thread and the timer."""
        self.timer.start(33)  # 30 fps
        self.exec_()

    @pyqtSlot()
    def control_heater(self):
        """Control the heater power based on the setpoint and actual temperatures."""
        setpoint = self.printer_status.chamberTemperatureSetpoint
        temps = self.printer_status.chamberTemperatures
        bottom_temp = temps.get('Bottom', 0)
        right_temp = temps.get('Right', 0)
        top_temp = temps.get('Top', 0)
        left_temp = temps.get('Left', 0)

        # Simple watermark algorithm to turn on and off heater between power levels of 1 and 99
        bottom_power = self.calculate_power(bottom_temp, setpoint)
        right_power = self.calculate_power(right_temp, setpoint)
        top_power = self.calculate_power(top_temp, setpoint)
        left_power = self.calculate_power(left_temp, setpoint)

        # Set heater powers
        self.heater_board.setHeaterPowers(bottom_power, bottom_power, right_power, right_power, top_power, top_power, left_power, left_power)

    def calculate_power(self, temperature, setpoint):
        """Calculate heater power based on temperature and setpoint."""
        if temperature < setpoint - 2:
            return 99  # Turn on heater at full power
        elif temperature > setpoint + 2:
            return 1  # Turn off heater
        else:
            return int((setpoint + 2 - temperature) * 20)  # Scale power between 1 and 99