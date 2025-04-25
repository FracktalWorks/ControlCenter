from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QListWidget, QLabel, QToolButton

class PrintFromLocation(QWidget):
    def __init__(self, main_window):
        super(PrintFromLocation, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/print_from_location/print_from_location.ui', self)
            print("UI file loaded successfully")
        except Exception as e:
            print(f"Failed to load UI file: {e}")

        # Find buttons by their object names
        self.backButton = self.findChild(QPushButton, 'USBStorageBackButton')
        self.scrollDownButton = self.findChild(QPushButton, 'USBStorageScrollDown')
        self.scrollUpButton = self.findChild(QPushButton, 'USBStorageScrollUp')
        self.selectButton = self.findChild(QPushButton, 'USBStorageSelectButton')
        self.saveButton = self.findChild(QPushButton, 'USBStorageSaveButton')
        self.fromUsbButton = self.findChild(QPushButton, 'fromUsbButton')
        self.fromLocalButton = self.findChild(QPushButton, 'fromLocalButton')
        self.printLocationScreenBackButton = self.findChild(QPushButton, 'printLocationScreenBackButton')
        self.fileSelectedUSBPrintButton = self.findChild(QToolButton, 'fileSelectedUSBPrintButton')
        self.fileSelectedUSBTransferButton = self.findChild(QToolButton, 'fileSelectedUSBTransferButton')
        self.fileSelectedUSBBackButton = self.findChild(QPushButton, 'fileSelectedUSBBackButton')
        self.USBStorageDeleteButton = self.findChild(QPushButton, 'USBStorageDeleteButton')
        self.fileSelectedPrintButton = self.findChild(QPushButton, 'fileSelectedPrintButton')
        self.fileSelectedBackButton = self.findChild(QPushButton, 'fileSelectedBackButton')

        # Find other UI elements
        self.fileListWidgetUSB = self.findChild(QListWidget, 'fileListWidgetUSB')
        self.fileSelectedUSBName = self.findChild(QLabel, 'fileSelectedUSBName')
        self.printPreviewSelectedUSB = self.findChild(QLabel, 'printPreviewSelectedUSB')

        # Find stacked widget and pages
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        self.fileListLocalPage = self.findChild(QWidget, 'fileListLocalPage')
        self.fileListUSBPage = self.findChild(QWidget, 'fileListUSBPage')
        self.printLocationPage = self.findChild(QWidget, 'printLocationPage')
        self.printSelectedLocalPage = self.findChild(QWidget, 'printSelectedLocalPage')
        self.printSelectedUSBPage = self.findChild(QWidget, 'printSelectedUSBPage')

        # Check if all elements are found
        if not all([
            self.backButton, self.scrollDownButton, self.scrollUpButton, self.selectButton, self.saveButton,
            self.fromUsbButton, self.fromLocalButton, self.printLocationScreenBackButton,
            self.fileSelectedUSBPrintButton, self.fileSelectedUSBTransferButton, self.fileSelectedUSBBackButton,
            self.fileListWidgetUSB, self.fileSelectedUSBName, self.printPreviewSelectedUSB,
            self.stackedWidget, self.fileListLocalPage, self.printLocationPage, self.printSelectedUSBPage
        ]):
            raise ValueError("One or more UI elements not found in the UI file")

        # Connect buttons to their respective functions
        self.backButton.clicked.connect(self.main_window.switch_to_previous_screen)
        self.scrollDownButton.clicked.connect(self.scroll_down)
        self.scrollUpButton.clicked.connect(self.scroll_up)
        self.selectButton.clicked.connect(self.select_file)
        self.saveButton.clicked.connect(self.save_file)
        self.fromUsbButton.clicked.connect(self.show_usb_files)
        self.fromLocalButton.clicked.connect(self.show_local_files)
        self.printLocationScreenBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        self.fileSelectedUSBPrintButton.clicked.connect(self.print_selected_file)
        self.fileSelectedUSBTransferButton.clicked.connect(self.transfer_selected_file)
        self.fileSelectedUSBBackButton.clicked.connect(self.go_back_to_file_list)

        # Set the default screen to printLocationPage
        self.stackedWidget.setCurrentWidget(self.printLocationPage)

    def scroll_down(self):
        """Scroll down the file list."""
        print("Scrolling down the file list")

    def scroll_up(self):
        """Scroll up the file list."""
        print("Scrolling up the file list")

    def select_file(self):
        """Select a file from the list."""
        print("File selected")
        self.stackedWidget.setCurrentWidget(self.printSelectedUSBPage)

    def save_file(self):
        """Save the selected file."""
        print("File saved")

    def show_usb_files(self):
        """Show files from USB storage."""
        print("Showing USB files")
        self.stackedWidget.setCurrentWidget(self.fileListLocalPage)

    def show_local_files(self):
        """Show files from local storage."""
        print("Showing local files")
        self.stackedWidget.setCurrentWidget(self.fileListLocalPage)

    def print_selected_file(self):
        """Print the selected file."""
        print("Printing the selected file")

    def transfer_selected_file(self):
        """Transfer the selected file."""
        print("Transferring the selected file")

    def go_back_to_file_list(self):
        """Go back to the file list."""
        print("Going back to the file list")
        self.stackedWidget.setCurrentWidget(self.fileListLocalPage)