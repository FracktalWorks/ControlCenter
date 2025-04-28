from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QListWidget, QLabel, QToolButton
from utils.helpers import check_ui_elements
from utils.logger import setup_logger

class PrintFromLocation(QWidget):
    def __init__(self, main_window):
        """Initialize the PrintFromLocation screen with all UI components and connections."""
        super(PrintFromLocation, self).__init__()
        self.main_window = main_window
        
        # Setup logger
        self.logger = setup_logger('PrintFromLocation')
        self.logger.info("Initializing PrintFromLocation screen")

        # Load the UI file with proper error handling
        try:
            uic.loadUi('src/ui/print_from_location/print_from_location.ui', self)
            self.logger.info("PrintFromLocation UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load PrintFromLocation UI file: {e}")
            return
        
        # Initialize UI components directly
        self.logger.debug("Initializing UI components")
        
        # Main container widget
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        
        # Pages for stacked widget
        self.printLocationPage = self.findChild(QWidget, "printLocationPage")
        self.fileListLocalPage = self.findChild(QWidget, "fileListLocalPage")
        self.fileListUSBPage = self.findChild(QWidget, "fileListUSBPage")
        self.printSelectedLocalPage = self.findChild(QWidget, "printSelectedLocalPage")
        self.printSelectedUSBPage = self.findChild(QWidget, "printSelectedUSBPage")
        
        # USB storage related buttons
        self.USBStorageBackButton = self.findChild(QPushButton, "USBStorageBackButton")
        self.USBStorageScrollDown = self.findChild(QPushButton, "USBStorageScrollDown")
        self.USBStorageScrollUp = self.findChild(QPushButton, "USBStorageScrollUp")
        self.USBStorageSelectButton = self.findChild(QPushButton, "USBStorageSelectButton")
        self.USBStorageSaveButton = self.findChild(QPushButton, "USBStorageSaveButton")
        
        # Local storage related buttons
        self.localStorageBackButton = self.findChild(QPushButton, "localStorageBackButton")
        self.localStorageScrollDown = self.findChild(QPushButton, "localStorageScrollDown")
        self.localStorageScrollUp = self.findChild(QPushButton, "localStorageScrollUp")
        self.localStorageSelectButton = self.findChild(QPushButton, "localStorageSelectButton")
        self.localStorageDeleteButton = self.findChild(QPushButton, "localStorageDeleteButton")
        
        # Location selection buttons
        self.fromUsbButton = self.findChild(QPushButton, "fromUsbButton")
        self.fromLocalButton = self.findChild(QPushButton, "fromLocalButton")
        self.printLocationScreenBackButton = self.findChild(QPushButton, "printLocationScreenBackButton")
        
        # Selected file buttons - USB
        self.fileSelectedUSBPrintButton = self.findChild(QToolButton, "fileSelectedUSBPrintButton")
        self.fileSelectedUSBTransferButton = self.findChild(QToolButton, "fileSelectedUSBTransferButton")
        self.fileSelectedUSBBackButton = self.findChild(QPushButton, "fileSelectedUSBBackButton")
        
        # Selected file buttons - Local
        self.fileSelectedLocalPrintButton = self.findChild(QToolButton, "fileSelectedLocalPrintButton")
        self.fileSelectedLocalBackButton = self.findChild(QPushButton, "fileSelectedLocalBackButton")
        
        # List widgets
        self.fileListWidgetLocal = self.findChild(QListWidget, "fileListWidgetLocal")
        self.fileListWidgetUSB = self.findChild(QListWidget, "fileListWidgetUSB")
        
        # Preview and info labels
        self.fileSelectedLocalName = self.findChild(QLabel, "fileSelectedLocalName")
        self.fileSelectedUSBName = self.findChild(QLabel, "fileSelectedUSBName")
        self.printPreviewSelectedLocal = self.findChild(QLabel, "printPreviewSelectedLocal")
        self.printPreviewSelectedUSB = self.findChild(QLabel, "printPreviewSelectedUSB")
        
        # Check all UI elements exist in one consolidated list
        check_ui_elements(self, [
            # Main container
            self.stackedWidget,
            
            # Pages
            self.printLocationPage, self.fileListLocalPage, self.fileListUSBPage,
            self.printSelectedLocalPage, self.printSelectedUSBPage,
            
            # USB storage buttons
            self.USBStorageBackButton, self.USBStorageScrollDown, self.USBStorageScrollUp,
            self.USBStorageSelectButton, self.USBStorageSaveButton,
            
            # Local storage buttons
            self.localStorageBackButton, self.localStorageScrollDown, self.localStorageScrollUp,
            self.localStorageSelectButton, self.localStorageDeleteButton,
            
            # Location selection buttons
            self.fromUsbButton, self.fromLocalButton, self.printLocationScreenBackButton,
            
            # USB file buttons
            self.fileSelectedUSBPrintButton, self.fileSelectedUSBTransferButton, self.fileSelectedUSBBackButton,
            
            # Local file buttons
            self.fileSelectedLocalPrintButton, self.fileSelectedLocalBackButton,
            
            # List widgets
            self.fileListWidgetLocal, self.fileListWidgetUSB,
            
            # Info labels
            self.fileSelectedLocalName, self.fileSelectedUSBName,
            self.printPreviewSelectedLocal, self.printPreviewSelectedUSB
        ], "PrintFromLocation - All UI Elements")
        
        # Connect all button signals with safety checks to prevent NoneType errors
        self.logger.debug("Connecting button signals")
        
        # USB storage navigation
        if self.USBStorageBackButton:
            self.USBStorageBackButton.clicked.connect(self._usb_storage_back)
        if self.USBStorageScrollDown:
            self.USBStorageScrollDown.clicked.connect(self._usb_scroll_down)
        if self.USBStorageScrollUp:
            self.USBStorageScrollUp.clicked.connect(self._usb_scroll_up)
        if self.USBStorageSelectButton:
            self.USBStorageSelectButton.clicked.connect(self.printSelectedUSB)
        if self.USBStorageSaveButton:
            self.USBStorageSaveButton.clicked.connect(self.transferToLocal)
        
        # Local storage navigation
        if self.localStorageBackButton:
            self.localStorageBackButton.clicked.connect(self._local_storage_back)
        if self.localStorageScrollDown:
            self.localStorageScrollDown.clicked.connect(self._local_scroll_down)
        if self.localStorageScrollUp:
            self.localStorageScrollUp.clicked.connect(self._local_scroll_up)
        if self.localStorageSelectButton:
            self.localStorageSelectButton.clicked.connect(self.printSelectedLocal)
        if self.localStorageDeleteButton:
            self.localStorageDeleteButton.clicked.connect(self.deleteItem)
        
        # Location selection buttons
        if self.fromUsbButton:
            self.fromUsbButton.clicked.connect(self.fileListUSB)
        if self.fromLocalButton:
            self.fromLocalButton.clicked.connect(self.fileListLocal)
        if self.printLocationScreenBackButton:
            self.printLocationScreenBackButton.clicked.connect(self.main_window.switch_to_previous_screen)
        
        # Selected file buttons - USB
        if self.fileSelectedUSBPrintButton:
            self.fileSelectedUSBPrintButton.clicked.connect(self.printFile)
        if self.fileSelectedUSBTransferButton:
            self.fileSelectedUSBTransferButton.clicked.connect(self.transferToLocal)
        if self.fileSelectedUSBBackButton:
            self.fileSelectedUSBBackButton.clicked.connect(self.fileListUSB)
        
        # Selected file buttons - Local
        if self.fileSelectedLocalPrintButton:
            self.fileSelectedLocalPrintButton.clicked.connect(self.printFile)
        if self.fileSelectedLocalBackButton:
            self.fileSelectedLocalBackButton.clicked.connect(self.fileListLocal)
        
        # Set the default screen to printLocationPage if it exists
        if self.stackedWidget and self.printLocationPage:
            self.stackedWidget.setCurrentWidget(self.printLocationPage)
            self.logger.info("Set initial page to printLocationPage")
        else:
            self.logger.warning("Could not set default page - required widgets missing")

    # Helper methods for button connections
    def _usb_storage_back(self):
        """Handle back button in USB storage page"""
        if self.stackedWidget and self.printLocationPage:
            self.stackedWidget.setCurrentWidget(self.printLocationPage)
            self.logger.info("USB Storage: going back to location selection")

    def _local_storage_back(self):
        """Handle back button in local storage page"""
        if self.stackedWidget and self.printLocationPage:
            self.stackedWidget.setCurrentWidget(self.printLocationPage)
            self.logger.info("Local Storage: going back to location selection")
        else:
            self.logger.warning("Using fallback for localStorageBackButton")
            self.main_window.switch_to_previous_screen()

    def _usb_scroll_down(self):
        """Handle scroll down in USB file list"""
        if self.fileListWidgetUSB:
            current_row = self.fileListWidgetUSB.currentRow()
            self.fileListWidgetUSB.setCurrentRow(current_row + 1)
            self.logger.info("USB Storage: scrolling down")

    def _usb_scroll_up(self):
        """Handle scroll up in USB file list"""
        if self.fileListWidgetUSB:
            current_row = self.fileListWidgetUSB.currentRow()
            self.fileListWidgetUSB.setCurrentRow(current_row - 1)
            self.logger.info("USB Storage: scrolling up")

    def _local_scroll_down(self):
        """Handle scroll down in local file list"""
        if self.fileListWidgetLocal:
            current_row = self.fileListWidgetLocal.currentRow()
            self.fileListWidgetLocal.setCurrentRow(current_row + 1)
            self.logger.info("Local Storage: scrolling down")

    def _local_scroll_up(self):
        """Handle scroll up in local file list"""
        if self.fileListWidgetLocal:
            current_row = self.fileListWidgetLocal.currentRow()
            self.fileListWidgetLocal.setCurrentRow(current_row - 1)
            self.logger.info("Local Storage: scrolling up")

    def fileListLocal(self):
        """Shows the local file list screen and populates the list with local files"""
        self.logger.info("Showing local file list")
        
        if self.stackedWidget and self.fileListLocalPage:
            self.stackedWidget.setCurrentWidget(self.fileListLocalPage)
            self.logger.info("Switched to local file list")
        # TODO: Populate file list from octoprint server

    def fileListUSB(self):
        """Shows the USB file list screen and populates the list with USB files"""
        self.logger.info("Showing USB file list")
        
        if self.stackedWidget and self.fileListUSBPage:
            self.stackedWidget.setCurrentWidget(self.fileListUSBPage)
            self.logger.info("Switched to USB file list")
        # TODO: Populate file list from USB drive

    def printSelectedLocal(self):
        """Displays the selected local file details before printing"""
        self.logger.info("Displaying selected local file")
        
        if self.fileListWidgetLocal and self.fileListWidgetLocal.currentItem():
            # TODO: Get file details and preview
            if self.stackedWidget and self.printSelectedLocalPage:
                self.stackedWidget.setCurrentWidget(self.printSelectedLocalPage)
                self.logger.info("Showing selected local file details")
        else:
            self.logger.warning("No file selected")

    def printSelectedUSB(self):
        """Displays the selected USB file details before printing"""
        self.logger.info("Displaying selected USB file")
        
        if self.fileListWidgetUSB and self.fileListWidgetUSB.currentItem():
            # TODO: Get file details and preview
            if self.stackedWidget and self.printSelectedUSBPage:
                self.stackedWidget.setCurrentWidget(self.printSelectedUSBPage)
                self.logger.info("Showing selected USB file details")
        else:
            self.logger.warning("No file selected")

    def printFile(self):
        """Sends the selected file to printer and starts printing"""
        self.logger.info("Printing file")
        # TODO: Send file to printer and switch to the home screen to show print progress
        self.main_window.switch_to_home_screen()

    def deleteItem(self):
        """Deletes the selected local file"""
        self.logger.info("Deleting file")
        
        if self.fileListWidgetLocal and self.fileListWidgetLocal.currentItem():
            # TODO: Delete the selected file
            self.logger.info(f"Deleting file: {self.fileListWidgetLocal.currentItem().text()}")
        else:
            self.logger.warning("No file selected to delete")

    def transferToLocal(self):
        """Transfers the selected USB file to local storage"""
        self.logger.info("Transferring file from USB to local storage")
        
        if self.fileListWidgetUSB and self.fileListWidgetUSB.currentItem():
            # TODO: Copy the file from USB to local storage
            self.logger.info(f"Transferring file: {self.fileListWidgetUSB.currentItem().text()}")
        else:
            self.logger.warning("No file selected to transfer")