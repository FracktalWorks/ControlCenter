from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QListWidget, QLabel, QToolButton
from utils.helpers import check_ui_elements
from utils import logger
from utils.logger import setup_logger
from utils import dialog
from octoprint_client.octoprint_threaded_file_upload import ThreadFileUpload

import subprocess
from datetime import datetime

from utils.helpers import run_async
from hurry.filesize.filesize import size

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


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
            uic.loadUi(
                '/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/print_from_location/print_from_location.ui',
                self)
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

        # ! USB storage navigation
        if self.USBStorageBackButton:
            self.USBStorageBackButton.clicked.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.printLocationPage)
            )
        if self.USBStorageScrollDown:
            self.USBStorageScrollDown.clicked.connect(
                lambda: self.fileListWidgetUSB.setCurrentRow(self.fileListWidgetUSB.currentRow() + 1)
            )
        if self.USBStorageScrollUp:
            self.USBStorageScrollUp.clicked.connect(
                lambda: self.fileListWidgetUSB.setCurrentRow(self.fileListWidgetUSB.currentRow() - 1)
            )
        if self.USBStorageSelectButton:
            self.USBStorageSelectButton.clicked.connect(self.printSelectedUSB)
        if self.USBStorageSaveButton:
            self.USBStorageSaveButton.clicked.connect(self.transferToLocal)

        # ! Local storage navigation
        if self.localStorageBackButton:
            self.localStorageBackButton.clicked.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.printLocationPage)
            )
        if self.localStorageScrollDown:
            self.localStorageScrollDown.clicked.connect(
                lambda: self.fileListWidgetLocal.setCurrentRow(self.fileListWidgetLocal.currentRow() + 1)
            )
        if self.localStorageScrollUp:
            self.localStorageScrollUp.clicked.connect(
                lambda: self.fileListWidgetLocal.setCurrentRow(self.fileListWidgetLocal.currentRow() - 1)
            )
        if self.localStorageSelectButton:
            self.localStorageSelectButton.clicked.connect(self.printSelectedLocal)
        if self.localStorageDeleteButton:
            self.localStorageDeleteButton.clicked.connect(self.deleteItem)

        # ! Location selection buttons
        if self.fromUsbButton:
            self.fromUsbButton.clicked.connect(self.fileListUSB)
        if self.fromLocalButton:
            self.fromLocalButton.clicked.connect(self.fileListLocal)
        if self.printLocationScreenBackButton:
            self.printLocationScreenBackButton.clicked.connect(self.main_window.switch_to_previous_screen)

        # ! Selected file buttons - USB
        if self.fileSelectedUSBPrintButton:
            self.fileSelectedUSBPrintButton.clicked.connect(lambda: self.transferToLocal(prnt=True))
        if self.fileSelectedUSBTransferButton:
            self.fileSelectedUSBTransferButton.clicked.connect(lambda: self.transferToLocal(prnt=False))
        if self.fileSelectedUSBBackButton:
            self.fileSelectedUSBBackButton.clicked.connect(self.fileListUSB)

        # ! Selected file buttons - Local
        if self.fileSelectedLocalPrintButton:
            self.fileSelectedLocalPrintButton.clicked.connect(self.printFile)
        if self.fileSelectedLocalBackButton:
            self.fileSelectedLocalBackButton.clicked.connect(self.fileListLocal)

        # ! Set the default screen to printLocationPage if it exists
        if self.stackedWidget and self.printLocationPage:
            self.stackedWidget.setCurrentWidget(self.printLocationPage)
            self.logger.info("Set initial page to printLocationPage")
        else:
            self.logger.warning("Could not set default page - required widgets missing")

    ''' ------------------------ HELPER METHODS -------------------------- '''

    def fileListLocal(self):
        """
        Gets the file list from octoprint server, displays it on the list, as well as
        sets the stacked widget page to the file list page
        """
        logger.info("MainUiClass.fileListLocal started")
        try:
            self.stackedWidget.setCurrentWidget(self.fileListLocalPage)
            files = []
            for file in self.main_window.octoprint_client.retrieveFileInformation()['files']:
                if file["type"] == "machinecode":
                    files.append(file)

            self.fileListWidgetLocal.clear()
            files.sort(key=lambda d: d['date'], reverse=True)
            # for item in [f['name'] for f in files] :
            #     self.fileListWidget.addItem(item)
            self.fileListWidgetLocal.addItems([f['name'] for f in files])
            self.fileListWidgetLocal.setCurrentRow(0)
        except Exception as e:
            logger.error("Error in MainUiClass.fileListLocal: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.fileListLocal: {}".format(e), overlay=True)

    def fileListUSB(self):
        """
        Gets the file list from octoprint server, displays it on the list, as well as
        sets the stacked widget page to the file list page
        ToDO: Add deapth of folders recursively get all gcodes
        """
        logger.info("MainUiClass.fileListUSB started")
        try:
            self.stackedWidget.setCurrentWidget(self.fileListUSBPage)
            self.fileListWidgetUSB.clear()
            files = subprocess.Popen("ls /media/usb0 | grep gcode", stdout=subprocess.PIPE, shell=True).communicate()[0]
            files = files.decode('utf-8').split('\n')
            files = filter(None, files)
            # for item in files:
            #     self.fileListWidgetUSB.addItem(item)
            self.fileListWidgetUSB.addItems(files)
            self.fileListWidgetUSB.setCurrentRow(0)
        except Exception as e:
            logger.error("Error in MainUiClass.fileListUSB: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.fileListUSB: {}".format(e), overlay=True)

    def printSelectedLocal(self):

        """
        gets information about the selected file from octoprint server,
        as well as sets the current page to the print selected page.
        This function also selects the file to print from octoprint
        """
        logger.info("MainUiClass.printSelectedLocal started")
        try:
            self.fileSelectedLocalName.setText(self.fileListWidgetLocal.currentItem().text())
            self.stackedWidget.setCurrentWidget(self.printSelectedLocalPage)
            file = self.main_window.octoprint_client.retrieveFileInformation(
                self.fileListWidgetLocal.currentItem().text())
            try:
                self.fileSizeSelected.setText(size(file['size']))
            except KeyError:
                self.fileSizeSelected.setText('-')
            try:
                self.fileDateSelected.setText(datetime.fromtimestamp(file['date']).strftime('%d/%m/%Y %H:%M:%S'))
            except KeyError:
                self.fileDateSelected.setText('-')
            try:
                m, s = divmod(file['gcodeAnalysis']['estimatedPrintTime'], 60)
                h, m = divmod(m, 60)
                d, h = divmod(h, 24)
                self.filePrintTimeSelected.setText("%dd:%dh:%02dm:%02ds" % (d, h, m, s))
            except KeyError:
                self.filePrintTimeSelected.setText('-')
            try:
                self.filamentVolumeSelected.setText(
                    ("%.2f cm" % file['gcodeAnalysis']['filament']['tool0']['volume']) + chr(179))
            except KeyError:
                self.filamentVolumeSelected.setText('-')

            try:
                self.filamentLengthFileSelected.setText(
                    "%.2f mm" % file['gcodeAnalysis']['filament']['tool0']['length'])
            except KeyError:
                self.filamentLengthFileSelected.setText('-')
            # uncomment to select the file when selectedd in list
            # octopiclient.selectFile(self.fileListWidget.currentItem().text(), False)
            self.stackedWidget.setCurrentWidget(self.printSelectedLocalPage)

            '''
            If image is available from server, set it, otherwise display default image
            '''
            self.displayThumbnail(self.printPreviewSelectedLocal, str(self.fileListWidgetLocal.currentItem().text()),
                                  usb=False)

        except Exception as e:
            logger.error("Error in MainUiClass.printSelectedLocal: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.printSelectedLocal: {}".format(e), overlay=True)

    def printSelectedUSB(self):
        """
        Sets the screen to the print selected screen for USB, on which you can transfer to local drive and view preview image.
        :return:
        """
        logger.info("MainUiClass.printSelectedUSB started")
        try:
            self.fileSelectedUSBName.setText(self.fileListWidgetUSB.currentItem().text())
            self.stackedWidget.setCurrentWidget(self.printSelectedUSBPage)
            self.displayThumbnail(self.printPreviewSelectedUSB,
                                  '/media/usb0/' + str(self.fileListWidgetUSB.currentItem().text()), usb=True)
        except Exception as e:
            logger.error("Error in MainUiClass.printSelectedUSB: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.printSelectedUSB: {}".format(e), overlay=True)

    def deleteItem(self):
        """
        Deletes a gcode file, and if associates, its image file from the memory
        """
        logger.info("MainUiClass.deleteItem started")
        try:
            self.main_window.octoprint_client.deleteFile(self.fileListWidgetLocal.currentItem().text())
            self.main_window.octoprint_client.deleteFile(
                self.fileListWidgetLocal.currentItem().text().replace(".gcode", ".png"))
            # delete PNG also
            self.fileListLocal()
        except Exception as e:
            logger.error("Error in MainUiClass.deleteItem: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.deleteItem: {}".format(e), overlay=True)

    def transferToLocal(self, prnt=False):
        """
        Transfers a file from USB mounted at /media/usb0 to octoprint's watched folder so that it gets automatically detected bu Octoprint.
        Warning: If the file is read-only, octoprint API for reading the file crashes.
        """
        logger.info("MainUiClass.transferToLocal started")
        try:
            file = '/media/usb0/' + str(self.fileListWidgetUSB.currentItem().text())

            self.uploadThread = ThreadFileUpload(file, prnt=prnt)
            self.uploadThread.start()
            if prnt:
                self.stackedWidget.setCurrentWidget(self.main_window.home_screen)
        except Exception as e:
            logger.error("Error in MainUiClass.transferToLocal: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.transferToLocal: {}".format(e), overlay=True)

    def printFile(self):
        """
        Prints the file selected from printSelected()
        """
        logger.info("MainUiClass.printFile started")
        try:
            self.main_window.octoprint_client.home(['x', 'y', 'z'])
            self.main_window.octoprint_client.selectFile(self.fileListWidgetLocal.currentItem().text(), True)
            self.main_window.checkKlipperPrinterCFG()

            # Ensure the home_screen is part of the stackedWidget
            # if self.main_window.home_screen not in [self.stackedWidget.widget(i) for i in
            #                                         range(self.stackedWidget.count())]:
            #     self.stackedWidget.addWidget(self.main_window.home_screen)

            self.main_window.switch_to_home_screen()

            # self.stackedWidget.setCurrentWidget(self.main_window.home_screen)
        except Exception as e:
            logger.error("Error in MainUiClass.printFile: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.printFile: {}".format(e), overlay=True)

    @run_async
    def displayThumbnail(self, labelObject, fileLocation, usb=False):
        """
        Displays the image on the label object
        :param labelObject: QLabel object to display the image
        :param fileLocation: location of the file
        :param usb: if the file is from
        """
        logger.info("MainUiClass.displayThumbnail started")
        try:
            pixmap = QtGui.QPixmap()
            if usb:
                img = self.getImageFromGcode(fileLocation)
            else:
                img = self.main_window.octoprint_client.getImage(fileLocation)
            if img:
                pixmap.loadFromData(img)
                labelObject.setPixmap(pixmap)
            else:
                labelObject.setPixmap(QtGui.QPixmap(_fromUtf8("templates/img/thumbnail.png")))
        except Exception as e:
            labelObject.setPixmap(QtGui.QPixmap(_fromUtf8("templates/img/thumbnail.png")))
            logger.error("Error in MainUiClass.displayThumbnail: {}".format(e))