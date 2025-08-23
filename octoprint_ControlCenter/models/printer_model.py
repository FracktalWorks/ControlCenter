"""
Printer Model Module
Handles printer state, temperature monitoring, and operations
"""
import time
from PyQt5.QtCore import QObject, pyqtSignal
from utils.logger import get_logger
logger = get_logger(__name__)
from utils import dialog
# Use configuration from config.py
import config
from utils.printer_config_store import PrinterConfigStore

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
    print_status_updated = pyqtSignal('PyQt_PyObject')  # ! done
    active_extruder_changed = pyqtSignal(str)  # ! done
    z_probe_offset_updated = pyqtSignal(str)  # ! done
    tool_offset_updated = pyqtSignal(str)  # done
    printer_error_signal = pyqtSignal(str)  # done
    filament_sensor_triggered = pyqtSignal(str)  # done
    filament_runout_sensor_triggered = pyqtSignal(str)
    filament_jam_sensor_triggered = pyqtSignal(str)
    filament_runout_state = pyqtSignal(str, bool)
    z_probing_failed = pyqtSignal()  # done
    z_tool_offset_updated = pyqtSignal(str)  # done
    update_started_signal = pyqtSignal(dict)
    update_log_signal = pyqtSignal(dict)  # ! REMAINING
    update_log_result_signal = pyqtSignal(dict)  # ! REMAINING
    update_failed_signal = pyqtSignal(dict)  # ! REMAINING
    connected_signal = pyqtSignal()  # done
    # Klipper state propagated from websocket via controller
    klipper_state_changed = pyqtSignal(str)
    # Signals for tool-bay state persistence and UI sync
    tool_bay_states_loaded = pyqtSignal(dict)      # {'tool0': {...}, 'tool1': {...}}
    tool_bay_state_changed = pyqtSignal(str, str, dict) # tool, bay, bay_state
    # Signals for feed rate and flow rate updates
    feed_rate_updated = pyqtSignal(int)  # Feed rate percentage
    flow_rate_updated = pyqtSignal(int)  # Flow rate percentage

    def __init__(self):
        super(PrinterModel, self).__init__()
        self.logger = get_logger(self.__class__.__name__)
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
        self.filaments = config.filaments
        self.calibrationPosition = config.calibrationPosition
        self.tool0PurgePosition = config.tool0PurgePosition
        self.tool1PurgePosition = config.tool1PurgePosition
        self.ptfeTubeLength = config.ptfeTubeLength
        self.machineBuildSize = config.machineBuildSize
        # Klipper state cache
        self.klipper_state = "unknown"
        # Tool state persistence
        # self.status_options = ["Empty", "Unknown", "Loaded", "Staged"]
        self.status_options = ["Empty", "Loaded"]
        self.nozzle_options = ["0.25", "0.4", "0.6", "0.8", "1.0"]
        # Nested per-bay structure per tool; defaults reflect current A/B mapping
        self.tools = {
            "tool0": {
                "material_bay_a": {"filament": None, "status": "Unknown", "nozzle": "Unknown"}
            },
            "tool1": {
                "material_bay_x": {"filament": None, "status": "Unknown", "nozzle": "Unknown"}
            },
        }
        self._config_store = PrinterConfigStore()
        # Load full cached state once
        try:
            state = self._config_store.load_full()
        except Exception as e:
            self.logger.error(f"Failed to load printer config store: {e}")
            state = {"tools": {}, "preferences": {}}
        # Initialize tools from cached state
        self._init_tools_from_store(state.get("tools", {}))
        # Filament sensor states & preferences
        prefs = state.get("preferences", {})
        self.filament_runout_sensor_persistent_state = bool(prefs.get("filament_runout_enabled", False))
        self.filament_jam_sensor_persistent_state = bool(prefs.get("filament_jam_enabled", False))
        self.print_compatibility_check_enabled = bool(prefs.get("print_compatibility_check_enabled", True))  # Default to enabled
        self.filament_runout_state_map = {}  # {sensor: bool}
        
        # Feed rate and flow rate storage
        self.current_feed_rate = 100  # Default 100%
        self.current_flow_rate = 100  # Default 100%

    # --- Filament sensor preference setters (called by controller/UI) -------
    def set_filament_runout_pref(self, enabled: bool, persist: bool = True):
        prev = self.filament_runout_sensor_persistent_state
        self.filament_runout_sensor_persistent_state = bool(enabled)
        try:
            self.filament_runout_sensor_persistent_state.emit('1' if enabled else '0')  # type: ignore
        except Exception:
            pass
        if persist and prev != enabled:
            self._config_store.set_preference('filament_runout_enabled', bool(enabled))

    def set_filament_jam_pref(self, enabled: bool, persist: bool = True):
        prev = self.filament_jam_sensor_persistent_state
        self.filament_jam_sensor_persistent_state = bool(enabled)
        try:
            self.filament_jam_sensor_persistent_state.emit('1' if enabled else '0')  # type: ignore
        except Exception:
            pass
        if persist and prev != enabled:
            self._config_store.set_preference('filament_jam_enabled', bool(enabled))

    def set_print_compatibility_check_pref(self, enabled: bool, persist: bool = True):
        """Set print compatibility check preference and persist if requested."""
        prev = self.print_compatibility_check_enabled
        self.print_compatibility_check_enabled = bool(enabled)
        if persist and prev != enabled:
            self._config_store.set_preference('print_compatibility_check_enabled', bool(enabled))

    def update_feed_rate(self, rate: int):
        """Update the current feed rate and emit signal."""
        try:
            self.current_feed_rate = max(1, min(500, int(rate)))  # Clamp between 1-500%
            self.feed_rate_updated.emit(self.current_feed_rate)
        except (ValueError, TypeError):
            self.logger.error(f"Invalid feed rate value: {rate}")

    def update_flow_rate(self, rate: int):
        """Update the current flow rate and emit signal."""
        try:
            self.current_flow_rate = max(1, min(500, int(rate)))  # Clamp between 1-500%
            self.flow_rate_updated.emit(self.current_flow_rate)
        except (ValueError, TypeError):
            self.logger.error(f"Invalid flow rate value: {rate}")

    def updateTemperature(self, temp_data):
        """ Updates the temperature data. Is a slot for the temperatures_updated signal. """
        if temp_data['tool0Actual'] is None:
            temp_data['tool0Actual'] = 0
        if temp_data['tool0Target'] is None:
            temp_data['tool0Target'] = 0
        if temp_data['tool1Actual'] is None:
            temp_data['tool1Actual'] = 0
        if temp_data['tool1Target'] is None:
            temp_data['tool1Target'] = 0
        if temp_data['bedActual'] is None:
            temp_data['bedActual'] = 0
        if temp_data['bedTarget'] is None:
            temp_data['bedTarget'] = 0
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
            self.active_extruder = extruder
            self.active_extruder_changed.emit(self.active_extruder)
        except ValueError:
            self.logger.error(f"Invalid extruder value: {extruder}")

    def updateEEPROMProbeOffset(self, offset):
        """ Updates the Z probe offset in EEPROM """
        try:
            self.z_probe_offset = offset
            self.z_probe_offset_updated.emit(self.z_probe_offset)
        except ValueError:
            self.logger.error(f"Invalid Z probe offset value: {offset}")
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
            self.tool_offset_updated.emit(M218Data)
        except Exception as e:
            self.logger.error("Error in PrinterModel.getToolOffset: {}".format(e))
            dialog.WarningOk(self, "Error in PrinterModel.getToolOffset: {}".format(e), overlay=True)

    def filamentSensorHandler(self, data):
        """
        Handles legacy filament sensor trigger events.
        :param data: Data from the filament sensor.
        """
        self.filament_sensor_triggered.emit(data)

    def filamentRunoutSensorTriggered(self, tool):
        """
        Handles filament runout sensor triggered events.
        :param tool: Tool identifier.
        """
        self.filament_runout_sensor_triggered.emit(tool)

    def filamentJamSensorTriggered(self, tool):
        """
        Handles filament jam sensor triggered events.
        :param tool: Tool identifier.
        """
        self.filament_jam_sensor_triggered.emit(tool)

    def filamentRunoutState(self, sensor, present):
        """
        Handles filament runout state events.
        :param sensor: Sensor identifier.
        :param present: Boolean indicating filament runout.
        """
        # Store in map for UI access
        self.filament_runout_state_map[sensor] = bool(present)
        self.filament_runout_state.emit(sensor, present)

    def setZToolOffset(self, offset):
        # self.tool_offsets['Z'] = offset
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
        self.update_log_result_signal.emit(update_info)

    def updateFailed(self, update_info):
        self.updateData = update_info
        self.update_failed_signal.emit(update_info)

    # --- Tool state persistence helpers ---
    def _sanitize_bay_state(self, v: dict) -> dict:
        filament = v.get("filament")
        status = v.get("status", "Unknown")
        nozzle = v.get("nozzle", "Unknown")
        if status not in self.status_options:
            status = "Unknown"
        if nozzle not in self.nozzle_options and nozzle != "Unknown":
            nozzle = "Unknown"
        return {"filament": filament, "status": status, "nozzle": nozzle}

    def _init_tools_from_store(self, tools_state: dict):
        try:
            for tool_id in ("tool0", "tool1"):
                raw = tools_state.get(tool_id, {})
                # Already upgraded by store; just validate & copy
                cleaned = {}
                for bay, v in raw.items():
                    cleaned[bay] = self._sanitize_bay_state(v)
                if not cleaned:
                    cleaned = {("material_bay_a" if tool_id == "tool0" else "material_bay_x"): {"filament": None, "status": "Unknown", "nozzle": "Unknown"}}
                self.tools[tool_id] = cleaned
            self.tool_bay_states_loaded.emit(self.tools.copy())
        except Exception as e:
            self.logger.error(f"Failed initializing tool state: {e}")
            self.tool_bay_states_loaded.emit(self.tools.copy())

    def update_tool_bay_state(self, tool: str, bay: str = None, filament=None, status=None, nozzle=None, persist=True):
        if tool not in ("tool0", "tool1"):
            self.logger.error(f"Invalid tool: {tool}")
            return
        bay = bay or ("material_bay_a" if tool == "tool0" else "material_bay_x")
        # Validate inputs
        if status is not None and status not in self.status_options:
            status = "Unknown"
        if nozzle is not None and (nozzle not in self.nozzle_options and nozzle != "Unknown"):
            nozzle = "Unknown"
        cur = self._config_store.set_tool_state(tool, bay=bay, filament=filament if filament is not None else None,
                                                status=status if status is not None else None,
                                                nozzle=nozzle if nozzle is not None else None)
        # Mirror into in-memory tools dict
        if tool not in self.tools:
            self.tools[tool] = {}
        self.tools[tool][bay] = cur
        self.tool_bay_state_changed.emit(tool, bay, cur.copy())

    # Backward-compatible wrapper
    def set_tool_state(self, tool: str, bay: str = None, filament=None, status=None, nozzle=None, persist=True):
        return self.update_tool_bay_state(tool, bay, filament, status, nozzle, persist)

    # Convenience getters for primary bays used by current UI
    def get_default_bay(self, tool: str) -> str:
        return "material_bay_a" if tool == "tool0" else "material_bay_x"
    def get_bay_state(self, tool: str, bay: str = None) -> dict:
        bay = bay or self.get_default_bay(tool)
        return self.tools.get(tool, {}).get(bay, {"filament": None, "status": "Unknown", "nozzle": "Unknown"})

    def get_current_tool_config(self):
        """
        Get current nozzle and material configuration for both tools.
        Returns dictionary with current setup for validation against GCODE metadata.
        """
        config = {}
        for tool in ["tool0", "tool1"]:
            bay_state = self.get_bay_state(tool)
            config[tool] = {
                'nozzle': bay_state.get('nozzle', 'Unknown'),
                'material': bay_state.get('filament', None)
            }
        return config

    # --- Klipper state updater ---
    def update_klipper_state(self, state: str):
        try:
            norm = str(state).strip().lower() if state is not None else "unknown"
            # Only emit if changed to avoid UI churn
            if getattr(self, 'klipper_state', None) != norm:
                self.klipper_state = norm
                self.klipper_state_changed.emit(norm)
        except Exception:
            # Ensure we don't crash signal flow
            self.klipper_state = str(state)
            self.klipper_state_changed.emit(self.klipper_state)
