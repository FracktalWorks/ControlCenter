from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QListWidget, QLabel, QToolButton
from utils.helpers import check_ui_elements

class PrintFromLocation(QWidget):
    def __init__(self, main_window):
        super(PrintFromLocation, self).__init__()
        self.main_window = main_window

        # Load the .ui file
        try:
            uic.loadUi('src/ui/print_from_location/print_from_location.ui', self)
            print("PrintFromLocation UI loaded successfully")
        except Exception as e:
            print(f"Failed to load PrintFromLocation UI file: {e}")

        # Find buttons by their object names - USB storage
        self.USBStorageBackButton = self.findChild(QPushButton, 'USBStorageBackButton')
        self.USBStorageScrollDown = self.findChild(QPushButton, 'USBStorageScrollDown')
        self.USBStorageScrollUp = self.findChild(QPushButton, 'USBStorageScrollUp')
        self.USBStorageSelectButton = self.findChild(QPushButton, 'USBStorageSelectButton')
        self.USBStorageSaveButton = self.findChild(QPushButton, 'USBStorageSaveButton')
        
        # Find buttons by their object names - local storage
        self.localStorageBackButton = self.findChild(QPushButton, 'localStorageBackButton')
        self.localStorageScrollDown = self.findChild(QPushButton, 'localStorageScrollDown')
        self.localStorageScrollUp = self.findChild(QPushButton, 'localStorageScrollUp')
        self.localStorageSelectButton = self.findChild(QPushButton, 'localStorageSelectButton')
        self.localStorageDeleteButton = self.findChild(QPushButton, 'localStorageDeleteButton')
        
        # Location selection buttons
        self.fromUsbButton = self.findChild(QPushButton, 'fromUsbButton')
        self.fromLocalButton = self.findChild(QPushButton, 'fromLocalButton')
        self.printLocationScreenBackButton = self.findChild(QPushButton, 'printLocationScreenBackButton')
        
        # Selected file buttons - USB
        self.fileSelectedUSBPrintButton = self.findChild(QToolButton, 'fileSelectedUSBPrintButton')
        self.fileSelectedUSBTransferButton = self.findChild(QToolButton, 'fileSelectedUSBTransferButton')
        self.fileSelectedUSBBackButton = self.findChild(QPushButton, 'fileSelectedUSBBackButton')
        
        # Selected file buttons - Local
        self.fileSelectedPrintButton = self.findChild(QPushButton, 'fileSelectedPrintButton')
        self.fileSelectedBackButton = self.findChild(QPushButton, 'fileSelectedBackButton')

        # Find other UI elements
        self.fileListWidget = self.findChild(QListWidget, 'fileListWidget')  # Local files
        self.fileListWidgetUSB = self.findChild(QListWidget, 'fileListWidgetUSB')  # USB files
        self.fileSelectedName = self.findChild(QLabel, 'fileSelectedName')  # Local file name
        self.fileSelectedUSBName = self.findChild(QLabel, 'fileSelectedUSBName')  # USB file name
        self.printPreviewSelected = self.findChild(QLabel, 'printPreviewSelected')  # Local preview
        self.printPreviewSelectedUSB = self.findChild(QLabel, 'printPreviewSelectedUSB')  # USB preview

        # Find stacked widget and pages
        self.stackedWidget = self.findChild(QStackedWidget, 'stackedWidget')
        self.fileListLocalPage = self.findChild(QWidget, 'fileListLocalPage')
        self.fileListUSBPage = self.findChild(QWidget, 'fileListUSBPage')
        self.printLocationPage = self.findChild(QWidget, 'printLocationPage')
        self.printSelectedLocalPage = self.findChild(QWidget, 'printSelectedLocalPage')
        self.printSelectedUSBPage = self.findChild(QWidget, 'printSelectedUSBPage')
        
        # Check for critical widget existence
        self._check_widgets_existence()

        # Connect all button signals with safety checks
        self._connect_buttons()

        # Set the default screen to printLocationPage if it exists
        if self.stackedWidget and self.printLocationPage:
            self.stackedWidget.setCurrentWidget(self.printLocationPage)

    def _check_widgets_existence(self):
        """Check if critical widgets were found and print warnings for missing ones"""
        # Use the helper function to check and report missing widgets
        # Group widgets logically for better reporting
        
        # Check main pages and container widgets
        main_widgets = {
            "stackedWidget": self.stackedWidget,
            "printLocationPage": self.printLocationPage,
            "fileListLocalPage": self.fileListLocalPage,
            "fileListUSBPage": self.fileListUSBPage, 
            "printSelectedLocalPage": self.printSelectedLocalPage,
            "printSelectedUSBPage": self.printSelectedUSBPage
        }
        check_ui_elements(self, main_widgets, "PrintFromLocation - Main Widgets")
        
        # Check local storage related buttons
        local_storage_buttons = {
            "localStorageBackButton": self.localStorageBackButton,
            "localStorageScrollDown": self.localStorageScrollDown,
            "localStorageScrollUp": self.localStorageScrollUp,
            "localStorageSelectButton": self.localStorageSelectButton,
            "localStorageDeleteButton": self.localStorageDeleteButton
        }
        check_ui_elements(self, local_storage_buttons, "PrintFromLocation - Local Storage Buttons")
        
        # Check USB storage related buttons
        usb_storage_buttons = {
            "USBStorageBackButton": self.USBStorageBackButton,
            "USBStorageScrollDown": self.USBStorageScrollDown,
            "USBStorageScrollUp": self.USBStorageScrollUp,
            "USBStorageSelectButton": self.USBStorageSelectButton,
            "USBStorageSaveButton": self.USBStorageSaveButton
        }
        check_ui_elements(self, usb_storage_buttons, "PrintFromLocation - USB Storage Buttons")
        
        # Check location selection buttons
        location_buttons = {
            "fromUsbButton": self.fromUsbButton,
            "fromLocalButton": self.fromLocalButton,
            "printLocationScreenBackButton": self.printLocationScreenBackButton
        }
        check_ui_elements(self, location_buttons, "PrintFromLocation - Location Selection Buttons")
        
        # Check list widgets and other UI elements
        list_widgets = {
            "fileListWidget": self.fileListWidget,
            "fileListWidgetUSB": self.fileListWidgetUSB,
            "fileSelectedName": self.fileSelectedName,
            "fileSelectedUSBName": self.fileSelectedUSBName, 
            "printPreviewSelected": self.printPreviewSelected,
            "printPreviewSelectedUSB": self.printPreviewSelectedUSB
        }
        check_ui_elements(self, list_widgets, "PrintFromLocation - List Widgets and Labels")
        
        # Check file selection related buttons
        file_selection_buttons = {
            "fileSelectedPrintButton": self.fileSelectedPrintButton,
            "fileSelectedBackButton": self.fileSelectedBackButton,
            "fileSelectedUSBPrintButton": self.fileSelectedUSBPrintButton,
            "fileSelectedUSBTransferButton": self.fileSelectedUSBTransferButton,
            "fileSelectedUSBBackButton": self.fileSelectedUSBBackButton
        }
        check_ui_elements(self, file_selection_buttons, "PrintFromLocation - File Selection Buttons")

    def _connect_buttons(self):
        """Connect all button signals with safety checks to prevent NoneType errors"""
        # Connect buttons for USB storage navigation
        if self.USBStorageBackButton and self.stackedWidget and self.printLocationPage:
            self.USBStorageBackButton.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.printLocationPage))
        
        if self.USBStorageScrollDown and self.fileListWidgetUSB:
            self.USBStorageScrollDown.clicked.connect(lambda: self.fileListWidgetUSB.setCurrentRow(self.fileListWidgetUSB.currentRow() + 1))
        
        if self.USBStorageScrollUp and self.fileListWidgetUSB:
            self.USBStorageScrollUp.clicked.connect(lambda: self.fileListWidgetUSB.setCurrentRow(self.fileListWidgetUSB.currentRow() - 1))
        
        if self.USBStorageSelectButton:
            self.USBStorageSelectButton.clicked.connect(self.printSelectedUSB)
        
        if self.USBStorageSaveButton:
            self.USBStorageSaveButton.clicked.connect(self.transferToLocal)
        
        # Connect buttons for local storage navigation
        if self.localStorageBackButton and self.stackedWidget and self.printLocationPage:
            self.localStorageBackButton.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.printLocationPage))
        elif self.localStorageBackButton:
            print("Using fallback for localStorageBackButton")
            self.localStorageBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
            
        if self.localStorageScrollDown and self.fileListWidget:
            self.localStorageScrollDown.clicked.connect(lambda: self.fileListWidget.setCurrentRow(self.fileListWidget.currentRow() + 1))
        
        if self.localStorageScrollUp and self.fileListWidget:
            self.localStorageScrollUp.clicked.connect(lambda: self.fileListWidget.setCurrentRow(self.fileListWidget.currentRow() - 1))
        
        if self.localStorageSelectButton:
            self.localStorageSelectButton.clicked.connect(self.printSelectedLocal)
        
        if self.localStorageDeleteButton:
            self.localStorageDeleteButton.clicked.connect(self.deleteItem)
        
        # Connect location selection buttons
        if self.fromUsbButton:
            self.fromUsbButton.clicked.connect(self.fileListUSB)
        
        if self.fromLocalButton:
            self.fromLocalButton.clicked.connect(self.fileListLocal)
        
        if self.printLocationScreenBackButton:
            self.printLocationScreenBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        
        # Connect selected file buttons - USB
        if self.fileSelectedUSBPrintButton:
            self.fileSelectedUSBPrintButton.clicked.connect(self.printFile)
        
        if self.fileSelectedUSBTransferButton:
            self.fileSelectedUSBTransferButton.clicked.connect(self.transferToLocal)
        
        if self.fileSelectedUSBBackButton:
            self.fileSelectedUSBBackButton.clicked.connect(self.fileListUSB)
        
        # Connect selected file buttons - Local
        if self.fileSelectedPrintButton:
            self.fileSelectedPrintButton.clicked.connect(self.printFile)
        
        if self.fileSelectedBackButton:
            self.fileSelectedBackButton.clicked.connect(self.fileListLocal)

    def fileListLocal(self):
        """
        Shows the local file list screen and populates the list with local files
        """
        print("Showing local file list")
        if self.stackedWidget and self.fileListLocalPage:
            self.stackedWidget.setCurrentWidget(self.fileListLocalPage)
        # TODO: Populate file list from octoprint server

    def fileListUSB(self):
        """
        Shows the USB file list screen and populates the list with USB files
        """
        print("Showing USB file list")
        if self.stackedWidget and self.fileListUSBPage:
            self.stackedWidget.setCurrentWidget(self.fileListUSBPage)
        # TODO: Populate file list from USB drive

    def printSelectedLocal(self):
        """
        Displays the selected local file details before printing
        """
        print("Displaying selected local file")
        if self.fileListWidget and self.fileListWidget.currentItem():
            # TODO: Get file details and preview
            if self.stackedWidget and self.printSelectedLocalPage:
                self.stackedWidget.setCurrentWidget(self.printSelectedLocalPage)
        else:
            print("No file selected")

    def printSelectedUSB(self):
        """
        Displays the selected USB file details before printing
        """
        print("Displaying selected USB file")
        if self.fileListWidgetUSB and self.fileListWidgetUSB.currentItem():
            # TODO: Get file details and preview
            if self.stackedWidget and self.printSelectedUSBPage:
                self.stackedWidget.setCurrentWidget(self.printSelectedUSBPage)
        else:
            print("No file selected")

    def printFile(self):
        """
        Sends the selected file to printer and starts printing
        """
        print("Printing file")
        # TODO: Send file to printer and switch to the home screen to show print progress
        self.main_window.switch_to_home_screen()

    def deleteItem(self):
        """
        Deletes the selected local file
        """
        print("Deleting file")
        if self.fileListWidget and self.fileListWidget.currentItem():
            # TODO: Delete the selected file
            pass
        else:
            print("No file selected")

    def transferToLocal(self):
        """
        Transfers the selected USB file to local storage
        """
        print("Transferring file from USB to local storage")
        if self.fileListWidgetUSB and self.fileListWidgetUSB.currentItem():
            # TODO: Copy the file from USB to local storage
            pass
        else:
            print("No file selected")