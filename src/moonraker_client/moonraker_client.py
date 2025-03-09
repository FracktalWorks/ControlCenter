# filepath: c:\Users\VijayRaghavVarada\Documents\Github\ControlCenter\src\octoprint_client\moonraker_client.py
from moonrakerpy import MoonrakerClient

class MoonrakerAPI:
    def __init__(self, base_url):
        self.client = MoonrakerClient(base_url)

    def get_printer_status(self):
        return self.client.get_printer_status()

    def start_print(self, file_path):
        return self.client.start_print(file_path)

    def stop_print(self):
        return self.client.stop_print()

    def pause_print(self):
        return self.client.pause_print()

    def resume_print(self):
        return self.client.resume_print()

    # Add more methods as needed