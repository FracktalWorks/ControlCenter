from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements

class BedLeveling(QWidget):
    def __init__(self, main_window):
        super(BedLeveling, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibratePage/bedLevelingPage/bedLevelingPage.ui', self)
            print("BedLeveling UI loaded successfully")
        except Exception as e:
            print(f"Failed to load BedLeveling UI file: {e}")

        # Find buttons by their object names
        self.moveZPT1CaliberateButton = self.findChild(QPushButton, 'moveZPT1CaliberateButton')
        self.moveZMT1CaliberateButton = self.findChild(QPushButton, 'moveZMT1CaliberateButton')
        self.nozzleHeightStep1NextButton = self.findChild(QPushButton, 'nozzleHeightStep1NextButton')
        self.nozzleHeightStep1CancelButton = self.findChild(QPushButton, 'nozzleHeightStep1CancelButton')
        self.quickStep1NextButton = self.findChild(QPushButton, 'quickStep1NextButton')
        self.quickStep1CancelButton = self.findChild(QPushButton, 'quickStep1CancelButton')
        self.quickStep2NextButton = self.findChild(QPushButton, 'quickStep2NextButton')
        self.quickStep2CancelButton = self.findChild(QPushButton, 'quickStep2CancelButton')
        self.quickStep3NextButton = self.findChild(QPushButton, 'quickStep3NextButton')
        self.quickStep3CancelButton = self.findChild(QPushButton, 'quickStep3CancelButton')
        self.quickStep4NextButton = self.findChild(QPushButton, 'quickStep4NextButton')
        self.quickStep4CancelButton = self.findChild(QPushButton, 'quickStep4CancelButton')

        # Find pages by their object names
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        self.nozzleHeightStep1Page = self.findChild(QWidget, 'nozzleHeightStep1Page')
        self.quickStep1Page = self.findChild(QWidget, 'quickStep1Page')
        self.quickStep2Page = self.findChild(QWidget, 'quickStep2Page')
        self.quickStep3Page = self.findChild(QWidget, 'quickStep3Page')
        self.quickStep4Page = self.findChild(QWidget, 'quickStep4Page')

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions - with safety checks
        self._connect_buttons()

        # Set the default screen to nozzleHeightStep1Page
        if self.stackedWidget and self.nozzleHeightStep1Page:
            self.stackedWidget.setCurrentWidget(self.nozzleHeightStep1Page)

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Group widgets for better reporting
        pages = {
            "stackedWidget": self.stackedWidget,
            "nozzleHeightStep1Page": self.nozzleHeightStep1Page,
            "quickStep1Page": self.quickStep1Page,
            "quickStep2Page": self.quickStep2Page,
            "quickStep3Page": self.quickStep3Page,
            "quickStep4Page": self.quickStep4Page
        }
        check_ui_elements(self, pages, "BedLeveling - Pages")
        
        step1_buttons = {
            "moveZPT1CaliberateButton": self.moveZPT1CaliberateButton,
            "moveZMT1CaliberateButton": self.moveZMT1CaliberateButton,
            "nozzleHeightStep1NextButton": self.nozzleHeightStep1NextButton,
            "nozzleHeightStep1CancelButton": self.nozzleHeightStep1CancelButton
        }
        check_ui_elements(self, step1_buttons, "BedLeveling - Step 1 Buttons")
        
        quick_step_buttons = {
            "quickStep1NextButton": self.quickStep1NextButton,
            "quickStep1CancelButton": self.quickStep1CancelButton,
            "quickStep2NextButton": self.quickStep2NextButton,
            "quickStep2CancelButton": self.quickStep2CancelButton,
            "quickStep3NextButton": self.quickStep3NextButton,
            "quickStep3CancelButton": self.quickStep3CancelButton,
            "quickStep4NextButton": self.quickStep4NextButton,
            "quickStep4CancelButton": self.quickStep4CancelButton
        }
        check_ui_elements(self, quick_step_buttons, "BedLeveling - Quick Step Buttons")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        if self.moveZPT1CaliberateButton:
            self.moveZPT1CaliberateButton.clicked.connect(self.move_z_pt1)

        if self.moveZMT1CaliberateButton:
            self.moveZMT1CaliberateButton.clicked.connect(self.move_z_mt1)

        if self.nozzleHeightStep1NextButton:
            self.nozzleHeightStep1NextButton.clicked.connect(self.go_to_quick_step1)

        if self.nozzleHeightStep1CancelButton:
            self.nozzleHeightStep1CancelButton.clicked.connect(self.cancel_bed_leveling)

        if self.quickStep1NextButton:
            self.quickStep1NextButton.clicked.connect(self.go_to_quick_step2)

        if self.quickStep1CancelButton:
            self.quickStep1CancelButton.clicked.connect(self.cancel_bed_leveling)

        if self.quickStep2NextButton:
            self.quickStep2NextButton.clicked.connect(self.go_to_quick_step3)

        if self.quickStep2CancelButton:
            self.quickStep2CancelButton.clicked.connect(self.cancel_bed_leveling)

        if self.quickStep3NextButton:
            self.quickStep3NextButton.clicked.connect(self.go_to_quick_step4)

        if self.quickStep3CancelButton:
            self.quickStep3CancelButton.clicked.connect(self.cancel_bed_leveling)

        if self.quickStep4NextButton:
            self.quickStep4NextButton.clicked.connect(self.finish_bed_leveling)

        if self.quickStep4CancelButton:
            self.quickStep4CancelButton.clicked.connect(self.cancel_bed_leveling)

    def move_z_pt1(self):
        """Logic to move Z-axis to PT1."""
        print("Move Z-axis to PT1 button clicked")

    def move_z_mt1(self):
        """Logic to move Z-axis to MT1."""
        print("Move Z-axis to MT1 button clicked")

    def go_to_quick_step1(self):
        """Navigate to Quick Step 1."""
        print("Navigating to Quick Step 1")
        if self.stackedWidget and self.quickStep1Page:
            self.stackedWidget.setCurrentWidget(self.quickStep1Page)

    def go_to_quick_step2(self):
        """Navigate to Quick Step 2."""
        print("Navigating to Quick Step 2")
        if self.stackedWidget and self.quickStep2Page:
            self.stackedWidget.setCurrentWidget(self.quickStep2Page)

    def go_to_quick_step3(self):
        """Navigate to Quick Step 3."""
        print("Navigating to Quick Step 3")
        if self.stackedWidget and self.quickStep3Page:
            self.stackedWidget.setCurrentWidget(self.quickStep3Page)

    def go_to_quick_step4(self):
        """Navigate to Quick Step 4."""
        print("Navigating to Quick Step 4")
        if self.stackedWidget and self.quickStep4Page:
            self.stackedWidget.setCurrentWidget(self.quickStep4Page)

    def finish_bed_leveling(self):
        """Finish bed leveling process."""
        print("Bed leveling process finished")
        self.main_window.switch_to_previous_screen()

    def cancel_bed_leveling(self):
        """Cancel bed leveling process."""
        print("Bed leveling process canceled")
        self.main_window.switch_to_previous_screen()