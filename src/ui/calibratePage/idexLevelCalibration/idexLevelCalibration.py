from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget
from utils.helpers import check_ui_elements

class IdexLevelCalibration(QWidget):
    def __init__(self, main_window):
        super(IdexLevelCalibration, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibratePage/idexLevelCalibration/idexLevelCalibration.ui', self)
            print("IdexLevelCalibration UI loaded successfully")
        except Exception as e:
            print(f"Failed to load IdexLevelCalibration UI file: {e}")

        # Find buttons by their object names
        self.idexConfigStep1NextButton = self.findChild(QPushButton, 'idexConfigStep1NextButton')
        self.idexConfigStep1CancelButton = self.findChild(QPushButton, 'idexConfigStep1CancelButton')
        self.idexConfigStep2NextButton = self.findChild(QPushButton, 'idexConfigStep2NextButton')
        self.idexConfigStep2CancelButton = self.findChild(QPushButton, 'idexConfigStep2CancelButton')
        self.idexConfigStep3NextButton = self.findChild(QPushButton, 'idexConfigStep3NextButton')
        self.idexConfigStep3CancelButton = self.findChild(QPushButton, 'idexConfigStep3CancelButton')
        self.idexConfigStep4NextButton = self.findChild(QPushButton, 'idexConfigStep4NextButton')
        self.idexConfigStep4CancelButton = self.findChild(QPushButton, 'idexConfigStep4CancelButton')
        self.idexConfigStep5NextButton = self.findChild(QPushButton, 'idexConfigStep5NextButton')
        self.idexConfigStep5CancelButton = self.findChild(QPushButton, 'idexConfigStep5CancelButton')

        # Find pages by their object names
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        self.idexConfigStep1Page = self.findChild(QWidget, 'idexConfigStep1Page')
        self.idexConfigStep2Page = self.findChild(QWidget, 'idexConfigStep2Page')
        self.idexConfigStep3Page = self.findChild(QWidget, 'idexConfigStep3Page')
        self.idexConfigStep4Page = self.findChild(QWidget, 'idexConfigStep4Page')
        self.idexConfigStep5Page = self.findChild(QWidget, 'idexConfigStep5Page')

        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()

        # Connect buttons to their respective functions - with safety checks
        self._connect_buttons()

        # Set the default screen to idexConfigStep1Page
        if self.stackedWidget and self.idexConfigStep1Page:
            self.stackedWidget.setCurrentWidget(self.idexConfigStep1Page)

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Group widgets for better reporting
        pages = {
            "stackedWidget": self.stackedWidget,
            "idexConfigStep1Page": self.idexConfigStep1Page,
            "idexConfigStep2Page": self.idexConfigStep2Page,
            "idexConfigStep3Page": self.idexConfigStep3Page,
            "idexConfigStep4Page": self.idexConfigStep4Page,
            "idexConfigStep5Page": self.idexConfigStep5Page
        }
        check_ui_elements(self, pages, "IdexLevelCalibration - Pages")
        
        step1_buttons = {
            "idexConfigStep1NextButton": self.idexConfigStep1NextButton,
            "idexConfigStep1CancelButton": self.idexConfigStep1CancelButton
        }
        check_ui_elements(self, step1_buttons, "IdexLevelCalibration - Step 1 Buttons")
        
        step2_buttons = {
            "idexConfigStep2NextButton": self.idexConfigStep2NextButton,
            "idexConfigStep2CancelButton": self.idexConfigStep2CancelButton
        }
        check_ui_elements(self, step2_buttons, "IdexLevelCalibration - Step 2 Buttons")
        
        step3_buttons = {
            "idexConfigStep3NextButton": self.idexConfigStep3NextButton,
            "idexConfigStep3CancelButton": self.idexConfigStep3CancelButton
        }
        check_ui_elements(self, step3_buttons, "IdexLevelCalibration - Step 3 Buttons")
        
        step4_buttons = {
            "idexConfigStep4NextButton": self.idexConfigStep4NextButton,
            "idexConfigStep4CancelButton": self.idexConfigStep4CancelButton
        }
        check_ui_elements(self, step4_buttons, "IdexLevelCalibration - Step 4 Buttons")
        
        step5_buttons = {
            "idexConfigStep5NextButton": self.idexConfigStep5NextButton,
            "idexConfigStep5CancelButton": self.idexConfigStep5CancelButton
        }
        check_ui_elements(self, step5_buttons, "IdexLevelCalibration - Step 5 Buttons")
    
    def _connect_buttons(self):
        """Connect buttons with safety checks"""
        if self.idexConfigStep1NextButton:
            self.idexConfigStep1NextButton.clicked.connect(self.go_to_step2)
        
        if self.idexConfigStep1CancelButton:
            self.idexConfigStep1CancelButton.clicked.connect(self.cancel_calibration)
        
        if self.idexConfigStep2NextButton:
            self.idexConfigStep2NextButton.clicked.connect(self.go_to_step3)
        
        if self.idexConfigStep2CancelButton:
            self.idexConfigStep2CancelButton.clicked.connect(self.cancel_calibration)
        
        if self.idexConfigStep3NextButton:
            self.idexConfigStep3NextButton.clicked.connect(self.go_to_step4)
        
        if self.idexConfigStep3CancelButton:
            self.idexConfigStep3CancelButton.clicked.connect(self.cancel_calibration)
        
        if self.idexConfigStep4NextButton:
            self.idexConfigStep4NextButton.clicked.connect(self.go_to_step5)
        
        if self.idexConfigStep4CancelButton:
            self.idexConfigStep4CancelButton.clicked.connect(self.cancel_calibration)
        
        if self.idexConfigStep5NextButton:
            self.idexConfigStep5NextButton.clicked.connect(self.finish_calibration)
        
        if self.idexConfigStep5CancelButton:
            self.idexConfigStep5CancelButton.clicked.connect(self.cancel_calibration)

    def go_to_step2(self):
        """Navigate to Step 2."""
        print("Navigating to Step 2")
        if self.stackedWidget and self.idexConfigStep2Page:
            self.stackedWidget.setCurrentWidget(self.idexConfigStep2Page)

    def go_to_step3(self):
        """Navigate to Step 3."""
        print("Navigating to Step 3")
        if self.stackedWidget and self.idexConfigStep3Page:
            self.stackedWidget.setCurrentWidget(self.idexConfigStep3Page)

    def go_to_step4(self):
        """Navigate to Step 4."""
        print("Navigating to Step 4")
        if self.stackedWidget and self.idexConfigStep4Page:
            self.stackedWidget.setCurrentWidget(self.idexConfigStep4Page)

    def go_to_step5(self):
        """Navigate to Step 5."""
        print("Navigating to Step 5")
        if self.stackedWidget and self.idexConfigStep5Page:
            self.stackedWidget.setCurrentWidget(self.idexConfigStep5Page)

    def finish_calibration(self):
        """Finish the IDEX calibration process."""
        print("IDEX Calibration process finished")
        self.main_window.switch_to_previous_screen()

    def cancel_calibration(self):
        """Cancel the IDEX calibration process."""
        print("IDEX Calibration process canceled")
        if self.stackedWidget:
            self.stackedWidget.setCurrentIndex(0)
        self.main_window.switch_to_previous_screen()