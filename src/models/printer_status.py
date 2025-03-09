from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

class PrinterStatus(QObject):
    temperatures_updated = pyqtSignal(np.ndarray, dict)

    def __init__(self):
        super().__init__()
        self.frame: Optional[Any] = None
        self.temps: Dict[str, float] = {}
        self.is_printing: bool = False
        self.progress: float = 0.0

    def updateTemperatures(self, frame: Any, temps: Dict[str, float]):
        """Update the model with a new frame and temperature values."""
        self.frame = frame
        self.temps = temps.copy()
        self.temperatures_updated.emit(frame, temps)
