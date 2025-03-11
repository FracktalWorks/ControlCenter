# https://github.com/alchemyEngine/MoonrakerPy/blob/main/moonrakerpy for all functions

from moonrakerpy import MoonrakerPrinter
import time

class MoonrakerAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.client = MoonrakerPrinter(base_url)

    def reconnect(self):
        """
        Attempt to reconnect to the Moonraker server.
        """
        try:
            self.client = MoonrakerPrinter(self.base_url)
            print("Reconnected to Moonraker server.")
        except Exception as e:
            print(f"Failed to reconnect: {e}")


    def send_gcode(self, cmd):
        try:
            return self.client.send_gcode(cmd)
        except Exception as e:
            print(f"Error sending G-code: {e}")
            self.reconnect()
            return str(e)
    
    def query_status(self):
        try:
            return self.client.query_status()
        except Exception as e:
            print(f"Error querying status: {e}")
            self.reconnect()
            return str(e)

    def query_temperatures(self):
        try:
            return self.client.query_temperatures()
        except Exception as e:
            print(f"Error querying temperatures: {e}")
            self.reconnect()
            return str(e)

