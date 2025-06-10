from PyQt5 import QtGui, QtCore
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel, QCheckBox
from functools import partial  # Add missing import for partial function
from utils.custom_widgets import ClickableLineEdit
from utils.helpers import check_ui_elements
from utils.logger import setup_logger
from utils import styles  # Import styles module
from utils import keyboard  # Import keyboard module

# Network utils import
from utils.network_utils import getIP, getHostname, getWifiAp, getMac
from utils.network_utils import ThreadRestartNetworking

from utils import dialog

from utils.helpers import run_async
import time
import subprocess
import qrcode
import io
from utils.qrcode_image import Image

# Initialize logger for NetworkSettings
logger = setup_logger('network_settings')


class NetworkSettings(QWidget):
    """
    Network Settings widget that allows users to configure network connections
    including WiFi and Static IP settings.
    """

    def __init__(self, parent, settings_screen):
        super(NetworkSettings, self).__init__(parent)
        self.mainSettingsWidget = settings_screen  # Reference to the main settings widget

        # Load the UI
        try:
            uic.loadUi(
                '/home/pi/OctoPrint/venv/lib/python3.7/site-packages/octoprint_ControlCenter/ui/settings_screen/network_settings/network_settings.ui',
                self)
            logger.info("NetworkSettings UI loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load NetworkSettings UI file: {e}")

        # Initialize UI components
        # Navigation buttons
        self.networkSettingsBackButton = self.findChild(QPushButton, "networkSettingsBackButton")
        self.networkInfoBackButton = self.findChild(QPushButton, "networkInfoBackButton")
        self.staticIPSettingsCancelButton = self.findChild(QPushButton, "staticIPSettingsCancelButton")
        self.wifiSettingsCancelButton = self.findChild(QPushButton, "wifiSettingsCancelButton")

        # Action buttons
        self.networkInfoButton = self.findChild(QPushButton, "networkInfoButton")
        self.configureStaticIPButton = self.findChild(QPushButton, "configureStaticIPButton")
        self.configureWifiButton = self.findChild(QPushButton, "configureWifiButton")
        self.staticIPSettingsDoneButton = self.findChild(QPushButton, "staticIPSettingsDoneButton")
        self.wifiSettingsDoneButton = self.findChild(QPushButton, "wifiSettingsDoneButton")
        self.deleteStaticIPSettingsButton = self.findChild(QPushButton, "deleteStaticIPSettingsButton")

        # Keyboard buttons
        self.staticIPKeyboardButton = self.findChild(QPushButton, "staticIPKeyboardButton")
        self.staticIPGatewayKeyboardButton = self.findChild(QPushButton, "staticIPGatewayKeyboardButton")
        self.staticIPNameServerKeyboardButton = self.findChild(QPushButton, "staticIPNameServerKeyboardButton")
        self.wifiSettingsSSIDKeyboardButton = self.findChild(QPushButton, "wifiSettingsSSIDKeyboardButton")

        # UI containers and pages
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.networkSettingsPage = self.findChild(QWidget, "networkSettingsPage")
        self.networkInfoPage = self.findChild(QWidget, "networkInfoPage")
        self.staticIPSettingsPage = self.findChild(QWidget, "staticIPSettingsPage")
        self.wifiSettingsPage = self.findChild(QWidget, "wifiSettingsPage")

        self.QRCodeLabel = self.findChild(QLabel, "QRCodeLabel")
        self.hiddenCheckBox = self.findChild(QCheckBox, "hiddenCheckBox")

        # Validate UI components using simplified check_ui_elements
        # Convert all UI components into a single list for validation
        ui_components = [
            self.networkSettingsBackButton, self.networkInfoBackButton,
            self.staticIPSettingsCancelButton, self.wifiSettingsCancelButton,
            self.networkInfoButton, self.configureStaticIPButton,
            self.configureWifiButton, self.staticIPSettingsDoneButton,
            self.wifiSettingsDoneButton, self.deleteStaticIPSettingsButton,
            self.staticIPKeyboardButton, self.staticIPGatewayKeyboardButton,
            self.staticIPNameServerKeyboardButton, self.wifiSettingsSSIDKeyboardButton,
            self.stackedWidget, self.networkSettingsPage, self.networkInfoPage,
            self.staticIPSettingsPage, self.wifiSettingsPage, self.QRCodeLabel
        ]

        # Validate all components at once
        check_ui_elements(self, ui_components, "NetworkSettings UI Components")

        # Create ClickableLineEdit components
        # Fonts and styles
        font = QtGui.QFont()
        font.setFamily("Gotham")
        font.setPointSize(15)

        # WiFi Password Line Edit
        self.wifiPasswordLineEdit = ClickableLineEdit(self.wifiSettingsPage)
        self.wifiPasswordLineEdit.setGeometry(QtCore.QRect(300, 170, 400, 60))
        self.wifiPasswordLineEdit.setFont(font)
        self.wifiPasswordLineEdit.setStyleSheet(styles.textedit)
        self.wifiPasswordLineEdit.setObjectName("wifiPasswordLineEdit")

        # Static IP Line Edits
        font.setPointSize(11)
        self.staticIPLineEdit = ClickableLineEdit(self.staticIPSettingsPage)
        self.staticIPLineEdit.setGeometry(QtCore.QRect(200, 15, 450, 40))
        self.staticIPLineEdit.setFont(font)
        self.staticIPLineEdit.setStyleSheet(styles.textedit)
        self.staticIPLineEdit.setObjectName("staticIPLineEdit")

        self.staticIPGatewayLineEdit = ClickableLineEdit(self.staticIPSettingsPage)
        self.staticIPGatewayLineEdit.setGeometry(QtCore.QRect(200, 85, 450, 40))
        self.staticIPGatewayLineEdit.setFont(font)
        self.staticIPGatewayLineEdit.setStyleSheet(styles.textedit)
        self.staticIPGatewayLineEdit.setObjectName("staticIPGatewayLineEdit")

        self.staticIPNameServerLineEdit = ClickableLineEdit(self.staticIPSettingsPage)
        self.staticIPNameServerLineEdit.setGeometry(QtCore.QRect(200, 155, 450, 40))
        self.staticIPNameServerLineEdit.setFont(font)
        self.staticIPNameServerLineEdit.setStyleSheet(styles.textedit)
        self.staticIPNameServerLineEdit.setObjectName("staticIPNameServerLineEdit")

        # Connect buttons to their respective functions
        # Navigation buttons
        if self.networkSettingsBackButton:
            self.networkSettingsBackButton.clicked.connect(self.go_back_to_settings_screen)

        if self.networkInfoBackButton:
            self.networkInfoBackButton.clicked.connect(self.go_back)

        if self.staticIPSettingsCancelButton:
            self.staticIPSettingsCancelButton.clicked.connect(self.cancel_network_settings)

        if self.wifiSettingsCancelButton:
            self.wifiSettingsCancelButton.clicked.connect(self.cancel_network_settings)

        # Action buttons
        if self.networkInfoButton:
            self.networkInfoButton.clicked.connect(self.networkInfo)

        if self.configureStaticIPButton:
            self.configureStaticIPButton.clicked.connect(self.show_static_ip_settings)

        if self.configureWifiButton:
            self.configureWifiButton.clicked.connect(self.wifiSettings)

        if self.staticIPSettingsDoneButton:
            self.staticIPSettingsDoneButton.clicked.connect(self.save_network_settings)

        if self.wifiSettingsDoneButton:
            self.wifiSettingsDoneButton.clicked.connect(self.acceptWifiSettings)

        if self.hiddenCheckBox:
            self.hiddenCheckBox.stateChanged.connect(self.togglePasswordVisibility)

        # Set the default page in stacked widget
        if self.stackedWidget and self.networkSettingsPage:
            self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
            logger.info("Set default page to networkSettingsPage")
        else:
            logger.warning("Could not set default page - required widgets missing")

        # Connect text input fields to keyboard
        # Text Input events
        self.wifiPasswordLineEdit.clicked_signal.connect(lambda: self.startKeyboard(self.wifiPasswordLineEdit.setText))
        self.staticIPLineEdit.clicked_signal.connect(lambda: self.staticIPShowKeyboard(self.staticIPLineEdit))
        self.staticIPGatewayLineEdit.clicked_signal.connect(
            lambda: self.staticIPShowKeyboard(self.staticIPGatewayLineEdit))
        self.staticIPNameServerLineEdit.clicked_signal.connect(
            lambda: self.staticIPShowKeyboard(self.staticIPNameServerLineEdit))
        self.wifiSettingsSSIDKeyboardButton.clicked.connect(
            lambda: self.startKeyboard(self.wifiSettingsComboBox.addItem))

    def networkInfo(self):
        logger.info("MainUiClass.networkInfo started")
        try:
            ipWifi = getIP(ThreadRestartNetworking.WLAN)
            ipEth = getIP(ThreadRestartNetworking.ETH)

            self.hostname.setText(getHostname())
            self.wifiAp.setText(getWifiAp())
            self.wifiIp.setText("Not connected" if not ipWifi else ipWifi)
            self.mainSettingsWidget.main_window.home_screen.ipStatus.setText("Not connected" if not ipWifi else ipWifi)
            self.lanIp.setText("Not connected" if not ipEth else ipEth)
            self.wifiMac.setText(getMac(ThreadRestartNetworking.WLAN).decode('utf8'))
            self.lanMac.setText(getMac(ThreadRestartNetworking.ETH).decode('utf8'))
            self.stackedWidget.setCurrentWidget(self.networkInfoPage)
            self.displayQRCode()
        except Exception as e:
            logger.error("Error in MainUiClass.networkInfo: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.networkInfo: {}".format(e), overlay=True)

    def displayQRCode(self):
        # Display QR Code
        try:
            if getIP(ThreadRestartNetworking.ETH) is not None:
                qrip = getIP(ThreadRestartNetworking.ETH)
            elif getIP(ThreadRestartNetworking.WLAN) is not None:
                qrip = getIP(ThreadRestartNetworking.WLAN)
            else:
                if dialog.WarningOk(self, "Network Disconnected"):
                    return
            self.QRCodeLabel.setPixmap(
                qrcode.make("http://" + qrip, image_factory=Image).pixmap())
            # self.stackedWidget.setCurrentWidget(self.QRCodePage)
        except Exception as e:
            logger.error("Error in Network Settings: QR CODE {}".format(e))
            dialog.WarningOk(self, "Error in Network Settings: QR CODE {}".format(e), overlay=True)

    def startKeyboard(self, returnFn, onlyNumeric=False, noSpace=False, text=""):
        """
        starts the keyboard screen for entering Password
        """
        logger.info("MainUiClass.startKeyboard started")
        try:
            keyBoardobj = keyboard.Keyboard(onlyNumeric=onlyNumeric, noSpace=noSpace, text=text)
            keyBoardobj.keyboard_signal.connect(returnFn)
            keyBoardobj.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            keyBoardobj.show()
        except Exception as e:
            logger.error("Error in MainUiClass.startKeyboard: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.startKeyboard: {}".format(e), overlay=True)

    def wifiSettings(self):
        logger.info("MainUiClass.wifiSettings started")
        try:
            self.stackedWidget.setCurrentWidget(self.wifiSettingsPage)
            self.wifiSettingsComboBox.clear()
            self.wifiSettingsComboBox.addItems(self.scan_wifi())
            self.wifiPasswordLineEdit.clear()
        except Exception as e:
            logger.error("Error in MainUiClass.wifiSettings: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.wifiSettings: {}".format(e), overlay=True)

    def scan_wifi(self):
        """
        uses linux shell and WIFI interface to scan available networks
        :return: dictionary of the SSID and the signal strength
        """
        logger.info("MainUiClass.scan_wifi started")
        try:
            # scanData = {}
            # print "Scanning available wireless signals available to wlan0"
            scan_result = \
                subprocess.Popen("iwlist wlan0 scan | grep 'ESSID'", stdout=subprocess.PIPE, shell=True).communicate()[0]
            # Processing STDOUT into a dictionary that later will be converted to a json file later
            scan_result = scan_result.decode('utf8').split('ESSID:')  # each ssid and pass from an item in a list ([ssid pass,ssid paas])
            scan_result = [s.strip() for s in scan_result]
            scan_result = [s.strip('"') for s in scan_result]
            scan_result = filter(None, scan_result)
            return scan_result
        except Exception as e:
            logger.error("Error in MainUiClass.scan_wifi: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.scan_wifi: {}".format(e), overlay=True)
            return []

    def acceptWifiSettings(self):
        logger.info("MainUiClass.acceptWifiSettings started")
        try:
            wlan0_config_file = io.open("/etc/wpa_supplicant/wpa_supplicant.conf", "r+", encoding='utf8')
            wlan0_config_file.truncate()
            ascii_ssid = self.wifiSettingsComboBox.currentText()
            # unicode_ssid = ascii_ssid.decode('string_escape').decode('utf-8')
            wlan0_config_file.write(u"country=IN\n")
            wlan0_config_file.write(u"ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
            wlan0_config_file.write(u"update_config=1\n")
            wlan0_config_file.write(u"network={\n")
            wlan0_config_file.write(u'ssid="' + str(ascii_ssid) + '"\n')
            if self.hiddenCheckBox.isChecked():
                wlan0_config_file.write(u'scan_ssid=1\n')
            # wlan0_config_file.write(u"scan_ssid=1\n")
            if str(self.wifiPasswordLineEdit.text()) != "":
                wlan0_config_file.write(u'psk="' + str(self.wifiPasswordLineEdit.text()) + '"\n')
            # wlan0_config_file.write(u"key_mgmt=WPA-PSK\n")
            wlan0_config_file.write(u'}')
            wlan0_config_file.close()
            self.restartWifiThreadObject = ThreadRestartNetworking(ThreadRestartNetworking.WLAN)
            self.restartWifiThreadObject.signal.connect(self.wifiReconnectResult)
            self.restartWifiThreadObject.start()
            self.wifiMessageBox = dialog.dialog(self,
                                                "Restarting networking, please wait...",
                                                icon="exclamation-mark.png",
                                                buttons=QtWidgets.QMessageBox.Cancel)
            if self.wifiMessageBox.exec_() in {QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel}:
                self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
        except Exception as e:
            logger.error("Error in MainUiClass.acceptWifiSettings: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.acceptWifiSettings: {}".format(e), overlay=True)

    def wifiReconnectResult(self, x):
        logger.info("MainUiClass.wifiReconnectResult started")
        try:
            self.wifiMessageBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            if x is not None:
                print("Ouput from signal " + x)
                self.wifiMessageBox.setLocalIcon('success.png')
                self.wifiMessageBox.setText('Connected, IP: ' + x)
                self.wifiMessageBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                self.mainSettingsWidget.main_window.home_screen.ipStatus.setText(x)  # sets the IP addr. in the status bar

            else:
                self.wifiMessageBox.setText("Not able to connect to WiFi")
        except Exception as e:
            logger.error("Error in MainUiClass.wifiReconnectResult: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.wifiReconnectResult: {}".format(e), overlay=True)

    def togglePasswordVisibility(self, state):
        """
        Toggles the visibility of the WiFi password based on the hidden checkbox state.
        """
        if state == QtCore.Qt.Checked:
            self.wifiPasswordLineEdit.setEchoMode(QtWidgets.QLineEdit.Password)  # Hide password
        else:
            self.wifiPasswordLineEdit.setEchoMode(QtWidgets.QLineEdit.Normal)  # Show password

    # ! TO BE COMMENTED OUT
    def save_network_settings(self):
        """Save network settings and return to main network page."""
        logger.info("Save Network Settings button clicked")
        if self.stackedWidget and self.networkSettingsPage:
            self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
            logger.info("Returned to network settings page after save")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def cancel_network_settings(self):
        """Cancel network settings change and return to main network page."""
        logger.info("Cancel Network Settings button clicked")
        if self.stackedWidget and self.networkSettingsPage:
            self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
            logger.info("Returned to network settings page after cancel")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def go_back_to_settings_screen(self):
        """Return to the main settings screen."""
        logger.info("Back to settings screen button clicked")
        if hasattr(self.mainSettingsWidget, 'stackedWidget') and hasattr(self.mainSettingsWidget, 'mainSettingsPage'):
            self.mainSettingsWidget.stackedWidget.setCurrentWidget(self.mainSettingsWidget.mainSettingsPage)
            logger.info("Navigated back to main settings screen")
        else:
            logger.error("Cannot navigate back - required widgets not found in mainSettingsWidget")

    def go_back(self):
        """Return to main network settings page from network info page."""
        logger.info("Back to network settings page button clicked")
        if self.stackedWidget and self.networkSettingsPage:
            self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
            logger.info("Navigated back to network settings page")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def show_network_info(self):
        """Show network information page."""
        logger.info("Network Info button clicked")
        if self.stackedWidget and self.networkInfoPage:
            self.stackedWidget.setCurrentWidget(self.networkInfoPage)
            logger.info("Navigated to network info page")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def show_static_ip_settings(self):
        """Show static IP configuration page."""
        logger.info("Static IP Settings button clicked")
        if self.stackedWidget and self.staticIPSettingsPage:
            self.stackedWidget.setCurrentWidget(self.staticIPSettingsPage)
            logger.info("Navigated to static IP settings page")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def show_wifi_settings(self):
        """Show WiFi configuration page."""
        logger.info("WiFi Settings button clicked")
        if self.stackedWidget and self.wifiSettingsPage:
            self.stackedWidget.setCurrentWidget(self.wifiSettingsPage)
            logger.info("Navigated to WiFi settings page")
        else:
            logger.error("Cannot navigate - required widgets missing")

    def staticIPShowKeyboard(self, textbox):
        """
        Opens the keyboard with IP-specific settings (numeric only, no spaces)
        """
        logger.info("NetworkSettings.staticIPShowKeyboard started")
        try:
            self.startKeyboard(textbox.setText, onlyNumeric=True, noSpace=True, text=str(textbox.text()))
        except Exception as e:
            logger.error(f"Error in NetworkSettings.staticIPShowKeyboard: {e}")
            # If you have a dialog module:
            # dialog.WarningOk(self, f"Error in NetworkSettings.staticIPShowKeyboard: {e}", overlay=True)
