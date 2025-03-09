import serial
import time
from queue import Queue, Empty
from threading import Thread

class SerialProtocol:
    def __init__(self, port="COM19", baudrate=115200, timeout=1):
        self.command_queue = Queue()
        self.response_queue = Queue()
        self.running = True

        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2)  # Wait for the board to initialize
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            self.ser = None

        # Start the communication thread
        self.thread = Thread(target=self._process_commands)
        self.thread.start()

    def _process_commands(self):
        while self.running:
            try:
                command = self.command_queue.get(timeout=1)
                if command is None:
                    break

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
                self.response_queue.put(response)

            except Empty:
                continue
            except Exception as e:
                print(f"Error: {e}")

    def send_command(self, command):
        if not self.ser:
            print("Serial port is not initialized.")
            return

        self.command_queue.put(command)

    def close(self):
        self.running = False
        self.command_queue.put(None)
        self.thread.join()
        if self.ser:
            self.ser.close()