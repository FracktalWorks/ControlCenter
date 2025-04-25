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
        self.idexConfigStep1CancelButton = self.findChild(QPushButton, 'indexConfigStep1CancelButton')
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
        if not all([self.stackedWidget, self.idexConfigStep1Page, self.idexConfigStep2Page, self.idexConfigStep3Page,
                        self.idexConfigStep4Page, self.idexConfigStep5Page, self.idexConfigStep1NextButton, self.idexConfigStep1CancelButton,
                        self.idexConfigStep2NextButton, self.idexConfigStep2CancelButton, self.idexConfigStep3NextButton, self.idexConfigStep3CancelButton,
                        self.idexConfigStep4NextButton, self.idexConfigStep4CancelButton, self.idexConfigStep5NextButton, self.idexConfigStep5CancelButton]):
            raise ValueError("One or more buttons or pages not found in the UI file")

        # Connect buttons to their respective functions
        self.startCalibrationButton.clicked.connect(self.start_idex_calibration)
        self.cancelCalibrationButton.clicked.connect(self.cancel_idex_calibration)
        self.backButton.clicked.connect(self.main_window.switch_to_previous_screen)

        # Set the default screen to calibrationPage
        self.stackedWidget.setCurrentWidget(self.calibrationPage)

    def start_idex_calibration(self):
        # Placeholder for starting IDEX calibration logic
        print("Start IDEX Calibration button clicked")
        self.stackedWidget.setCurrentWidget(self.confirmationPage)

    def cancel_idex_calibration(self):
        # Placeholder for cancel IDEX calibration logic
        print("Cancel IDEX Calibration button clicked")
        self.stackedWidget.setCurrentWidget(self.calibrationPage)