# https://github.com/alchemyEngine/MoonrakerPy/blob/main/moonrakerpy for all functions

from moonrakerpy import MoonrakerPrinter

class MoonrakerAPI:
    def __init__(self, base_url):
        self.client = MoonrakerPrinter(base_url)

 
    def send_gcode(self, cmd):
        return self.client.send_gcode(cmd)
    
    def query_status(self):
        return self.client.query_status()
    
    def query_temperatures(self):
        return self.client.query_temperatures()

