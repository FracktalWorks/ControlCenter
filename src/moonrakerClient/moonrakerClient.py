# https://github.com/alchemyEngine/MoonrakerPy/blob/main/moonrakerpy/moonrakerpy.py for all functions

from moonrakerpy import MoonrakerClient

class MoonrakerAPI:
    def __init__(self, base_url):
        self.client = MoonrakerClient(base_url)


    def send_gcode(self, cmd):
        return self.client.send_gcode(cmd)
    
    def query_status(self):
        return self.client.query_status()
    
    def query_temperatures(self):
        return self.client.query_temperatures()

