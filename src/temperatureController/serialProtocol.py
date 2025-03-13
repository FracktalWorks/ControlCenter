import serial
import time
from concurrent.futures import ThreadPoolExecutor, Future
from PyQt5.QtCore import QTimer, QMutex

class SerialProtocol:
    def __init__(self, port="COM19", baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.executor = ThreadPoolExecutor(max_workers=1)  # Initialize a thread pool executor
        self.connect()

        # Set up a timer to periodically check the connection
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_connection)
        self.timer.start(5000)  # Check every 5 seconds

        # Mutex to ensure only one command is sent at a time
        self.mutex = QMutex()

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # Wait for the board to initialize
            print(f"Connected to {self.port}")
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            self.ser = None

    def check_connection(self):
        if self.ser is None or not self.ser.is_open:
            print("Serial connection lost. Attempting to reconnect...")
            self.connect()

    def flush_buffers(self):
        """Flush the input and output buffers of the serial connection."""
        if self.ser:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            print("Serial buffers flushed.")

    def send_command(self, command):
        if not self.ser:
            print("Serial port is not initialized.")
            return
        
        self.mutex.lock()  # Lock the mutex to ensure only one command is sent at a time
        try:
            # Ensure command starts with '$'
            if not command.startswith('$'):
                command = '$' + command

            # Append '\r\n' automatically
            command += '\r\n'

            # Send command
            self.ser.write(command.encode())
            self.ser.flush()  # Ensure data is sent
            time.sleep(0.1)  # Wait for the response

            # Read response
            response = self.ser.readline().decode().strip()
            # print(f"Response: {response}")
            return response

        except Exception as e:
            print(f"Error: {e}")
            self.flush_buffers()  # Flush the buffers if an error occurs
        finally:
            self.mutex.unlock()  # Unlock the mutex

    def send_command_async(self, command) -> Future:
        """Send command asynchronously and return a Future object."""
        return self.executor.submit(self.send_command, command)

    def close(self):
        if self.ser:
            self.ser.close()
        self.executor.shutdown(wait=False)  # Shutdown the executor
        self.timer.stop()  # Stop the timer