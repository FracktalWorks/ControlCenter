from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QListWidget, QTextEdit
from utils.helpers import check_ui_elements

class SoftwareUpdate(QWidget):
    """
    Software Update widget that allows users to check for and perform
    software updates on the printer's firmware and system.
    """
    def __init__(self, parent, settings_screen):
        super(SoftwareUpdate, self).__init__(parent)
        self.mainSettingsWidget = settings_screen  # Reference to the main settings widget
        
        # Load the UI
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Connect buttons to their respective functions
        self._connect_buttons()
        
        # Set the default screen to OTA Update Page
        self._set_default_page()

    def _load_ui(self):
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('src/ui/settings_screen/software_update/software_update.ui', self)
            print("SoftwareUpdate UI loaded successfully")
        except Exception as e:
            print(f"Failed to load SoftwareUpdate UI file: {e}")

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        # Navigation buttons
        self.navigation_buttons = {
            "softwareUpdateBackButton": {"type": QPushButton, "instance": None}
        }
        
        # Action buttons
        self.action_buttons = {
            "performUpdateButton": {"type": QPushButton, "instance": None}
        }
        
        # UI containers and pages
        self.containers = {
            "stackedWidget": {"type": QStackedWidget, "instance": None},
            "OTAUpdatePage": {"type": QWidget, "instance": None},
            "softwareUpdateProgressPage": {"type": QWidget, "instance": None}
        }
        
        # UI content elements
        self.content_elements = {
            "updateListWidget": {"type": QListWidget, "instance": None},
            "logTextEdit": {"type": QTextEdit, "instance": None}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.navigation_buttons)
        self.all_components.update(self.action_buttons)
        self.all_components.update(self.containers)
        self.all_components.update(self.content_elements)
        
        # Find all components using the dictionary
        self._find_components()

    def _find_components(self):
        """Find all UI components based on their object names"""
        for name, component_info in self.all_components.items():
            component_info["instance"] = self.findChild(component_info["type"], name)
            
            # Debug output
            if component_info["instance"]:
                print(f"Found {component_info['type'].__name__} '{name}'")
            else:
                print(f"WARNING: Could not find {component_info['type'].__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create mappings of component categories for reporting
        component_groups = {
            "SoftwareUpdate - Navigation Buttons": {name: info["instance"] for name, info in self.navigation_buttons.items()},
            "SoftwareUpdate - Action Buttons": {name: info["instance"] for name, info in self.action_buttons.items()},
            "SoftwareUpdate - Containers": {name: info["instance"] for name, info in self.containers.items()},
            "SoftwareUpdate - Content Elements": {name: info["instance"] for name, info in self.content_elements.items()}
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)

    def _connect_buttons(self):
        """Connect buttons to their respective functions with safety checks"""
        # Connect back button
        back_button = self.navigation_buttons.get("softwareUpdateBackButton", {}).get("instance")
        if back_button:
            back_button.clicked.connect(self.go_back_to_settings_screen)
            print("Connected back button to go_back_to_settings_screen")
        else:
            print("WARNING: Could not connect back button - button not found")
            
        # Connect update button
        update_button = self.action_buttons.get("performUpdateButton", {}).get("instance")
        if update_button:
            update_button.clicked.connect(self.update_software)
            print("Connected update button to update_software")
        else:
            print("WARNING: Could not connect update button - button not found")

    def _set_default_page(self):
        """Set the default page in stacked widget"""
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance")
        default_page = self.containers.get("OTAUpdatePage", {}).get("instance")
        
        if stacked_widget and default_page:
            stacked_widget.setCurrentWidget(default_page)
            print("Set default page to OTAUpdatePage")
        else:
            print("WARNING: Could not set default page - required widgets missing")

    def go_back_to_settings_screen(self):
        """Return to the settings screen."""
        print("Back to settings screen button clicked")
        if hasattr(self.mainSettingsWidget, 'stackedWidget') and hasattr(self.mainSettingsWidget, 'mainSettingsPage'):
            self.mainSettingsWidget.stackedWidget.setCurrentWidget(self.mainSettingsWidget.mainSettingsPage)
            print("Navigated back to settings screen")
        else:
            print("ERROR: Cannot navigate back - required widgets not found in mainSettingsWidget")

    def update_software(self):
        """Update the software."""
        print("Updating software...")
        
        stacked_widget = self.containers.get("stackedWidget", {}).get("instance")
        progress_page = self.containers.get("softwareUpdateProgressPage", {}).get("instance")
        log_text = self.content_elements.get("logTextEdit", {}).get("instance")
        
        if stacked_widget and progress_page:
            stacked_widget.setCurrentWidget(progress_page)
            print("Switched to software update progress page")
            
            if log_text:
                log_text.append("Software update in progress...")
                print("Added log message to text edit")
            else:
                print("WARNING: Could not add log message - logTextEdit not found")
        else:
            print("ERROR: Cannot update software - required widgets missing")
            
        # Actual implementation would include code to:
        # 1. Check for network connectivity
        # 2. Download updates
        # 3. Verify downloaded packages
        # 4. Apply updates
        # 5. Restart system if necessary
