from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget

class IdexLevelCalibration(QWidget):
    def __init__(self, main_window):
        super(IdexLevelCalibration, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibratePage/idexLevelCalibration/idexLevelCalibration.ui', self)
            print("UI file loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

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

        # Check if buttons and pages are found
        if not all([
            self.stackedWidget, self.idexConfigStep1Page, self.idexConfigStep2Page, self.idexConfigStep3Page,
            self.idexConfigStep4Page, self.idexConfigStep5Page, self.idexConfigStep1NextButton, self.idexConfigStep1CancelButton,
            self.idexConfigStep2NextButton, self.idexConfigStep2CancelButton, self.idexConfigStep3NextButton, self.idexConfigStep3CancelButton,
            self.idexConfigStep4NextButton, self.idexConfigStep4CancelButton, self.idexConfigStep5NextButton, self.idexConfigStep5CancelButton
        ]):
            raise ValueError("One or more buttons or pages not found in the UI file")

        # Connect buttons to their respective functions
        self.idexConfigStep1NextButton.clicked.connect(self.go_to_step2)
        self.idexConfigStep1CancelButton.clicked.connect(self.cancel_calibration)
        self.idexConfigStep2NextButton.clicked.connect(self.go_to_step3)
        self.idexConfigStep2CancelButton.clicked.connect(self.cancel_calibration)
        self.idexConfigStep3NextButton.clicked.connect(self.go_to_step4)
        self.idexConfigStep3CancelButton.clicked.connect(self.cancel_calibration)
        self.idexConfigStep4NextButton.clicked.connect(self.go_to_step5)
        self.idexConfigStep4CancelButton.clicked.connect(self.cancel_calibration)
        self.idexConfigStep5NextButton.clicked.connect(self.finish_calibration)
        self.idexConfigStep5CancelButton.clicked.connect(self.cancel_calibration)

        # Set the default screen to idexConfigStep1Page
        self.stackedWidget.setCurrentWidget(self.idexConfigStep1Page)

    def go_to_step2(self):
        """Navigate to Step 2."""
        print("Navigating to Step 2")
        self.stackedWidget.setCurrentWidget(self.idexConfigStep2Page)

    def go_to_step3(self):
        """Navigate to Step 3."""
        print("Navigating to Step 3")
        self.stackedWidget.setCurrentWidget(self.idexConfigStep3Page)

    def go_to_step4(self):
        """Navigate to Step 4."""
        print("Navigating to Step 4")
        self.stackedWidget.setCurrentWidget(self.idexConfigStep4Page)

    def go_to_step5(self):
        """Navigate to Step 5."""
        print("Navigating to Step 5")
        self.stackedWidget.setCurrentWidget(self.idexConfigStep5Page)

    def finish_calibration(self):
        """Finish the IDEX calibration process."""
        print("IDEX Calibration process finished")
        self.main_window.switch_to_previous_screen()

    def cancel_calibration(self):
        """Cancel the IDEX calibration process."""
        print("IDEX Calibration process canceled")
        self.main_window.switch_to_previous_screen()