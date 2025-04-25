from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget

class BedLeveling(QWidget):
    def __init__(self, main_window):
        super(BedLeveling, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/calibratePage/bedLevelingPage/bedLevelingPage.ui', self)
            print("UI file loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

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

        # Check if buttons and pages are found
        if not all([self.stackedWidget, self.moveZPT1CaliberateButton, self.moveZMT1CaliberateButton, self.nozzleHeightStep1NextButton, self.nozzleHeightStep1CancelButton,
                        self.quickStep1NextButton,self.quickStep1CancelButton, self.quickStep2NextButton, self.quickStep2CancelButton, 
                        self. quickStep3NextButton, self.quickStep3CancelButton, self.quickStep4NextButton, self. quickStep4CancelButton,
                        self.nozzleHeightStep1Page, self.quickStep1Page, self.quickStep2Page,
                        self.quickStep3Page, self.quickStep4Page]):
            raise ValueError("One or more buttons or pages not found in the UI file")

        # Connect buttons to their respective functions
        self.moveZPT1CaliberateButton.clicked.connect(self.)
        self.moveZMT1CaliberateButton.clicked.connect(self.)
        self.nozzleHeightStep1NextButton.clicked.connect(self.)
        self.nozzleHeightStep1CancelButton.clicked.connect(self.)
        self.quickStep1NextButton.clicked.connect(self.)
        self.quickStep1CancelButton.clicked.connect(self.)
        self.quickStep2NextButton.clicked.connect(self.)
        self.quickStep2CancelButton.clicked.connect(self.)
        self.quickStep3NextButton.clicked.connect(self.)
        self.quickStep3CancelButton.clicked.connect(self.)
        self.quickStep4NextButton.clicked.connect(self.)
        self.quickStep4CancelButton.clicked.connect(self.)


        # Set the default screen to levelingPage
        self.stackedWidget.setCurrentWidget(self.nozzleHeightStep1Page)

    def start_bed_leveling(self):
        # Placeholder for starting bed leveling logic
        print("Start Bed Leveling button clicked")
        self.stackedWidget.setCurrentWidget(self.confirmationPage)

    def cancel_bed_leveling(self):
        # Placeholder for cancel bed leveling logic
        print("Cancel Bed Leveling button clicked")
        self.stackedWidget.setCurrentWidget(self.levelingPage)