# https://github.com/alchemyEngine/MoonrakerPy/blob/main/moonrakerpy for all functions

import requests

class MoonrakerAPI:
    def __init__(self, base_url):
        self.base_url = base_url

    def reconnect(self):
        """
        Attempt to reconnect to the Moonraker server.
        """
        try:
            # No specific action needed for reconnecting in this context
            print("Reconnected to Moonraker server.")
        except Exception as e:
            print(f"Failed to reconnect: {e}")

    def send_gcode(self, cmd):
        try:
            response = requests.post(
                url=f"{self.base_url}/printer/gcode/script",
                json={"script": cmd},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print("Request to Moonraker timed out.")
            self.reconnect()
            return "Timeout"
        except requests.exceptions.RequestException as e:
            print(f"Error sending G-code: {e}")
            self.reconnect()
            return str(e)

    def query_status(self):
        try:
            response = requests.get(
                url=f"{self.base_url}/printer/objects/query?status",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print("Request to Moonraker timed out.")
            self.reconnect()
            return "Timeout"
        except requests.exceptions.RequestException as e:
            print(f"Error querying status: {e}")
            self.reconnect()
            return str(e)

    def query_temperatures(self):
        try:
            response = requests.get(
                url=f"{self.base_url}/printer/objects/query?temperature",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print("Request to Moonraker timed out.")
            self.reconnect()
            return "Timeout"
        except requests.exceptions.RequestException as e:
            print(f"Error querying temperatures: {e}")
            self.reconnect()
            return str(e)

