def format_printer_status(status):
    """Format the printer status for display."""
    return f"Status: {status['state']['text']}, Progress: {status['progress']['completion']}%"

def handle_api_error(error):
    """Handle errors from the OctoPrint API."""
    print(f"API Error: {error}")

def validate_ip_address(ip):
    """Validate the format of an IP address."""
    import re
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    return re.match(pattern, ip) is not None

def convert_to_percentage(value, total):
    """Convert a value to a percentage of a total."""
    if total == 0:
        return 0
    return (value / total) * 100

from PyQt5.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(Exception)

class Worker(QRunnable):
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            self.signals.error.emit(e)
        finally:
            self.signals.finished.emit()

# Keep a reference to the workers to prevent them from being garbage collected
workers = []

def run_async(func):
    """
    Function decorator to make methods run in a QRunnable
    """
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        worker = Worker(func, *args, **kwargs)
        worker.signals.error.connect(lambda e: print(f"Error in thread: {e}"))
        
        workers.append(worker)  # Keep a reference to the worker
        QThreadPool.globalInstance().start(worker)
        return worker

    return async_func