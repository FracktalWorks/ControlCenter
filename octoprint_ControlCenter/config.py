IGNORED_PRINTER_ERRORS = [
    "Move out of range:",
]
# Critical printer errors that require immediate attention, can cancel the print using mainController.showPrinterError
CRITICAL_PRINTER_ERRORS = [
    "Can not update MCU", 
    "Error loading template", 
    "Must home axis first", 
    "probe",
    "Error during homing move", 
    "still triggered after retract", 
    "'mcu' must be specified", 
    "Unable to connect",
    "Shutdown due to M112",
    "Printer is not ready"
]
from collections import OrderedDict

# Configuration settings
ip = '0.0.0.0'
apiKey = 'B508534ED20348F090B4D0AD637D3660'   

# Screen resolution settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

file_name = ''

filaments = [
    ("PLA", 190),
    ("ABS", 220),
    ("PETG", 220),
    ("PVA", 210),
    ("TPU", 230),
    ("Nylon", 220),
    ("PolyCarbonate", 240),
    ("HIPS", 220),
    ("WoodFill", 220),
    ("CopperFill", 200),
    ("Breakaway", 220)
]

filaments = OrderedDict(filaments)

# Values before 2020 changes
calibrationPosition = {
    'X1': 63, 'Y1': 67,  # 110, 18
    'X2': 542, 'Y2': 67,  # 510, 18
    'X3': 303, 'Y3': 567,  # 310, 308
    'X4': 303, 'Y4': 20
}

tool0PurgePosition = {'X': -27, 'Y': -112}
tool1PurgePosition = {'X': 648, 'Y': -112}

ptfeTubeLength = 1500  # 2400 for 600x600, 1500 for 600x300 keep as multiples of 300 only