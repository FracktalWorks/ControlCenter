import json
import os
import tempfile
from utils.logger import get_logger


logger = get_logger(__name__)


PRIMARY_PATH = "/home/pi/.octoprint/.printerConfig"
FALLBACK_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                             ".printerConfig")


DEFAULT_STATE = {
    "version": 1,
    "tools": {
        "tool0": {
            "material_bay_a": {"filament": None, "status": "Unknown", "nozzle": "Unknown"}
        },
        "tool1": {
            "material_bay_x": {"filament": None, "status": "Unknown", "nozzle": "Unknown"}
        },
    },
}


class PrinterConfigStore:
    """Persistence layer for current filament/nozzle state.

    - Loads from PRIMARY_PATH; if missing/unreadable, falls back to FALLBACK_PATH.
    - Saves atomically; prefers PRIMARY_PATH if directory exists, else FALLBACK_PATH.
    """

    def __init__(self, primary_path: str = PRIMARY_PATH, fallback_path: str = FALLBACK_PATH):
        self.primary_path = primary_path
        self.fallback_path = fallback_path

    def _read_json(self, path: str):
        try:
            if not os.path.exists(path):
                return None
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read printer config at {path}: {e}")
            return None

    def load(self) -> dict:
        data = self._read_json(self.primary_path)
        if data is not None:
            return data
        data = self._read_json(self.fallback_path)
        if data is not None:
            return data
        return DEFAULT_STATE.copy()

    def _atomic_write(self, dest_path: str, data: dict):
        directory = os.path.dirname(dest_path)
        if not os.path.isdir(directory):
            # Directory must exist for atomic write; let caller choose fallback
            raise FileNotFoundError(f"Directory does not exist: {directory}")

        fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".printerConfig.tmp.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                json.dump(data, tmp, indent=2)
                tmp.flush()
                os.fsync(tmp.fileno())
            # Atomic replace on POSIX and Windows (since Python 3.3)
            os.replace(tmp_path, dest_path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    def save(self, state: dict) -> bool:
        for path in (self.primary_path, self.fallback_path):
            try:
                self._atomic_write(path, state)
                logger.info(f"Saved printer config to {path}")
                return True
            except FileNotFoundError:
                # Try next path
                continue
            except Exception as e:
                logger.error(f"Failed to save printer config at {path}: {e}")
        return False
