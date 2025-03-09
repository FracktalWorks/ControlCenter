import serial
import time

class SerialProtocol:
    def __init__(self, port="COM19", baudrate=115200, timeout=1):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2)  # Wait for the board to initialize
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            self.ser = None

    def send_command(self, command):
        if not self.ser:
            print("Serial port is not initialized.")
            return
        
        try:
            # Ensure command starts with '$'
            if not command.startswith('$'):
                command = '$' + command

            # Append '\r\n' automatically
            command += '\r\n'

            # Send command
            self.ser.write(command.encode())
            self.ser.flush()  # Ensure data is sent
            time.sleep(0.1)  # Small delay to ensure board receives it
            print(f"Sent: {command.strip()}")

            # Read response
            response = self.ser.readline().decode().strip()
            print(f"Received: {response}")

        except Exception as e:
            print(f"Error: {e}")

    def close(self):
        if self.ser:
            self.ser.close()

class HeaterController:
    def __init__(self, port="COM19"):
        self.serial_model = SerialProtocol(port="COM19", baudrate=115200, timeout=1)

    def setHeaterPowers(self,ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8):
        command = f"8,{ch1},{ch2},{ch3},{ch4},{ch5},{ch6},{ch7},{ch8}"
        self.serial_model.send_command(command)

    def stopHeaters(self):
        command = "8,1,1,1,1,1,1,1,1"
        self.serial_model.send_command(command)
        print("Heater stopped")

    def enableWatchdog(self, event):
        command = f"E"
        self.serial_model.send_command(command)

    def enableWatchdog(self, event):
        command = f"D"
        self.serial_model.send_command(command)