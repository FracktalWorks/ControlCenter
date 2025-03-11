# https://github.com/alchemyEngine/MoonrakerPy/blob/main/moonrakerpy for all functions

from moonrakerpy import MoonrakerPrinter

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


class MoonrakerAPI:
    def __init__(self, base_url):
        self.client = MoonrakerPrinter(base_url)

    def send_gcode(self, cmd):
        try:
            return self.client.send_gcode(cmd)
        except Exception as e:
            return str(e)
    
    @run_async
    def query_status(self):
        return self.client.query_status()
    @run_async
    def query_temperatures(self):
        return self.client.query_temperatures()

