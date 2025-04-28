from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton, QLabel, QProgressBar
from PyQt5.QtCore import QTimer
from utils.helpers import check_ui_elements
from models.printer_status import PrinterStatus  # Import the printer status model
from utils import logger  # Import the logger

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
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Connect signals to slots
        self._connect_signals()
        
        # Set up update timer
        self._setup_update_timer()

    def _load_ui(self):
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('src/ui/home_screen/home_screen.ui', self)
            logger.info("HomeScreen UI loaded successfully")
        except Exception as e:
            logger.exception(f"Failed to load HomeScreen UI file: {e}")

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        # Define component mappings by type
        self.control_buttons = {
            # Control buttons (by type and name)
            "doorLockButton": {"type": QToolButton, "instance": None},
            "menuButton": {"type": QPushButton, "instance": None},
            "stopButton": {"type": QPushButton, "instance": None},
            "playPauseButton": {"type": QPushButton, "instance": None},
            "controlButton": {"type": QPushButton, "instance": None},
        }
        
        self.temperature_displays = {
            # Tool 0
            "tool0TargetTemperature": {"type": QLabel, "instance": None},
            "tool0ActualTemperature": {"type": QLabel, "instance": None},
            "tool0TempBar": {"type": QProgressBar, "instance": None},
            
            # Tool 1
            "tool1TargetTemperature": {"type": QLabel, "instance": None},
            "tool1ActualTemperature": {"type": QLabel, "instance": None},
            "tool1TempBar": {"type": QProgressBar, "instance": None},
            
            # Bed
            "bedTargetTemperature": {"type": QLabel, "instance": None},
            "bedActualTemperatute": {"type": QLabel, "instance": None},
            "bedTempBar": {"type": QProgressBar, "instance": None},
        }
        
        self.status_components = {
            # Status components
            "printerStatus": {"type": QLabel, "instance": None},
            "printerStatusColour": {"type": QLabel, "instance": None},
            "ipStatus": {"type": QLabel, "instance": None},
        }
        
        self.print_info_components = {
            # Print information
            "fileName": {"type": QLabel, "instance": None},
            "printTime": {"type": QLabel, "instance": None},
            "timeLeft": {"type": QLabel, "instance": None},
            "printProgressBar": {"type": QProgressBar, "instance": None},
            "printPreviewMain": {"type": QLabel, "instance": None},
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.control_buttons)
        self.all_components.update(self.temperature_displays)
        self.all_components.update(self.status_components)
        self.all_components.update(self.print_info_components)
        
        # Find all components using the dictionary
        self._find_components()
        
        # Initial UI state
        self._update_temperature_displays()
        self._update_print_info()
        self._update_printer_status("Disconnected")
        
    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_type = component_info["type"]
            component = self.findChild(component_type, name)
            component_info["instance"] = component
            
            # Store a direct reference for easy access
            setattr(self, name, component)
            
            # Debug output
            if component:
                logger.debug(f"Found {component_type.__name__} '{name}'")
            else:
                logger.warning(f"Could not find {component_type.__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create a dictionary with component name to instance mapping
        ui_components = {name: info["instance"] for name, info in self.all_components.items()}
        
        # Use the helper function to check and report missing widgets
        check_ui_elements(self, ui_components, "HomeScreen")
    
    def _connect_signals(self):
        """Connect UI signals to their handlers with safety checks"""
        # Control buttons
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

    def _setup_update_timer(self):
        """Set up timer for periodic UI updates"""
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
            self.printerStatusColour.setStyleSheet("""\
                border: 1px solid rgb(87, 87, 87);
                border-radius: 10px;
                background-color: qlineargradient(spread:pad, x1:0, y1:0.523, x2:0, y2:0.534, \
                                               stop:0 rgba(130, 203, 117, 255), \
                                               stop:1 rgba(66, 191, 85, 255));
            """)
        elif status_text.lower() in ["printing", "paused"]:
            self.printerStatusColour.setStyleSheet("""\
                border: 1px solid rgb(87, 87, 87);
                border-radius: 10px;
                background-color: qlineargradient(spread:pad, x1:0, y1:0.523, x2:0, y2:0.534, \
                                               stop:0 rgba(255, 191, 0, 255), \
                                               stop:1 rgba(254, 153, 0, 255));
            """)
        else:
            self.printerStatusColour.setStyleSheet("""\
                border: 1px solid rgb(87, 87, 87);
                border-radius: 10px;
                background-color: qlineargradient(spread:pad, x1:0, y1:0.523, x2:0, y2:0.534, \
                                               stop:0 rgba(255, 60, 60, 255), \
                                               stop:1 rgba(255, 30, 30, 255));
            """)

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