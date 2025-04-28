from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton, QLabel, QProgressBar
from PyQt5.QtCore import QTimer
from utils.helpers import check_ui_elements
from models.printer_model import PrinterModel  # Import the printer status model
from utils import logger  # Import the logger
from utils.styles import printer_status_green, printer_status_red, printer_status_amber

class HomeScreen(QWidget):
    def __init__(self, main_window):
        super(HomeScreen, self).__init__()
        self.main_window = main_window
        self.printer_connected = False
        self.is_printing = False
        self.temperature_data = {"tool0": {"actual": 0, "target": 0}, 
                              "tool1": {"actual": 0, "target": 0}, 
                              "bed": {"actual": 0, "target": 0}}
        
        # Job info
        self.current_file = "No file selected"
        self.print_progress = 0
        self.print_time = "00:00:00"
        self.time_left = "00:00:00"

        # Load the UI
        try:
            uic.loadUi('src/ui/home_screen/home_screen.ui', self)
            logger.info("HomeScreen UI loaded successfully")
        except Exception as e:
            logger.exception(f"Failed to load HomeScreen UI file: {e}")
        
        # Initialize UI components by group
        # Control buttons
        self.doorLockButton = self.findChild(QToolButton, "doorLockButton")
        self.menuButton = self.findChild(QPushButton, "menuButton")
        self.stopButton = self.findChild(QPushButton, "stopButton")
        self.playPauseButton = self.findChild(QPushButton, "playPauseButton")
        self.controlButton = self.findChild(QPushButton, "controlButton")
        
        # Temperature displays - Tool 0
        self.tool0TargetTemperature = self.findChild(QLabel, "tool0TargetTemperature")
        self.tool0ActualTemperature = self.findChild(QLabel, "tool0ActualTemperature")
        self.tool0TempBar = self.findChild(QProgressBar, "tool0TempBar")
        
        # Temperature displays - Tool 1
        self.tool1TargetTemperature = self.findChild(QLabel, "tool1TargetTemperature")
        self.tool1ActualTemperature = self.findChild(QLabel, "tool1ActualTemperature")
        self.tool1TempBar = self.findChild(QProgressBar, "tool1TempBar")
        
        # Temperature displays - Bed
        self.bedTargetTemperature = self.findChild(QLabel, "bedTargetTemperature")
        self.bedActualTemperatute = self.findChild(QLabel, "bedActualTemperatute")
        self.bedTempBar = self.findChild(QProgressBar, "bedTempBar")
        
        # Status components
        self.printerStatus = self.findChild(QLabel, "printerStatus")
        self.printerStatusColour = self.findChild(QLabel, "printerStatusColour")
        self.ipStatus = self.findChild(QLabel, "ipStatus")
        
        # Print information
        self.fileName = self.findChild(QLabel, "fileName")
        self.printTime = self.findChild(QLabel, "printTime")
        self.timeLeft = self.findChild(QLabel, "timeLeft")
        self.printProgressBar = self.findChild(QProgressBar, "printProgressBar")
        self.printPreviewMain = self.findChild(QLabel, "printPreviewMain")
        
        # Validate UI components
        all_components = [
            self.doorLockButton, self.menuButton, self.stopButton, self.playPauseButton, self.controlButton,
            self.tool0TargetTemperature, self.tool0ActualTemperature, self.tool0TempBar,
            self.tool1TargetTemperature, self.tool1ActualTemperature, self.tool1TempBar,
            self.bedTargetTemperature, self.bedActualTemperatute, self.bedTempBar,
            self.printerStatus, self.printerStatusColour, self.ipStatus,
            self.fileName, self.printTime, self.timeLeft, self.printProgressBar, self.printPreviewMain
        ]
        check_ui_elements(self, all_components, "HomeScreen")
        
        # Connect button signals to their handlers
        if self.doorLockButton:
            self.doorLockButton.clicked.connect(self.toggle_door_lock)
        
        if self.menuButton:
            self.menuButton.clicked.connect(self.open_menu)
        
        if self.stopButton:
            self.stopButton.clicked.connect(self.stop_print)
        
        if self.playPauseButton:
            self.playPauseButton.clicked.connect(self.play_pause_print)
        
        if self.controlButton:
            self.controlButton.clicked.connect(self.open_control_panel)
        
        # Initialize UI state
        # Update temperature displays
        if self.tool0ActualTemperature and self.tool0TargetTemperature:
            self.tool0ActualTemperature.setText("0.0")
            self.tool0TargetTemperature.setText("0.0")
            if self.tool0TempBar:
                self.tool0TempBar.setValue(0)
        
        if self.tool1ActualTemperature and self.tool1TargetTemperature:
            self.tool1ActualTemperature.setText("0.0")
            self.tool1TargetTemperature.setText("0.0")
            if self.tool1TempBar:
                self.tool1TempBar.setValue(0)
        
        if self.bedActualTemperatute and self.bedTargetTemperature:
            self.bedActualTemperatute.setText("0.0")
            self.bedTargetTemperature.setText("0.0")
            if self.bedTempBar:
                self.bedTempBar.setValue(0)
        
        # Update print info
        if self.fileName:
            self.fileName.setText(self.current_file)
        if self.printTime:
            self.printTime.setText(self.print_time)
        if self.timeLeft:
            self.timeLeft.setText(self.time_left)
        if self.printProgressBar:
            self.printProgressBar.setValue(self.print_progress)
        
        # Update printer status
        if self.printerStatus:
            self.printerStatus.setText("Disconnected")
        if self.printerStatusColour:
            self.printerStatusColour.setStyleSheet(printer_status_red)
        if self.ipStatus:
            self.ipStatus.setText("Not Connected")
        
        # Set up update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui_from_printer_status)
        self.update_timer.start(1000)  # Update every second

    def update_ui_from_printer_status(self):
        """Update UI based on current printer status"""
        if hasattr(self.main_window, 'octoprint_client'):
            client = self.main_window.octoprint_client
            if client and client.is_connected():
                # Get latest status information
                printer_data = client.get_printer_status()
                job_data = client.get_job_status()
                
                # Update our internal data
                self._update_temperature_data(printer_data)
                self._update_job_data(job_data)
                
                # Update UI
                self._update_temperature_displays()
                self._update_print_info()
                self._update_printer_status(printer_data.get("state", {}).get("text", "Unknown"))
                
                # Update connection status
                self._update_connection_status(True, client.get_ip_address())
            else:
                self._update_connection_status(False)
    
    def _update_temperature_data(self, printer_data):
        """Update internal temperature data from printer status"""
        if not printer_data or "temperature" not in printer_data:
            return
            
        temp_data = printer_data["temperature"]
        
        # Update tool0 temperature
        if "tool0" in temp_data:
            self.temperature_data["tool0"]["actual"] = temp_data["tool0"]["actual"]
            self.temperature_data["tool0"]["target"] = temp_data["tool0"]["target"]
        
        # Update tool1 temperature
        if "tool1" in temp_data:
            self.temperature_data["tool1"]["actual"] = temp_data["tool1"]["actual"]
            self.temperature_data["tool1"]["target"] = temp_data["tool1"]["target"]
        
        # Update bed temperature
        if "bed" in temp_data:
            self.temperature_data["bed"]["actual"] = temp_data["bed"]["actual"] 
            self.temperature_data["bed"]["target"] = temp_data["bed"]["target"]
    
    def _update_job_data(self, job_data):
        """Update internal job data from printer status"""
        if not job_data:
            return
            
        # Update file name
        if "file" in job_data and "name" in job_data["file"]:
            self.current_file = job_data["file"]["name"]
        else:
            self.current_file = "No file selected"
        
        # Update progress
        if "progress" in job_data and "completion" in job_data["progress"]:
            progress = job_data["progress"]["completion"]
            self.print_progress = int(progress) if progress is not None else 0
        
        # Update time information
        if "progress" in job_data:
            # Print time
            if "printTime" in job_data["progress"]:
                seconds = job_data["progress"]["printTime"] or 0
                self.print_time = self._format_time(seconds)
            
            # Time left
            if "printTimeLeft" in job_data["progress"]:
                seconds = job_data["progress"]["printTimeLeft"] or 0
                self.time_left = self._format_time(seconds)
    
    def _format_time(self, seconds):
        """Format seconds to HH:MM:SS"""
        if seconds is None:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _update_temperature_displays(self):
        """Update all temperature displays"""
        # Tool 0
        if self.tool0ActualTemperature and self.tool0TargetTemperature and self.tool0TempBar:
            actual = self.temperature_data["tool0"]["actual"]
            target = self.temperature_data["tool0"]["target"]
            
            self.tool0ActualTemperature.setText(f"{actual:.1f}")
            self.tool0TargetTemperature.setText(f"{target:.1f}")
            self.tool0TempBar.setValue(min(int(actual), self.tool0TempBar.maximum()))
        
        # Tool 1
        if self.tool1ActualTemperature and self.tool1TargetTemperature and self.tool1TempBar:
            actual = self.temperature_data["tool1"]["actual"]
            target = self.temperature_data["tool1"]["target"]
            
            self.tool1ActualTemperature.setText(f"{actual:.1f}")
            self.tool1TargetTemperature.setText(f"{target:.1f}")
            self.tool1TempBar.setValue(min(int(actual), self.tool1TempBar.maximum()))
        
        # Bed
        if self.bedActualTemperatute and self.bedTargetTemperature and self.bedTempBar:
            actual = self.temperature_data["bed"]["actual"]
            target = self.temperature_data["bed"]["target"]
            
            self.bedActualTemperatute.setText(f"{actual:.1f}")
            self.bedTargetTemperature.setText(f"{target:.1f}")
            self.bedTempBar.setValue(min(int(actual), self.bedTempBar.maximum()))
    
    def _update_print_info(self):
        """Update print job information"""
        if self.fileName:
            self.fileName.setText(self.current_file)
        
        if self.printTime:
            self.printTime.setText(self.print_time)
        
        if self.timeLeft:
            self.timeLeft.setText(self.time_left)
        
        if self.printProgressBar:
            self.printProgressBar.setValue(self.print_progress)
    
    def _update_printer_status(self, status_text):
        """Update printer status display and indicator"""
        if not self.printerStatus or not self.printerStatusColour:
            return

        self.printerStatus.setText(status_text)

        # Set color based on status
        if status_text.lower() in ["operational", "ready"]:
            self.printerStatusColour.setStyleSheet(printer_status_green)
        elif status_text.lower() in ["printing", "paused"]:
            self.printerStatusColour.setStyleSheet(printer_status_amber)
        else:
            self.printerStatusColour.setStyleSheet(printer_status_red)

    def _update_connection_status(self, connected, ip_address=None):
        """Update printer connection status"""
        self.printer_connected = connected
        
        if self.ipStatus:
            if connected and ip_address:
                self.ipStatus.setText(f"Connected: {ip_address}")
            else:
                self.ipStatus.setText("Not Connected")
        
        # Disable controls when not connected
        for button_name in ["doorLockButton", "playPauseButton", "stopButton"]:
            button = self.all_components.get(button_name, {}).get("instance")
            if button:
                button.setEnabled(connected)

    # Event handlers
    
    def toggle_door_lock(self):
        """Toggle printer door lock"""
        if not self.printer_connected:
            return
            
        logger.debug("Toggle Door Lock button clicked")
        is_locked = self.doorLockButton.isChecked()
        door_status = "locked" if is_locked else "unlocked"
        logger.info(f"Door {door_status}")
        
        # Send command to OctoPrint if connected
        if hasattr(self.main_window, 'octoprint_client'):
            client = self.main_window.octoprint_client
            if client and client.is_connected():
                # Replace with actual command for your printer
                command = "M280 P0 S10" if is_locked else "M280 P0 S90" 
                client.send_gcode_command(command)

    def open_menu(self):
        """Navigate to menu screen"""
        self.main_window.switch_to_menu_screen()
        logger.debug("Menu button clicked")

    def stop_print(self):
        """Stop current print job"""
        if not self.printer_connected:
            return
            
        logger.debug("Stop Print button clicked")
        
        # Send command to OctoPrint if connected
        if hasattr(self.main_window, 'octoprint_client'):
            client = self.main_window.octoprint_client
            if client and client.is_connected():
                client.cancel_print()

    def play_pause_print(self):
        """Play or pause print job based on current state"""
        if not self.printer_connected:
            return
            
        is_paused = self.playPauseButton.isChecked()
        logger.debug(f"Play/Pause button clicked: {'Pausing' if not is_paused else 'Resuming'}")
        
        # Send command to OctoPrint if connected
        if hasattr(self.main_window, 'octoprint_client'):
            client = self.main_window.octoprint_client
            if client and client.is_connected():
                if is_paused:
                    client.resume_print()
                else:
                    client.pause_print()

    def open_control_panel(self):
        """Navigate to control panel screen"""
        self.main_window.switch_to_control_screen()
        logger.debug("Control Panel button clicked")