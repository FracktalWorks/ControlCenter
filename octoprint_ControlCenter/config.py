IGNORED_PRINTER_ERRORS = [
    "Move out of range:"
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
    ("PC", 240),
    ("HIPS", 220),
    ("WoodFill", 220),
    ("MetalFill", 200)
]

filaments = OrderedDict(filaments)

# Values before 2020 changes
calibrationPosition = {'X1': 110, 'Y1': 18,
                       'X2': 510, 'Y2': 18,
                       'X3': 310, 'Y3': 308,
                       'X4': 310, 'Y4': 178
                       }

machineBuildSize = {'X': 600, 'Y': 300, 'Z': 400}


tool0PurgePosition = {'X': -30, 'Y': -77}
tool1PurgePosition = {'X': 655, 'Y': -77}

ptfeTubeLength = 1500  # 2400 for 600x600, 1500 for 600x300 keep as multiples of 300 only

# Printer Configuration
IS_DUAL_NOZZLE = True  # Set to False for single nozzle printers

def is_dual_nozzle_printer():
    """Check if the printer is configured for dual nozzle operation."""
    return IS_DUAL_NOZZLE