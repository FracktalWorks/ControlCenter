from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QComboBox, QProgressBar, QLabel

class ChangeFilament(QWidget):
    def __init__(self, main_window):
        super(ChangeFilament, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/changeFilament/changeFilament.ui', self)
            print("UI file loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

        # Find buttons by their object names
        self.changeFilamentBackButton = self.findChild(QPushButton, 'changeFilamentBackButton')
        self.changeFilamentLoadButton = self.findChild(QPushButton, 'changeFilamentLoadButton')
        self.changeFilamentUnloadButton = self.findChild(QPushButton, 'changeFilamentUnloadButton')
        self.toolToggleChangeFilamentButton = self.findChild(QPushButton, 'toolToggleChangeFilamentButton')
        self.changeFilamentBackButton2 = self.findChild(QPushButton, 'changeFilamentBackButton2')
        self.changeFilamentBackButton3 = self.findChild(QPushButton, 'changeFilamentBackButton3')
        self.loadedTillExtruderButton = self.findChild(QPushButton, 'loadedTillExtruderButton')
        self.loadDoneButton = self.findChild(QPushButton, 'loadDoneButton')
        self.unloadDoneButton = self.findChild(QPushButton, 'unloadDoneButton')

        # Find other UI elements
        self.changeFilamentComboBox = self.findChild(QComboBox, 'changeFilamentComboBox')
        self.changeFilamentProgress = self.findChild(QProgressBar, 'changeFilamentProgress')
        self.changeFilamentStatus = self.findChild(QLabel, 'changeFilamentStatus')

        # Find stacked widget and pages
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        self.changeFilamentPage = self.findChild(QWidget, 'changeFilamentPage')
        self.changeFilamentProgressPage = self.findChild(QWidget, 'changeFilamentProgressPage')
        self.changeFilamentLoadPage = self.findChild(QWidget, 'changeFilamentLoadPage')
        self.changeFilamentExtrudePage = self.findChild(QWidget, 'changeFilamentExtrudePage')
        self.changeFilamentRetractPage = self.findChild(QWidget, 'changeFilamentRetractPage')

        # Check if all elements are found
        if not all([
            self.changeFilamentBackButton, self.changeFilamentLoadButton, self.changeFilamentUnloadButton,
            self.toolToggleChangeFilamentButton, self.changeFilamentBackButton2, self.changeFilamentBackButton3,
            self.loadedTillExtruderButton, self.loadDoneButton, self.unloadDoneButton,
            self.changeFilamentComboBox, self.changeFilamentProgress, self.changeFilamentStatus,
            self.stackedWidget, self.changeFilamentPage, self.changeFilamentProgressPage,
            self.changeFilamentLoadPage, self.changeFilamentExtrudePage, self.changeFilamentRetractPage
        ]):
            raise ValueError("One or more UI elements not found in the UI file")

        # Connect buttons to their respective functions
        self.changeFilamentBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        self.changeFilamentLoadButton.clicked.connect(self.start_loading_filament)
        self.changeFilamentUnloadButton.clicked.connect(self.start_unloading_filament)
        self.toolToggleChangeFilamentButton.clicked.connect(self.toggle_tool)
        self.changeFilamentBackButton2.clicked.connect(self.main_window.switch_to_previous_screen)
        self.changeFilamentBackButton3.clicked.connect(self.main_window.switch_to_previous_screen)
        self.loadedTillExtruderButton.clicked.connect(self.filament_loaded_till_extruder)
        self.loadDoneButton.clicked.connect(self.finish_loading_filament)
        self.unloadDoneButton.clicked.connect(self.finish_unloading_filament)

        # Set the default screen to changeFilamentPage
        self.stackedWidget.setCurrentWidget(self.changeFilamentPage)

    def start_loading_filament(self):
        """Start the filament loading process."""
        print("Starting filament loading process")
        self.stackedWidget.setCurrentWidget(self.changeFilamentProgressPage)
        self.changeFilamentStatus.setText("Heating...")

    def start_unloading_filament(self):
        """Start the filament unloading process."""
        print("Starting filament unloading process")
        self.stackedWidget.setCurrentWidget(self.changeFilamentRetractPage)
        self.changeFilamentStatus.setText("Retracting...")

    def toggle_tool(self):
        """Toggle between tools."""
        print("Toggling tool")
        # Add logic to toggle between tools

    def filament_loaded_till_extruder(self):
        """Handle the event when filament is loaded till the extruder."""
        print("Filament loaded till extruder")
        self.stackedWidget.setCurrentWidget(self.changeFilamentExtrudePage)

    def finish_loading_filament(self):
        """Finish the filament loading process."""
        print("Filament loading process finished")
        self.main_window.switch_to_previous_screen()

    def finish_unloading_filament(self):
        """Finish the filament unloading process."""
        print("Filament unloading process finished")
        self.main_window.switch_to_previous_screen()