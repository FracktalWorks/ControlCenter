from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QListWidget, QLabel, QToolButton
from utils.helpers import check_ui_elements

class PrintFromLocation(QWidget):
    def __init__(self, main_window):
        super(PrintFromLocation, self).__init__()
        self.main_window = main_window

        # Load the UI
        self._load_ui()
        
        # Initialize UI components
        self._initialize_ui_components()
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Connect signals to slots
        self._connect_buttons()

        # Set the default screen to printLocationPage if it exists
        self._set_default_page()

    def _load_ui(self):
        """Load the UI file with proper error handling"""
        try:
            uic.loadUi('src/ui/print_from_location/print_from_location.ui', self)
            print("PrintFromLocation UI loaded successfully")
        except Exception as e:
            print(f"Failed to load PrintFromLocation UI file: {e}")

    def _initialize_ui_components(self):
        """Initialize all UI components with proper typing using dictionaries for organization"""
        # Main container widget
        self.container_widgets = {
            "stackedWidget": {"type": QStackedWidget, "instance": None}
        }
        
        # Pages for stacked widget
        self.pages = {
            "printLocationPage": {"type": QWidget, "instance": None},
            "fileListLocalPage": {"type": QWidget, "instance": None},
            "fileListUSBPage": {"type": QWidget, "instance": None},
            "printSelectedLocalPage": {"type": QWidget, "instance": None},
            "printSelectedUSBPage": {"type": QWidget, "instance": None}
        }
        
        # USB storage related buttons
        self.usb_storage_buttons = {
            "USBStorageBackButton": {"type": QPushButton, "instance": None},
            "USBStorageScrollDown": {"type": QPushButton, "instance": None},
            "USBStorageScrollUp": {"type": QPushButton, "instance": None},
            "USBStorageSelectButton": {"type": QPushButton, "instance": None},
            "USBStorageSaveButton": {"type": QPushButton, "instance": None}
        }
        
        # Local storage related buttons
        self.local_storage_buttons = {
            "localStorageBackButton": {"type": QPushButton, "instance": None},
            "localStorageScrollDown": {"type": QPushButton, "instance": None},
            "localStorageScrollUp": {"type": QPushButton, "instance": None},
            "localStorageSelectButton": {"type": QPushButton, "instance": None},
            "localStorageDeleteButton": {"type": QPushButton, "instance": None}
        }
        
        # Location selection buttons
        self.location_buttons = {
            "fromUsbButton": {"type": QPushButton, "instance": None},
            "fromLocalButton": {"type": QPushButton, "instance": None},
            "printLocationScreenBackButton": {"type": QPushButton, "instance": None}
        }
        
        # Selected file buttons - USB
        self.usb_file_buttons = {
            "fileSelectedUSBPrintButton": {"type": QToolButton, "instance": None},
            "fileSelectedUSBTransferButton": {"type": QToolButton, "instance": None},
            "fileSelectedUSBBackButton": {"type": QPushButton, "instance": None}
        }
        
        # Selected file buttons - Local
        self.local_file_buttons = {
            "fileSelectedLocalPrintButton": {"type": QPushButton, "instance": None},
            "fileSelectedLocalBackButton": {"type": QPushButton, "instance": None}
        }
        
        # List widgets and labels
        self.list_widgets = {
            "fileListWidgetLocal": {"type": QListWidget, "instance": None},
            "fileListWidgetUSB": {"type": QListWidget, "instance": None}
        }
        
        # Preview and info labels
        self.info_labels = {
            "fileSelectedLocalName": {"type": QLabel, "instance": None},
            "fileSelectedUSBName": {"type": QLabel, "instance": None},
            "printPreviewSelectedLocal": {"type": QLabel, "instance": None},
            "printPreviewSelectedUSB": {"type": QLabel, "instance": None}
        }
        
        # Combine all component dictionaries for easier iteration
        self.all_components = {}
        self.all_components.update(self.container_widgets)
        self.all_components.update(self.pages)
        self.all_components.update(self.usb_storage_buttons)
        self.all_components.update(self.local_storage_buttons)
        self.all_components.update(self.location_buttons)
        self.all_components.update(self.usb_file_buttons)
        self.all_components.update(self.local_file_buttons)
        self.all_components.update(self.list_widgets)
        self.all_components.update(self.info_labels)
        
        # Find all components using the dictionary
        self._find_components()

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
                print(f"Found {component_type.__name__} '{name}'")
            else:
                print(f"WARNING: Could not find {component_type.__name__} '{name}' in UI")

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        # Create mappings of component categories for reporting
        component_groups = {
            "PrintFromLocation - Main Widgets": {name: info["instance"] for name, info in self.container_widgets.items()},
            "PrintFromLocation - Pages": {name: info["instance"] for name, info in self.pages.items()},
            "PrintFromLocation - USB Storage Buttons": {name: info["instance"] for name, info in self.usb_storage_buttons.items()},
            "PrintFromLocation - Local Storage Buttons": {name: info["instance"] for name, info in self.local_storage_buttons.items()},
            "PrintFromLocation - Location Selection Buttons": {name: info["instance"] for name, info in self.location_buttons.items()},
            "PrintFromLocation - USB File Buttons": {name: info["instance"] for name, info in self.usb_file_buttons.items()},
            "PrintFromLocation - Local File Buttons": {name: info["instance"] for name, info in self.local_file_buttons.items()},
            "PrintFromLocation - List Widgets": {name: info["instance"] for name, info in self.list_widgets.items()},
            "PrintFromLocation - Info Labels": {name: info["instance"] for name, info in self.info_labels.items()}
        }
        
        # Check each component group
        for group_name, components in component_groups.items():
            check_ui_elements(self, components, group_name)

    def _set_default_page(self):
        """Set the default page in stacked widget"""
        stackedWidget = self.container_widgets["stackedWidget"]["instance"]
        printLocationPage = self.pages["printLocationPage"]["instance"]
        
        if stackedWidget and printLocationPage:
            stackedWidget.setCurrentWidget(printLocationPage)
            print("Set initial page to printLocationPage")
        else:
            print("WARNING: Could not set default page - required widgets missing")

    def _connect_buttons(self):
        """Connect all button signals with safety checks to prevent NoneType errors"""
        # Map buttons to their handler functions
        button_connections = [
            # USB storage navigation
            {"dict": self.usb_storage_buttons, "name": "USBStorageBackButton", "handler": self._usb_storage_back},
            {"dict": self.usb_storage_buttons, "name": "USBStorageScrollDown", "handler": self._usb_scroll_down},
            {"dict": self.usb_storage_buttons, "name": "USBStorageScrollUp", "handler": self._usb_scroll_up},
            {"dict": self.usb_storage_buttons, "name": "USBStorageSelectButton", "handler": self.printSelectedUSB},
            {"dict": self.usb_storage_buttons, "name": "USBStorageSaveButton", "handler": self.transferToLocal},
            
            # Local storage navigation
            {"dict": self.local_storage_buttons, "name": "localStorageBackButton", "handler": self._local_storage_back},
            {"dict": self.local_storage_buttons, "name": "localStorageScrollDown", "handler": self._local_scroll_down},
            {"dict": self.local_storage_buttons, "name": "localStorageScrollUp", "handler": self._local_scroll_up},
            {"dict": self.local_storage_buttons, "name": "localStorageSelectButton", "handler": self.printSelectedLocal},
            {"dict": self.local_storage_buttons, "name": "localStorageDeleteButton", "handler": self.deleteItem},
            
            # Location selection buttons
            {"dict": self.location_buttons, "name": "fromUsbButton", "handler": self.fileListUSB},
            {"dict": self.location_buttons, "name": "fromLocalButton", "handler": self.fileListLocal},
            {"dict": self.location_buttons, "name": "printLocationScreenBackButton", "handler": self.main_window.switch_to_previous_screen},
            
            # Selected file buttons - USB
            {"dict": self.usb_file_buttons, "name": "fileSelectedUSBPrintButton", "handler": self.printFile},
            {"dict": self.usb_file_buttons, "name": "fileSelectedUSBTransferButton", "handler": self.transferToLocal},
            {"dict": self.usb_file_buttons, "name": "fileSelectedUSBBackButton", "handler": self.fileListUSB},
            
            # Selected file buttons - Local
            {"dict": self.local_file_buttons, "name": "fileSelectedLocalPrintButton", "handler": self.printFile},
            {"dict": self.local_file_buttons, "name": "fileSelectedLocalBackButton", "handler": self.fileListLocal}
        ]
        
        # Connect each button to its handler with safety check
        for connection in button_connections:
            button_dict = connection["dict"]
            button_name = connection["name"]
            handler = connection["handler"]
            
            button = button_dict.get(button_name, {}).get("instance")
            if button:
                button.clicked.connect(handler)
                print(f"Connected {button_name} to handler")
            else:
                print(f"WARNING: Could not connect {button_name} - button not found")

    # Helper methods for button connections
    def _usb_storage_back(self):
        """Handle back button in USB storage page"""
        stackedWidget = self.container_widgets["stackedWidget"]["instance"]
        printLocationPage = self.pages["printLocationPage"]["instance"]
        
        if stackedWidget and printLocationPage:
            stackedWidget.setCurrentWidget(printLocationPage)
            print("USB Storage: going back to location selection")

    def _local_storage_back(self):
        """Handle back button in local storage page"""
        stackedWidget = self.container_widgets["stackedWidget"]["instance"]
        printLocationPage = self.pages["printLocationPage"]["instance"]
        
        if stackedWidget and printLocationPage:
            stackedWidget.setCurrentWidget(printLocationPage)
            print("Local Storage: going back to location selection")
        else:
            print("Using fallback for localStorageBackButton")
            self.main_window.switch_to_previous_screen()

    def _usb_scroll_down(self):
        """Handle scroll down in USB file list"""
        fileListWidgetUSB = self.list_widgets["fileListWidgetUSB"]["instance"]
        if fileListWidgetUSB:
            current_row = fileListWidgetUSB.currentRow()
            fileListWidgetUSB.setCurrentRow(current_row + 1)
            print("USB Storage: scrolling down")

    def _usb_scroll_up(self):
        """Handle scroll up in USB file list"""
        fileListWidgetUSB = self.list_widgets["fileListWidgetUSB"]["instance"]
        if fileListWidgetUSB:
            current_row = fileListWidgetUSB.currentRow()
            fileListWidgetUSB.setCurrentRow(current_row - 1)
            print("USB Storage: scrolling up")

    def _local_scroll_down(self):
        """Handle scroll down in local file list"""
        fileListWidgetLocal = self.list_widgets["fileListWidgetLocal"]["instance"]
        if fileListWidgetLocal:
            current_row = fileListWidgetLocal.currentRow()
            fileListWidgetLocal.setCurrentRow(current_row + 1)
            print("Local Storage: scrolling down")

    def _local_scroll_up(self):
        """Handle scroll up in local file list"""
        fileListWidgetLocal = self.list_widgets["fileListWidgetLocal"]["instance"]
        if fileListWidgetLocal:
            current_row = fileListWidgetLocal.currentRow()
            fileListWidgetLocal.setCurrentRow(current_row - 1)
            print("Local Storage: scrolling up")

    def fileListLocal(self):
        """Shows the local file list screen and populates the list with local files"""
        print("Showing local file list")
        stackedWidget = self.container_widgets["stackedWidget"]["instance"]
        fileListLocalPage = self.pages["fileListLocalPage"]["instance"]
        
        if stackedWidget and fileListLocalPage:
            stackedWidget.setCurrentWidget(fileListLocalPage)
            print("Switched to local file list")
        # TODO: Populate file list from octoprint server

    def fileListUSB(self):
        """Shows the USB file list screen and populates the list with USB files"""
        print("Showing USB file list")
        stackedWidget = self.container_widgets["stackedWidget"]["instance"]
        fileListUSBPage = self.pages["fileListUSBPage"]["instance"]
        
        if stackedWidget and fileListUSBPage:
            stackedWidget.setCurrentWidget(fileListUSBPage)
            print("Switched to USB file list")
        # TODO: Populate file list from USB drive

    def printSelectedLocal(self):
        """Displays the selected local file details before printing"""
        print("Displaying selected local file")
        fileListWidgetLocal = self.list_widgets["fileListWidgetLocal"]["instance"]
        stackedWidget = self.container_widgets["stackedWidget"]["instance"]
        printSelectedLocalPage = self.pages["printSelectedLocalPage"]["instance"]
        
        if fileListWidgetLocal and fileListWidgetLocal.currentItem():
            # TODO: Get file details and preview
            if stackedWidget and printSelectedLocalPage:
                stackedWidget.setCurrentWidget(printSelectedLocalPage)
                print("Showing selected local file details")
        else:
            print("No file selected")

    def printSelectedUSB(self):
        """Displays the selected USB file details before printing"""
        print("Displaying selected USB file")
        fileListWidgetUSB = self.list_widgets["fileListWidgetUSB"]["instance"]
        stackedWidget = self.container_widgets["stackedWidget"]["instance"]
        printSelectedUSBPage = self.pages["printSelectedUSBPage"]["instance"]
        
        if fileListWidgetUSB and fileListWidgetUSB.currentItem():
            # TODO: Get file details and preview
            if stackedWidget and printSelectedUSBPage:
                stackedWidget.setCurrentWidget(printSelectedUSBPage)
                print("Showing selected USB file details")
        else:
            print("No file selected")

    def printFile(self):
        """Sends the selected file to printer and starts printing"""
        print("Printing file")
        # TODO: Send file to printer and switch to the home screen to show print progress
        self.main_window.switch_to_home_screen()

    def deleteItem(self):
        """Deletes the selected local file"""
        print("Deleting file")
        fileListWidgetLocal = self.list_widgets["fileListWidgetLocal"]["instance"]
        
        if fileListWidgetLocal and fileListWidgetLocal.currentItem():
            # TODO: Delete the selected file
            print(f"Deleting file: {fileListWidgetLocal.currentItem().text()}")
        else:
            print("No file selected to delete")

    def transferToLocal(self):
        """Transfers the selected USB file to local storage"""
        print("Transferring file from USB to local storage")
        fileListWidgetUSB = self.list_widgets["fileListWidgetUSB"]["instance"]
        
        if fileListWidgetUSB and fileListWidgetUSB.currentItem():
            # TODO: Copy the file from USB to local storage
            print(f"Transferring file: {fileListWidgetUSB.currentItem().text()}")
        else:
            print("No file selected to transfer")