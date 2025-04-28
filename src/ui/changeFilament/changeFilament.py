from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QComboBox, QProgressBar, QLabel
from utils.helpers import check_ui_elements

class ChangeFilament(QWidget):
    def __init__(self, main_window):
        super(ChangeFilament, self).__init__()
        self.main_window = main_window
        
        # Load UI
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Connect signals to slots
        self._connect_signals()

        # Set the default screen
        self._show_page('changeFilamentPage')

    def _load_ui(self):
        """Load the UI file with error handling"""
        try:
            uic.loadUi('src/ui/changeFilament/changeFilament.ui', self)
            print("ChangeFilament UI loaded successfully")
        except Exception as e:
            print(f"Failed to load ChangeFilament UI file: {e}")

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        # Container widgets
        self.container_widgets = {
            "stackedWidget": {"type": QStackedWidget, "instance": None}
        }
        
        # Pages in the stacked widget
        self.page_widgets = {
            "changeFilamentPage": {"type": QWidget, "instance": None},
            "changeFilamentProgressPage": {"type": QWidget, "instance": None},
            "changeFilamentLoadPage": {"type": QWidget, "instance": None},
            "changeFilamentExtrudePage": {"type": QWidget, "instance": None},
            "changeFilamentRetractPage": {"type": QWidget, "instance": None}
        }
        
        # Navigation buttons
        self.nav_buttons = {
            "changeFilamentBackButton": {"type": QPushButton, "instance": None},
            "changeFilamentBackButton2": {"type": QPushButton, "instance": None},
            "changeFilamentBackButton3": {"type": QPushButton, "instance": None}
        }
        
        # Action buttons
        self.action_buttons = {
            "changeFilamentLoadButton": {"type": QPushButton, "instance": None},
            "changeFilamentUnloadButton": {"type": QPushButton, "instance": None},
            "toolToggleChangeFilamentButton": {"type": QPushButton, "instance": None},
            "loadedTillExtruderButton": {"type": QPushButton, "instance": None},
            "loadDoneButton": {"type": QPushButton, "instance": None},
            "unloadDoneButton": {"type": QPushButton, "instance": None}
        }
        
        # Status and control elements
        self.status_controls = {
            "changeFilamentComboBox": {"type": QComboBox, "instance": None},
            "changeFilamentProgress": {"type": QProgressBar, "instance": None},
            "changeFilamentStatus": {"type": QLabel, "instance": None}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.container_widgets)
        self.all_components.update(self.page_widgets)
        self.all_components.update(self.nav_buttons)
        self.all_components.update(self.action_buttons)
        self.all_components.update(self.status_controls)
        
        # Find all components using the dictionary
        self._find_components()
        
        # Store reference to essential stacked widget for convenience
        self.stackedWidget = self.container_widgets["stackedWidget"]["instance"]

    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_type = component_info["type"]
            component = self.findChild(component_type, name)
            component_info["instance"] = component
            
            # Debug output
            if component:
                print(f"Found {component_type.__name__} '{name}'")
            else:
                print(f"WARNING: Could not find {component_type.__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create mappings of component categories for reporting
        component_groups = {
            "ChangeFilament - Containers": {name: info["instance"] for name, info in self.container_widgets.items()},
            "ChangeFilament - Pages": {name: info["instance"] for name, info in self.page_widgets.items()},
            "ChangeFilament - Navigation Buttons": {name: info["instance"] for name, info in self.nav_buttons.items()},
            "ChangeFilament - Action Buttons": {name: info["instance"] for name, info in self.action_buttons.items()},
            "ChangeFilament - Status Controls": {name: info["instance"] for name, info in self.status_controls.items()}
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)

    def _connect_signals(self):
        """Connect signals to slots using dictionary-based approach with safety checks"""
        # Map navigation buttons to back handler
        for button_name, button_info in self.nav_buttons.items():
            button = button_info["instance"]
            if button:
                button.clicked.connect(self._handle_back_button)
                print(f"Connected {button_name} to back handler")
        
        # Map action buttons to their respective handlers
        action_handlers = {
            "changeFilamentLoadButton": self.start_loading_filament,
            "changeFilamentUnloadButton": self.start_unloading_filament,
            "toolToggleChangeFilamentButton": self.toggle_tool,
            "loadedTillExtruderButton": self.filament_loaded_till_extruder,
            "loadDoneButton": self.finish_loading_filament,
            "unloadDoneButton": self.finish_unloading_filament
        }
        
        for button_name, handler in action_handlers.items():
            button = self.action_buttons.get(button_name, {}).get("instance")
            if button:
                button.clicked.connect(handler)
                print(f"Connected {button_name} to its handler")

    def _show_page(self, page_name):
        """Show a specific page in the stacked widget"""
        if not self.stackedWidget:
            print("ERROR: Cannot show page - stacked widget is missing")
            return False
            
        page = self.page_widgets.get(page_name, {}).get("instance")
        if page:
            self.stackedWidget.setCurrentWidget(page)
            print(f"Showing page: {page_name}")
            return True
        else:
            print(f"ERROR: Cannot show page {page_name} - page not found")
            return False

    def _update_status(self, message):
        """Update the status label with a message"""
        status_label = self.status_controls.get("changeFilamentStatus", {}).get("instance")
        if status_label:
            status_label.setText(message)
            print(f"Status updated: {message}")
        else:
            print("WARNING: Could not update status - label not found")

    def _handle_back_button(self):
        """Handle back button logic with proper safety checks"""
        if self.stackedWidget:
            # Reset to first page in this widget's stack
            first_page = self.page_widgets.get("changeFilamentPage", {}).get("instance")
            if first_page:
                self.stackedWidget.setCurrentWidget(first_page)
            print("Back button: reset to first page")
            
        # Return to previous screen in main window
        self.main_window.switch_to_previous_screen()
        print("Back button: returning to previous screen")

    def start_loading_filament(self):
        """Start the filament loading process"""
        print("Starting filament loading process")
        self._show_page('changeFilamentLoadPage')
        self._update_status("Insert filament and wait for automatic pull")
        
        # Here you would add logic to send commands to the printer
        # e.g., self.main_window.octoprint_client.start_loading_filament()

    def start_unloading_filament(self):
        """Start the filament unloading process"""
        print("Starting filament unloading process")
        self._show_page('changeFilamentRetractPage')
        self._update_status("Retracting filament...")
        
        # Here you would add logic to send commands to the printer
        # e.g., self.main_window.octoprint_client.start_unloading_filament()

    def toggle_tool(self):
        """Toggle between extruder tools (dual extruder support)"""
        tool_button = self.action_buttons.get("toolToggleChangeFilamentButton", {}).get("instance")
        if tool_button and tool_button.isChecked():
            print("Toggling to Tool 1")
            # Add logic for Tool 1
        else:
            print("Toggling to Tool 0")
            # Add logic for Tool 0

    def filament_loaded_till_extruder(self):
        """Handle the event when filament is loaded till the extruder"""
        print("Filament loaded till extruder")
        self._show_page('changeFilamentExtrudePage')
        self._update_status("Extruding filament...")
        
        # Here you would add logic to send commands to the printer
        # e.g., self.main_window.octoprint_client.extrude_filament()

    def finish_loading_filament(self):
        """Finish the filament loading process"""
        print("Filament loading process finished")
        self._update_status("Filament loaded successfully")
        
        # Return to previous screen
        self.main_window.switch_to_previous_screen()

    def finish_unloading_filament(self):
        """Finish the filament unloading process"""
        print("Filament unloading process finished")
        self._update_status("Filament unloaded successfully")
        
        # Return to initial page before going back
        self._show_page('changeFilamentPage')
        self.main_window.switch_to_previous_screen()