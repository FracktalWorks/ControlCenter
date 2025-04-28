"""
Printer Model Module
Handles printer state, temperature monitoring, and operations
"""
import time
from PyQt5.QtCore import QObject, pyqtSignal
from utils.logger import setup_logger

logger = setup_logger()

class PrinterModel(QObject):
    """
    Model class for printer state and operations
    Handles maintaining state of the printer including temperatures,
    file information, and print status
    """
    # Signal definitions
    temperatures_updated = pyqtSignal(dict)
    status_updated = pyqtSignal(str)
    print_status_updated = pyqtSignal(dict)
    active_extruder_changed = pyqtSignal(int)
    z_probe_offset_updated = pyqtSignal(float)
    tool_offset_updated = pyqtSignal(dict)
    printer_error_signal = pyqtSignal(str)
    filament_sensor_triggered = pyqtSignal(str)
    z_probing_failed = pyqtSignal()

    def __init__(self):
        super(PrinterModel, self).__init__()
        self.temperatures = {
            'tool0Actual': 0, 'tool0Target': 0,
            'tool1Actual': 0, 'tool1Target': 0,
            'bedActual': 0, 'bedTarget': 0
        }
        self.printer_status = "Offline"
        self.active_extruder = 0
        self.current_file = None
        self.current_image = None
        self.z_probe_offset = 0.0
        self.tool_offsets = {'X': 0, 'Y': 0, 'Z': 0}
        self.print_progress = 0
        self.print_time = 0
        self.print_time_left = 0
        
        # Configuration constants (to be moved to config file later)
        self.filaments = {
            "PLA": 190,
            "ABS": 220,
            "PETG": 220,
            "PVA": 210,
            "TPU": 230,
            "Nylon": 220,
            "PolyCarbonate": 240,
            "HIPS": 220,
            "WoodFill": 220,
            "CopperFill": 200,
            "Breakaway": 220
        }
        
        self.calibration_positions = {
            'X1': 63, 'Y1': 67,
            'X2': 542, 'Y2': 67,
            'X3': 303, 'Y3': 567,
            'X4': 303, 'Y4': 20
        }
        
        self.tool0_purge_position = {'X': -27, 'Y': -112}
        self.tool1_purge_position = {'X': 648, 'Y': -112}

    def update_temperatures(self, temp_data):
        """Updates temperature data"""
        self.temperatures = temp_data
        self.temperatures_updated.emit(temp_data)

    def update_status(self, status):
        """Updates printer status"""
        self.printer_status = status
        self.status_updated.emit(status)

    def update_print_status(self, file_info):
        """Updates print job status"""
        if file_info is None:
            self.current_file = None
            self.current_image = None
            self.print_progress = 0
            self.print_time = 0
            self.print_time_left = 0
        else:
            self.current_file = file_info.get('job', {}).get('file', {}).get('name')
            if file_info.get('progress', {}).get('completion') is not None:
                self.print_progress = file_info['progress']['completion']
            
            if file_info.get('progress', {}).get('printTime') is not None:
                self.print_time = file_info['progress']['printTime']
                
            if file_info.get('progress', {}).get('printTimeLeft') is not None:
                self.print_time_left = file_info['progress']['printTimeLeft']
        
        self.print_status_updated.emit(file_info)

    def set_active_extruder(self, extruder):
        """Sets the active extruder"""
        try:
            self.active_extruder = int(extruder)
            self.active_extruder_changed.emit(self.active_extruder)
        except ValueError:
            logger.error(f"Invalid extruder value: {extruder}")

    def set_z_probe_offset(self, offset):
        """Sets the Z probe offset"""
        try:
            self.z_probe_offset = float(offset)
            self.z_probe_offset_updated.emit(self.z_probe_offset)
        except ValueError:
            logger.error(f"Invalid Z probe offset value: {offset}")

    def set_tool_offset(self, offset_data):
        """Sets tool offset from M218 response"""
        try:
            if 'X' in offset_data:
                self.tool_offsets['X'] = float(offset_data[offset_data.index('X') + 1:].split(' ', 1)[0])
            if 'Y' in offset_data:
                self.tool_offsets['Y'] = float(offset_data[offset_data.index('Y') + 1:].split(' ', 1)[0])
            if 'Z' in offset_data:
                self.tool_offsets['Z'] = float(offset_data[offset_data.index('Z') + 1:].split(' ', 1)[0])
                
            self.tool_offset_updated.emit(self.tool_offsets)
        except Exception as e:
            logger.error(f"Error parsing tool offset data: {e}")

    def format_print_time(self, seconds):
        """Format print time in days, hours, minutes, seconds"""
        if seconds is None:
            return "-"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return "%d:%d:%02d:%02d" % (d, h, m, s)