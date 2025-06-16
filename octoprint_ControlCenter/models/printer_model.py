"""
Printer Model Module
Handles printer state, temperature monitoring, and operations
"""
import time
from PyQt5.QtCore import QObject, pyqtSignal
from utils.logger import setup_logger
from utils import dialog

logger = setup_logger("printer_model")

class PrinterModel(QObject):
    """
    Model class for printer state and operations
    Handles maintaining state of the printer including temperatures,
    file information, and print status
    """
    # Signal definitions
    # this one should have signal slot connections probably
    temperatures_updated = pyqtSignal(dict)  # done
    status_updated = pyqtSignal(str)  # done
    print_status_updated = pyqtSignal(dict)  # done
    active_extruder_changed = pyqtSignal(int)  # done
    z_probe_offset_updated = pyqtSignal(float)  # done
    tool_offset_updated = pyqtSignal(dict)  # done
    printer_error_signal = pyqtSignal(str)  # done
    filament_sensor_triggered = pyqtSignal(str)  # done
    z_probing_failed = pyqtSignal()  # done
    z_tool_offset_updated = pyqtSignal(float)  # done
    update_started_signal = pyqtSignal(dict)
    update_log_signal = pyqtSignal(dict)  # ! REMAINING
    update_log_result_signal = pyqtSignal(dict)  # ! REMAINING
    update_failed_signal = pyqtSignal(dict)  # ! REMAINING
    connected_signal = pyqtSignal()  # done

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
        self.updateData = {}
        
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
        
        self.calibrationPosition = {
            'X1': 63, 'Y1': 67,
            'X2': 542, 'Y2': 67,
            'X3': 303, 'Y3': 567,
            'X4': 303, 'Y4': 20
        }
        
        self.tool0PurgePosition = {'X': -27, 'Y': -112}
        self.tool1PurgePosition = {'X': 648, 'Y': -112}

        self.ptfeTubeLength = 1500  # 2400 for 600x600, 1500 for 600x300 keep as multiples of 300 only

    def updateTemperature(self, temp_data):
        """ Updates the temperature data. Is a slot for the temperatures_updated signal. """
        self.temperatures = temp_data
        self.temperatures_updated.emit(temp_data)

    def updateStatus(self, status):
        self.printer_status = status
        self.status_updated.emit(status)

    def updatePrintStatus(self, file_info):
        """Updates print job status"""
        if file_info["job"] is None:
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

    def setActiveExtruder(self, extruder):
        """Sets the active extruder"""
        try:
            self.active_extruder = int(extruder)
            self.active_extruder_changed.emit(self.active_extruder)
        except ValueError:
            logger.error(f"Invalid extruder value: {extruder}")

    def updateEEPROMProbeOffset(self, offset):
        """ Updates the Z probe offset in EEPROM """
        try:
            self.z_probe_offset = float(offset)
            self.z_probe_offset_updated.emit(self.z_probe_offset)
        except ValueError:
            logger.error(f"Invalid Z probe offset value: {offset}")
            dialog.WarningOk(self, "Invalid Z probe offset value: {}".format(offset), overlay=True)

    def getToolOffset(self, M218Data):
        """ Set the tool offsets from M218 response """
        try:
            if 'X' in M218Data:
                self.tool_offsets['X'] = M218Data[M218Data.index('X') + 1:].split(' ', 1)[0]
            if 'Y' in M218Data:
                self.tool_offsets['Y'] = M218Data[M218Data.index('Y') + 1:].split(' ', 1)[0]
            if 'Z' in M218Data:
                self.tool_offsets['Z'] = M218Data[M218Data.index('Z') + 1:].split(' ', 1)[0]

            self.tool_offset_updated.emit(self.tool_offsets)
        except Exception as e:
            logger.error("Error in MainUiClass.getToolOffset: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.getToolOffset: {}".format(e), overlay=True)

    def filamentSensorHandler(self, data):
        """
        Handles filament sensor trigger events.
        :param data: Data from the filament sensor.
        """
        self.filament_sensor_triggered.emit(data)

    def setZToolOffset(self, offset):
        self.tool_offsets['Z'] = offset
        self.z_tool_offset_updated.emit(offset)
        pass

    # Use the softwareUpdateProgress function to send data about software updates
    def softwareUpdateProgress(self, update_info):
        self.updateData = update_info
        self.update_started_signal.emit(update_info)

    def softwareUpdateProgressLog(self, update_info):
        self.updateData = update_info
        self.update_log_signal.emit(update_info)

    def softwareUpdateResult(self, update_info):
        self.updateData = update_info
        self.update_log_signal.emit(update_info)

    def updateFailed(self, update_info):
        self.updateData = update_info
        self.update_log_signal.emit(update_info)


    """ Boilerplate code - might not be needed. getting the functions from the original code """
    # def update_temperatures(self, temp_data):
    #     """Updates temperature data"""
    #     self.temperatures = temp_data
    #     self.temperatures_updated.emit(temp_data)
    #
    # def update_status(self, status):
    #     """Updates printer status"""
    #     self.printer_status = status
    #     self.status_updated.emit(status)
    #
    # def update_print_status(self, file_info):
    #     """Updates print job status"""
    #     if file_info is None:
    #         self.current_file = None
    #         self.current_image = None
    #         self.print_progress = 0
    #         self.print_time = 0
    #         self.print_time_left = 0
    #     else:
    #         self.current_file = file_info.get('job', {}).get('file', {}).get('name')
    #         if file_info.get('progress', {}).get('completion') is not None:
    #             self.print_progress = file_info['progress']['completion']
    #
    #         if file_info.get('progress', {}).get('printTime') is not None:
    #             self.print_time = file_info['progress']['printTime']
    #
    #         if file_info.get('progress', {}).get('printTimeLeft') is not None:
    #             self.print_time_left = file_info['progress']['printTimeLeft']
    #
    #     self.print_status_updated.emit(file_info)
    #
    # def set_active_extruder(self, extruder):
    #     """Sets the active extruder"""
    #     try:
    #         self.active_extruder = int(extruder)
    #         self.active_extruder_changed.emit(self.active_extruder)
    #     except ValueError:
    #         logger.error(f"Invalid extruder value: {extruder}")
    #
    # def set_z_probe_offset(self, offset):
    #     """Sets the Z probe offset"""
    #     try:
    #         self.z_probe_offset = float(offset)
    #         self.z_probe_offset_updated.emit(self.z_probe_offset)
    #     except ValueError:
    #         logger.error(f"Invalid Z probe offset value: {offset}")
    #
    # def set_tool_offset(self, offset_data):
    #     """Sets tool offset from M218 response"""
    #     try:
    #         if 'X' in offset_data:
    #             self.tool_offsets['X'] = float(offset_data[offset_data.index('X') + 1:].split(' ', 1)[0])
    #         if 'Y' in offset_data:
    #             self.tool_offsets['Y'] = float(offset_data[offset_data.index('Y') + 1:].split(' ', 1)[0])
    #         if 'Z' in offset_data:
    #             self.tool_offsets['Z'] = float(offset_data[offset_data.index('Z') + 1:].split(' ', 1)[0])
    #
    #         self.tool_offset_updated.emit(self.tool_offsets)
    #     except Exception as e:
    #         logger.error(f"Error parsing tool offset data: {e}")
    #
    # def format_print_time(self, seconds):
    #     """Format print time in days, hours, minutes, seconds"""
    #     if seconds is None:
    #         return "-"
    #     m, s = divmod(seconds, 60)
    #     h, m = divmod(m, 60)
    #     d, h = divmod(h, 24)
    #     return "%d:%d:%02d:%02d" % (d, h, m, s)