from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

class PrinterStatus(QObject):
    temperatures_updated = pyqtSignal(np.ndarray, dict)
    rgb_frame_updated = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.frame: Optional[Any] = None
        self.chamberTemperatures: Dict[str, float] = {}
        self.chamberTemperatureSetpoint = 0
        self.chamberHeatingStarted = False
        self.rgb_frame: Optional[Any] = None



    def updateTemperatures(self, frame: Any, chamberTemperatures: Dict[str, float]):
        """Update the model with a new frame and temperature values."""
        self.frame = frame
        self.chamberTemperatures = chamberTemperatures.copy()
        self.temperatures_updated.emit(frame, chamberTemperatures)

    def updateRGBFrame(self, frame: Any):
        """Update the model with a new RGB frame."""
        self.rgb_frame = frame
        self.rgb_frame_updated.emit(frame)
