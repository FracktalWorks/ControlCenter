from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QComboBox, QProgressBar, QLabel
from utils.helpers import check_ui_elements

class ChangeFilament(QWidget):
    def __init__(self, main_window):
        super(ChangeFilament, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/changeFilament/changeFilament.ui', self)
            print("ChangeFilament UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ChangeFilament UI file: {e}")

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

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions - with safety checks
        self._connect_buttons()

        # Set the default screen to changeFilamentPage
        if self.stackedWidget and self.changeFilamentPage:
            self.stackedWidget.setCurrentWidget(self.changeFilamentPage)

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Group widgets for better reporting
        main_widgets = {
            "stackedWidget": self.stackedWidget,
            "changeFilamentPage": self.changeFilamentPage,
            "changeFilamentProgressPage": self.changeFilamentProgressPage,
            "changeFilamentLoadPage": self.changeFilamentLoadPage,
            "changeFilamentExtrudePage": self.changeFilamentExtrudePage,
            "changeFilamentRetractPage": self.changeFilamentRetractPage
        }
        check_ui_elements(self, main_widgets, "ChangeFilament - Main Widgets")
        
        buttons = {
            "changeFilamentBackButton": self.changeFilamentBackButton,
            "changeFilamentLoadButton": self.changeFilamentLoadButton,
            "changeFilamentUnloadButton": self.changeFilamentUnloadButton,
            "toolToggleChangeFilamentButton": self.toolToggleChangeFilamentButton,
            "changeFilamentBackButton2": self.changeFilamentBackButton2,
            "changeFilamentBackButton3": self.changeFilamentBackButton3,
            "loadedTillExtruderButton": self.loadedTillExtruderButton,
            "loadDoneButton": self.loadDoneButton,
            "unloadDoneButton": self.unloadDoneButton
        }
        check_ui_elements(self, buttons, "ChangeFilament - Buttons")
        
        other_elements = {
            "changeFilamentComboBox": self.changeFilamentComboBox,
            "changeFilamentProgress": self.changeFilamentProgress,
            "changeFilamentStatus": self.changeFilamentStatus
        }
        check_ui_elements(self, other_elements, "ChangeFilament - Other Elements")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        if self.changeFilamentBackButton:
            self.changeFilamentBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        
        if self.changeFilamentLoadButton:
            self.changeFilamentLoadButton.clicked.connect(self.start_loading_filament)
        
        if self.changeFilamentUnloadButton:
            self.changeFilamentUnloadButton.clicked.connect(self.start_unloading_filament)
        
        if self.toolToggleChangeFilamentButton:
            self.toolToggleChangeFilamentButton.clicked.connect(self.toggle_tool)
        
        if self.changeFilamentBackButton2:
            self.changeFilamentBackButton2.clicked.connect(self.main_window.switch_to_previous_screen)
        
        if self.changeFilamentBackButton3:
            self.changeFilamentBackButton3.clicked.connect(self.main_window.switch_to_previous_screen)
        
        if self.loadedTillExtruderButton:
            self.loadedTillExtruderButton.clicked.connect(self.filament_loaded_till_extruder)
        
        if self.loadDoneButton:
            self.loadDoneButton.clicked.connect(self.finish_loading_filament)
        
        if self.unloadDoneButton:
            self.unloadDoneButton.clicked.connect(self.finish_unloading_filament)

    def start_loading_filament(self):
        """Start the filament loading process."""
        print("Starting filament loading process")
        if self.stackedWidget and self.changeFilamentProgressPage:
            self.stackedWidget.setCurrentWidget(self.changeFilamentProgressPage)
        if self.changeFilamentStatus:
            self.changeFilamentStatus.setText("Heating...")

    def start_unloading_filament(self):
        """Start the filament unloading process."""
        print("Starting filament unloading process")
        if self.stackedWidget and self.changeFilamentRetractPage:
            self.stackedWidget.setCurrentWidget(self.changeFilamentRetractPage)
        if self.changeFilamentStatus:
            self.changeFilamentStatus.setText("Retracting...")

    def toggle_tool(self):
        """Toggle between tools."""
        print("Toggling tool")
        # Add logic to toggle between tools

    def filament_loaded_till_extruder(self):
        """Handle the event when filament is loaded till the extruder."""
        print("Filament loaded till extruder")
        if self.stackedWidget and self.changeFilamentExtrudePage:
            self.stackedWidget.setCurrentWidget(self.changeFilamentExtrudePage)

    def finish_loading_filament(self):
        """Finish the filament loading process."""
        print("Filament loading process finished")
        self.main_window.switch_to_previous_screen()

    def finish_unloading_filament(self):
        """Finish the filament unloading process."""
        print("Filament unloading process finished")
        self.main_window.switch_to_previous_screen()