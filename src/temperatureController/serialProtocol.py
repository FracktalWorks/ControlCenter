import serial
import time
from concurrent.futures import ThreadPoolExecutor

class SerialProtocol:
    def __init__(self, port="COM19", baudrate=115200, timeout=1):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2)  # Wait for the board to initialize
            self.executor = ThreadPoolExecutor(max_workers=1)  # Initialize a thread pool executor
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

            # Read response
            response = self.ser.readline().decode().strip()

        except Exception as e:
            print(f"Error: {e}")

    def send_command_async(self, command):
        """Send command asynchronously."""
        self.executor.submit(self.send_command, command)

    def close(self):
        if self.ser:
            self.ser.close()
        self.executor.shutdown(wait=False)  # Shutdown the executor