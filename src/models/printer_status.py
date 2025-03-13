from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
import time  # Add this import

class PrinterStatus(QObject):
    temperatures_updated = pyqtSignal(np.ndarray, dict)
    rgb_frame_updated = pyqtSignal(np.ndarray)
    maxtemp_updated = pyqtSignal(float)  # Add the maxtemp_updated signal
    scancard_status_updated = pyqtSignal(str)  # Add the scancard_status_updated signal

    def __init__(self):
        super().__init__()
        self.frame: Optional[Any] = None
        self.chamberTemperatures: Dict[str, float] = {}
        self.chamberTemperatureSetpoint = 0
        self.chamberHeatingStarted = False
        self.rgb_frame: Optional[Any] = None
        self.layerHeight = 0.0
        self.initialLevellingHeight = 0.0
        self.heatedBufferHeight = 0.0
        self.powderLoadingExtraHeightGap = 0.0
        self.bedTemperature = 0.0
        self.volumeTemperature = 0.0
        self.chamberTemperature = 0.0
        self.p = 0.0
        self.i = 0.0
        self.d = 0.0
        self.powderLoadingSequence = ""
        self.moveToStartingSequence = ""
        self.prepareForPartRemovalSequence = ""
        self.initialLevellingRecoatingSequence = ""
        self.heatedBufferRecoatingSequence = ""
        self.printingRecoatingSequence = ""
        self.partHeight = 0.0
        self.dosingHeight = 0.0  # Add dosingHeight
        self.maxTemp = 0.0
        self.last_update_time = time.time()  # Add this attribute
        self.scancard_status = "Unknown"
        self.printing = False

    def updateTemperatures(self, frame: Any, chamberTemperatures: Dict[str, float]):
        """Update the model with a new frame and temperature values."""
        self.frame = frame
        self.chamberTemperatures = chamberTemperatures.copy()
        self.temperatures_updated.emit(frame, chamberTemperatures)
        self.last_update_time = time.time()  # Update the last update time

    def updateRGBFrame(self, frame: Any):
        """Update the model with a new RGB frame."""
        self.rgb_frame = frame
        self.rgb_frame_updated.emit(frame)

    def setLayerHeight(self, value: float):
        self.layerHeight = value

    def setInitialLevellingHeight(self, value: float):
        self.initialLevellingHeight = value

    def setHeatedBufferHeight(self, value: float):
        self.heatedBufferHeight = value

    def setPowderLoadingExtraHeightGap(self, value: float):
        self.powderLoadingExtraHeightGap = value

    def setBedTemperature(self, value: float):
        self.bedTemperature = value

    def setVolumeTemperature(self, value: float):
        self.volumeTemperature = value

    def setChamberTemperature(self, value: float):
        self.chamberTemperature = value

    def setP(self, value: float):
        self.p = value

    def setI(self, value: float):
        self.i = value

    def setD(self, value: float):
        self.d = value

    def setPowderLoadingSequence(self, value: str):
        self.powderLoadingSequence = value

    def setMoveToStartingSequence(self, value: str):
        self.moveToStartingSequence = value

    def setPrepareForPartRemovalSequence(self, value: str):
        self.prepareForPartRemovalSequence = value

    def setInitialLevellingRecoatingSequence(self, value: str):
        self.initialLevellingRecoatingSequence = value

    def setHeatedBufferRecoatingSequence(self, value: str):
        self.heatedBufferRecoatingSequence = value

    def setPrintingRecoatingSequence(self, value: str):
        self.printingRecoatingSequence = value

    def setPartHeight(self, value: float):
        self.partHeight = value

    def setDosingHeight(self, value: float):  # Add setDosingHeight method
        self.dosingHeight = value

    def updateMaxTemp(self, value: float):
        self.maxTemp = value
        self.maxtemp_updated.emit(value)  # Emit the maxtemp_updated signal
    
    def updateScancardStatus(self, status: str):
        self.scancard_status = status