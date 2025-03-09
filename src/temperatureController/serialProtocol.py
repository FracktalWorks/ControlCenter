import serial
import time

def run_async(func):
    """
    Function decorater to make methods run in a thread
    """
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func

class SerialProtocol:
    def __init__(self, port="COM19", baudrate=115200, timeout=1):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2)  # Wait for the board to initialize
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            self.ser = None
            
    @run_async        
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

            # Read response
            response = self.ser.readline().decode().strip()

        except Exception as e:
            print(f"Error: {e}")

    def close(self):
        if self.ser:
            self.ser.close()