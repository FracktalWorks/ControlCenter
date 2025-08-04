from PyQt5.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QButtonGroup, QSizePolicy, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5 import uic
from ui.home_screen.home_screen import HomeScreen
from ui.settings_screen.settings_screen import SettingsScreen
from ui.control_screen.control_screen import ControlScreen
from ui.print_from_location.print_from_location import PrintFromLocation
from ui.calibrate_screen.calibrate_screen import CalibrateScreen
from utils.logger import get_logger
from utils.helpers import check_ui_elements
import ui.resources.resource_rc  # Ensure resources are loaded
from utils.styles import printer_status_red, printer_status_green, printer_status_amber, printer_status_blue
from utils.dialog import WarningOk, WarningYesNo
from utils import dialog
import config
import os


logger = get_logger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, controller=None):
        super(MainWindow, self).__init__()
        logger.info("Initializing MainWindow")

        # Set controller (should be provided by MainController)
        self.controller = controller or self._create_fallback_controller()
        
        # Load UI and get element references
        self._load_ui()
        
        # Setup connections and configuration
        self._setup_ui()
        
        # Get references to controller components
        self.octoprint_client = self.controller.get_octoprint_client()
        self.printer_model = self.controller.get_printer_model()
        self.minimal_ui_mode = False

        # Initialize screen navigation
        self.screen_history = []
        self.current_screen = None
        self.next_screen = None
        self.dialogShown = False

        try:
            # Set window size from config but don't show yet - loading screen controls visibility
            self.resize(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
            
            # Load basic UI structure but don't load all screens yet
            # This will be done by loadFullUI() or showMinimalUI()
            
            logger.info("MainWindow initialized successfully - waiting for connection result")

        except Exception as e:
            logger.exception("Error during MainWindow initialization")
            WarningOk(self, f"Application Error: {str(e)}", overlay=True)

    def load_full_functionality(self):
        """Load all screens and enable full functionality."""
        logger.info("Loading all screens...")
        
        # Load all screens
        self.load_home_screen()
        self.load_settings_screen()
        self.load_control_screen()
        self.load_print_location_screen()
        self.load_calibration_screens()

        # Enable tab button connections
        self._connect_tab_buttons()
        
        # Start with the home screen
        self.switch_to_home_screen()
        
        logger.info("All screens loaded successfully")
        return True

    def _connect_tab_buttons(self):
        """Connect tab buttons to their respective screen switching methods."""
        self.homeTab.clicked.connect(self.switch_to_home_screen)
        self.controlTab.clicked.connect(self.switch_to_control_screen)  # Control tab maps to control screen
        self.printTab.clicked.connect(self.switch_to_print_location_screen)
        self.calibrateTab.clicked.connect(self.switch_to_calibrate_screen)
        self.materialNozzleTab.clicked.connect(self.switch_to_control_screen)
        self.settingsTab.clicked.connect(self.switch_to_settings_screen)

    def _update_tab_selection(self, active_tab_name):
        """Update which tab button is checked based on current screen."""
        # Use the button group for clean mutual exclusivity
        for button in self.tab_button_group.buttons():
            button.setChecked(False)
        
        # Check the appropriate tab
        tab_mapping = {
            'home': self.homeTab,
            'control': self.controlTab,  # Control tab (new)
            'print': self.printTab,
            'calibrate': self.calibrateTab,
            'material': self.materialNozzleTab,  # Keep material/nozzle separate
            'settings': self.settingsTab
        }
        
        if active_tab_name in tab_mapping:
            tab_mapping[active_tab_name].setChecked(True)

    def _load_ui(self):
        """Load UI file and get element references."""
        # Load the UI file into a central widget
        ui_file_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        self.central_widget = uic.loadUi(ui_file_path)
        self.setCentralWidget(self.central_widget)

        # Get references to UI elements
        self.homeTab = self.central_widget.findChild(QPushButton, 'homeTab')
        self.controlTab = self.central_widget.findChild(QPushButton, 'controlTab')
        self.printTab = self.central_widget.findChild(QPushButton, 'printTab')
        self.calibrateTab = self.central_widget.findChild(QPushButton, 'calibrateTab')
        self.materialNozzleTab = self.central_widget.findChild(QPushButton, 'materialNozzleTab')
        self.settingsTab = self.central_widget.findChild(QPushButton, 'settingsTab')
        self.stackedWidget = self.central_widget.findChild(QStackedWidget, 'mainStackedWidget')

        # Verify all UI elements were found
        ui_elements = [self.homeTab, self.controlTab, self.printTab, self.calibrateTab, 
                      self.materialNozzleTab, self.settingsTab, self.stackedWidget]
        check_ui_elements(self, ui_elements, "MainWindow")
        
        # Ensure critical elements exist
        if not self.homeTab or not self.stackedWidget:
            raise RuntimeError("Critical UI elements not found")

    def _setup_ui(self):
        """Setup UI connections and configuration."""
        # Set main window size first
        import config
        self.resize(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        self.setMinimumSize(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        
        # Configure widget sizing and layout management
        if self.stackedWidget:
            self.stackedWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # Ensure stacked widget properly manages its children's sizes
            self.stackedWidget.setContentsMargins(0, 0, 0, 0)
            
            # Create a layout for the stacked widget's parent if it doesn't have one
            self._setup_layout_management()
            
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set up tab button group for exclusive selection
        self.tab_button_group = QButtonGroup(self)
        for tab in [self.homeTab, self.controlTab, self.printTab, 
                   self.calibrateTab, self.materialNozzleTab, self.settingsTab]:
            self.tab_button_group.addButton(tab)

        # Connect controller signals
        self._connect_controller_signals()
    
    def _setup_layout_management(self):
        """Set up proper layout management for automatic resizing."""
        try:
            # If the central widget doesn't have a layout, create one
            if not self.central_widget.layout():
                logger.debug("Setting up layout management for central widget")
                
                # Create a main layout for the central widget
                main_layout = QVBoxLayout(self.central_widget)
                main_layout.setContentsMargins(0, 0, 0, 0)
                main_layout.setSpacing(0)
                
                # If stackedWidget has a parent that's not the central widget, 
                # we need to set up the layout hierarchy properly
                stacked_parent = self.stackedWidget.parent()
                if stacked_parent and stacked_parent != self.central_widget:
                    # Create layout for the stacked widget's immediate parent
                    if not stacked_parent.layout():
                        parent_layout = QVBoxLayout(stacked_parent)
                        parent_layout.setContentsMargins(0, 0, 0, 0)
                        parent_layout.setSpacing(0)
                        parent_layout.addWidget(self.stackedWidget)
                        logger.debug("Created layout for stackedWidget parent")
                
                # Ensure stackedWidget expands properly
                self.stackedWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
                logger.debug("Layout management setup completed")
            else:
                logger.debug("Central widget already has a layout")
                
        except Exception as e:
            logger.error(f"Error setting up layout management: {e}")
    
    def _create_widget_container_with_layout(self, widget):
        """Create a container widget with proper layout for the given widget."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(widget)
        
        # Set size policies for proper scaling
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        return container
        
    


    def _connect_controller_signals(self):
        """Connect controller signals to UI handlers."""
        self.controller.startup_success.connect(self._on_startup_success)
        self.controller.startup_error.connect(self._on_startup_error)
        self.controller.printer_error.connect(self._on_printer_error)
        self.controller.probing_failed.connect(self._on_probing_failed)

    def _on_startup_success(self):
        """Handle successful startup."""
        # Controller will handle enabling full UI mode
        pass

    def _on_startup_error(self):
        """Handle startup error."""
        # Controller will determine whether to show minimal UI directly
        pass

    def _on_printer_error(self, message, overlay):
        """Handle printer error messages."""
        if not self.dialogShown:
            self.dialogShown = True
            if WarningOk(self, message, overlay=overlay):
                self.dialogShown = False
                self.controller.reset_dialog_flag()

    def _on_probing_failed(self, message, overlay):
        """Handle probing failure messages."""
        if not self.dialogShown:
            self.dialogShown = True
            if WarningOk(self, message, overlay=overlay):
                self.dialogShown = False
                self.controller.reset_dialog_flag()

    def handleStartupError(self):
        """
        Error Handler when Octoprint gives up - now delegates to controller
        """
        logger.info("MainWindow.handleStartupError started")
        try:
            if WarningYesNo(self, "Server Error, Restore failsafe settings?", overlay=True):
                logger.info("User chose to restore failsafe settings")
                if self.controller.restore_failsafe_settings():
                    # Restart will be handled by the controller
                    pass
                else:
                    logger.error("Failed to restore failsafe settings")
                    self.controller.enable_minimal_ui_mode()
            else:
                logger.info("User chose not to restore failsafe settings, going to minimal UI")
                self.controller.enable_minimal_ui_mode()
        except Exception as e:
            logger.error("Error in MainWindow.handleStartupError: {}".format(e))
            WarningOk(self, "Error in MainWindow.handleStartupError: {}".format(e), overlay=True)

    def showMinimalUI(self):
        """
        Show a minimal UI with a message indicating that the server is not reachable.
        Only home screen and settings screen are accessible in this mode.
        """
        logger.info("Showing minimal UI due to startup error")
        
        # Load basic screens if not loaded yet (at minimum home and settings)
        if not hasattr(self, 'home_screen') or self.home_screen is None:
            self.load_home_screen()
            self.load_settings_screen()
            self._connect_tab_buttons()

        # Set the minimal UI mode flag
        self.minimal_ui_mode = True
        print(".......LOADED IN MINIMAL MODE .......")

        # Show a message to the user about the limited functionality
        WarningOk(
            self,
            "Server Connection Error\n\nThe printer server is not reachable. Only basic features are available.\n\n"
            "Please check your network connection and printer status.",
            overlay=True
        )

        # Disable buttons in various screens
        self._disable_buttons_for_minimal_ui()

        # Switch to the home screen initially
        self.switch_to_home_screen()

        # Show a visual indicator on the home screen that we're in limited mode
        self._update_home_screen_for_minimal_ui()
        
        # Refresh home screen layout to ensure proper display
        if hasattr(self, 'refresh_home_screen_layout'):
            self.refresh_home_screen_layout()
            
        # Force a complete layout update
        self.force_layout_update()

    def _disable_buttons_for_minimal_ui(self):
        """Disable buttons that require server connection."""
        # Disable tab buttons that require server connection
        self.controlTab.setDisabled(True)  # Control tab
        self.printTab.setDisabled(True)
        self.calibrateTab.setDisabled(True)
        self.materialNozzleTab.setDisabled(True)
        
        # Disable buttons in Home Screen (only if loaded)
        if hasattr(self, 'home_screen') and self.home_screen:
            if hasattr(self.home_screen, 'stopButton') and self.home_screen.stopButton:
                self.home_screen.stopButton.setDisabled(True)
            if hasattr(self.home_screen, 'controlButton') and self.home_screen.controlButton:
                self.home_screen.controlButton.setDisabled(True)
            if hasattr(self.home_screen, 'playPauseButton') and self.home_screen.playPauseButton:
                self.home_screen.playPauseButton.setDisabled(True)

        # Check for software update related buttons (only if settings screen is loaded)
        if hasattr(self, 'settings_screen') and self.settings_screen:
            if hasattr(self.settings_screen, 'softwareUpdateBackButton') and self.settings_screen.softwareUpdateBackButton:
                self.settings_screen.softwareUpdateBackButton.setDisabled(True)
            if hasattr(self.settings_screen, 'performUpdateButton') and self.settings_screen.performUpdateButton:
                self.settings_screen.performUpdateButton.setDisabled(True)

        # Check for filament sensor toggle (only if control screen is loaded)
        if hasattr(self, 'control_screen') and self.control_screen:
            if hasattr(self.control_screen, 'toggleFilamentSensorButton') and self.control_screen.toggleFilamentSensorButton:
                self.control_screen.toggleFilamentSensorButton.setDisabled(True)

    def _update_home_screen_for_minimal_ui(self):
        """Update home screen to show disconnected status."""
        if hasattr(self.home_screen, 'printerStatus') and self.home_screen.printerStatus:
            self.home_screen.printerStatus.setText("Disconnected - Limited Mode")
        if hasattr(self.home_screen, 'printerStatusColour') and self.home_screen.printerStatusColour:
            self.home_screen.printerStatusColour.setStyleSheet(printer_status_red)

    def loadFullUI(self):
        """
        Load the full UI when OctoPrint is connected successfully.
        All screens will be accessible in this mode.
        """
        logger.info("Loading full UI - OctoPrint connection successful")

        # Load all screens if not loaded
        self.load_full_functionality()

        # Reset the minimal UI mode flag
        self.minimal_ui_mode = False
        print(".......LOADED IN FULL MODE .......")

        # Get websocket instance from controller
        self.octoprint_websocket = self.controller.get_octoprint_websocket()

        # Re-enable buttons that were disabled in showMinimalUI
        self._enable_buttons_for_full_ui()

        # Update home screen connection status
        self._update_home_screen_for_full_ui()

        # Switch to the home screen
        self.switch_to_home_screen()
        if hasattr(self, 'home_screen') and self.home_screen:
            self.home_screen.setIPStatus()
            # Refresh home screen layout
            self.refresh_home_screen_layout()

        # Force a complete layout update to ensure everything is properly sized
        self.force_layout_update()

        # Start updating printer status if implemented
        if hasattr(self.home_screen, 'update_ui_from_printer_status'):
            self.home_screen.update_ui_from_printer_status()

    def _enable_buttons_for_full_ui(self):
        """Enable buttons that require server connection."""
        # Enable tab buttons that require server connection
        self.controlTab.setEnabled(True)  # Control tab
        self.printTab.setEnabled(True)
        self.calibrateTab.setEnabled(True)
        self.materialNozzleTab.setEnabled(True)
        
        # Enable buttons in Home Screen
        if hasattr(self.home_screen, 'stopButton') and self.home_screen.stopButton:
            self.home_screen.stopButton.setEnabled(True)
        if hasattr(self.home_screen, 'controlButton') and self.home_screen.controlButton:
            self.home_screen.controlButton.setEnabled(True)
        if hasattr(self.home_screen, 'playPauseButton') and self.home_screen.playPauseButton:
            self.home_screen.playPauseButton.setEnabled(True)

        # Check for software update related buttons
        if hasattr(self.settings_screen, 'softwareUpdateBackButton') and self.settings_screen.softwareUpdateBackButton:
            self.settings_screen.softwareUpdateBackButton.setEnabled(True)
        if hasattr(self.settings_screen, 'performUpdateButton') and self.settings_screen.performUpdateButton:
            self.settings_screen.performUpdateButton.setEnabled(True)

        # Check for filament sensor toggle
        if hasattr(self.control_screen, 'toggleFilamentSensorButton') and self.control_screen.toggleFilamentSensorButton:
            self.control_screen.toggleFilamentSensorButton.setEnabled(True)

    def _update_home_screen_for_full_ui(self):
        """Update home screen to show connected status."""
        if hasattr(self.home_screen, 'printerStatus') and self.home_screen.printerStatus:
            self.home_screen.printerStatus.setText("Connected")
        if hasattr(self.home_screen, 'printerStatusColour') and self.home_screen.printerStatusColour:
            self.home_screen.printerStatusColour.setStyleSheet(printer_status_green)
    # Screen Loading Methods
    def load_home_screen(self):
        logger.debug("Loading home screen")
        try:
            self.home_screen = HomeScreen(self)
            
            # Create a container with layout for proper resizing
            home_container = self._create_widget_container_with_layout(self.home_screen)
            self.stackedWidget.addWidget(home_container)
            
            # Store reference to the container for easy access
            self.home_screen_container = home_container
            
            logger.debug("Home screen loaded successfully with layout container")
        except Exception as e:
            logger.exception("Failed to load home screen")
            raise

    def load_settings_screen(self):
        logger.debug("Loading settings screen")
        try:
            self.settings_screen = SettingsScreen(self)
            
            # Create a container with layout for proper resizing
            settings_container = self._create_widget_container_with_layout(self.settings_screen)
            self.stackedWidget.addWidget(settings_container)
            
            # Store reference to the container
            self.settings_screen_container = settings_container
            
            logger.debug("Settings screen loaded successfully with layout container")
        except Exception as e:
            logger.exception("Failed to load settings screen")
            raise

    def load_control_screen(self):
        logger.debug("Loading control screen")
        try:
            self.control_screen = ControlScreen(self)
            
            # Create a container with layout for proper resizing
            control_container = self._create_widget_container_with_layout(self.control_screen)
            self.stackedWidget.addWidget(control_container)
            
            # Store reference to the container
            self.control_screen_container = control_container
            
            logger.debug("Control screen loaded successfully with layout container")
        except Exception as e:
            logger.exception("Failed to load control screen")
            raise

    def load_print_location_screen(self):
        logger.debug("Loading print location screen")
        try:
            self.print_location_screen = PrintFromLocation(self)
            
            # Create a container with layout for proper resizing
            print_container = self._create_widget_container_with_layout(self.print_location_screen)
            self.stackedWidget.addWidget(print_container)
            
            # Store reference to the container
            self.print_location_screen_container = print_container
            
            logger.debug("Print location screen loaded successfully with layout container")
        except Exception as e:
            logger.exception("Failed to load print location screen")
            raise

    def load_calibration_screens(self):
        logger.debug("Loading calibration screens")
        try:
            # Main calibration screen
            self.calibrate_screen = CalibrateScreen(self)
            
            # Create a container with layout for proper resizing
            calibrate_container = self._create_widget_container_with_layout(self.calibrate_screen)
            self.stackedWidget.addWidget(calibrate_container)
            
            # Store reference to the container
            self.calibrate_screen_container = calibrate_container

            logger.debug("Calibration screen loaded successfully with layout container")
        except Exception as e:
            logger.exception("Failed to load calibration screens")
            raise

    # Screen Navigation Methods
    def switch_screen(self, widget):
        """Switch to the given screen and update navigation history."""
        # If widget is a screen widget, find its container
        target_container = widget
        
        # Check if this widget is one of our screen widgets, and get its container instead
        screen_to_container_map = {
            getattr(self, 'home_screen', None): getattr(self, 'home_screen_container', None),
            getattr(self, 'settings_screen', None): getattr(self, 'settings_screen_container', None),
            getattr(self, 'control_screen', None): getattr(self, 'control_screen_container', None),
            getattr(self, 'print_location_screen', None): getattr(self, 'print_location_screen_container', None),
            getattr(self, 'calibrate_screen', None): getattr(self, 'calibrate_screen_container', None),
        }
        
        if widget in screen_to_container_map and screen_to_container_map[widget] is not None:
            target_container = screen_to_container_map[widget]
            logger.debug(f"Switching to container for screen: {widget.__class__.__name__}")
        
        logger.debug(f"Switching to screen: {widget.__class__.__name__}")
        logger.debug(
            f"Current screen before switch: {self.current_screen.__class__.__name__ if self.current_screen else None}")

        # Check if we're navigating between a main screen and its subscreens
        is_subscreen_navigation = False

        # Check if current screen has subscreens and the widget is one of those subscreens
        if self.current_screen and hasattr(self.current_screen, 'screens'):
            is_subscreen_navigation = any(widget == subscreen for subscreen in self.current_screen.screens.values())

        # Check if widget has subscreens and the current_screen is one of those subscreens
        if widget and hasattr(widget, 'screens') and self.current_screen:
            is_subscreen_navigation = is_subscreen_navigation or any(
                self.current_screen == subscreen for subscreen in widget.screens.values())

        # Only update history if not navigating between a screen and its subscreens
        if self.current_screen is not None and not is_subscreen_navigation:
            self.screen_history.append(self.current_screen)
            logger.debug(f"Added {self.current_screen.__class__.__name__} to history")

        self.current_screen = widget  # Keep reference to the actual screen widget
        self.stackedWidget.setCurrentWidget(target_container)  # But switch to its container

        logger.debug(f"History now contains: {[screen.__class__.__name__ for screen in self.screen_history]}")

    def _get_current_screen_widget(self):
        """Get the actual screen widget from the current stacked widget page."""
        current_container = self.stackedWidget.currentWidget()
        if current_container and current_container.layout():
            # Get the first (and should be only) widget from the container's layout
            layout_item = current_container.layout().itemAt(0)
            if layout_item:
                return layout_item.widget()
        return current_container

    def switch_to_previous_screen(self):
        """Go back to the previous screen in history."""
        logger.debug("Switching to previous screen")
        if self.screen_history:
            previous_screen = self.screen_history.pop()
            self.current_screen = previous_screen
            self.stackedWidget.setCurrentWidget(previous_screen)
            logger.debug(f"Switched to previous screen: {previous_screen.__class__.__name__}")
        else:
            # Default to home screen if no history exists
            logger.debug("No screen history, defaulting to home screen")
            self.switch_to_home_screen()

        # Ensure the stacked widget's current page is updated for multi-step wizards
        if hasattr(self.current_screen, 'stackedWidget') and self.current_screen.stackedWidget:
            self.current_screen.stackedWidget.setCurrentIndex(0)

    def switch_to_next_screen(self):
        """Used in multi-step flows like wizards to go to the next screen."""
        logger.debug("Attempting to switch to next screen")
        if self.next_screen:
            self.switch_screen(self.next_screen)
            self.next_screen = None
            logger.debug("Switched to next screen")
        else:
            # If no next screen is defined, do nothing or go to a default
            logger.warning("No next screen defined")

    # Direct navigation methods for main screens
    def switch_to_home_screen(self):
        logger.debug("Switching to home screen")
        # Ensure home screen is loaded
        if not hasattr(self, 'home_screen') or self.home_screen is None:
            logger.debug("Home screen not loaded, loading now...")
            self.load_home_screen()
        
        self.switch_screen(self.home_screen)
        self._update_tab_selection('home')
        
        # Ensure the home screen is properly visible
        if self.home_screen:
            self.home_screen.show()
            self.home_screen.setVisible(True)
            
            # Force layout update to ensure proper sizing
            current_container = self.stackedWidget.currentWidget()
            if current_container:
                current_container.updateGeometry()
                if current_container.layout():
                    current_container.layout().update()
                    
            logger.debug("Home screen set as current widget and layout updated")

    def refresh_home_screen_layout(self):
        """Force refresh of home screen layout and sizing."""
        if hasattr(self, 'home_screen') and self.home_screen:
            logger.debug("Refreshing home screen layout")
            
            # Update both the screen widget and its container
            self.home_screen.updateGeometry()
            self.home_screen.update()
            
            # Update the container if it exists
            if hasattr(self, 'home_screen_container') and self.home_screen_container:
                self.home_screen_container.updateGeometry()
                if self.home_screen_container.layout():
                    self.home_screen_container.layout().update()
            
            # Force stack widget to update
            self.stackedWidget.updateGeometry()
            logger.debug("Home screen layout refresh completed")
    
    def force_layout_update(self):
        """Force a complete layout update of the main window and all screens."""
        logger.debug("Forcing complete layout update")
        
        try:
            # Update main window geometry
            self.updateGeometry()
            
            # Update central widget
            if hasattr(self, 'central_widget') and self.central_widget:
                self.central_widget.updateGeometry()
                if self.central_widget.layout():
                    self.central_widget.layout().update()
            
            # Update stacked widget
            if self.stackedWidget:
                self.stackedWidget.updateGeometry()
                
                # Update all containers in the stacked widget
                for i in range(self.stackedWidget.count()):
                    container = self.stackedWidget.widget(i)
                    if container:
                        container.updateGeometry()
                        if container.layout():
                            container.layout().update()
                            
                            # Update the screen widget inside the container
                            layout_item = container.layout().itemAt(0)
                            if layout_item and layout_item.widget():
                                screen_widget = layout_item.widget()
                                screen_widget.updateGeometry()
            
            # Force a repaint
            self.update()
            logger.debug("Complete layout update finished")
            
        except Exception as e:
            logger.error(f"Error during force layout update: {e}")
    
    def resizeEvent(self, event):
        """Handle main window resize events."""
        super().resizeEvent(event)
        try:
            new_size = event.size()
            logger.debug(f"Main window resized to: {new_size.width()}x{new_size.height()}")
            
            # Force layout update on resize to ensure all children resize properly
            self.force_layout_update()
            
        except Exception as e:
            logger.error(f"Error in main window resizeEvent: {e}")

    def switch_to_settings_screen(self):
        logger.debug("Switching to settings screen")
        self.switch_screen(self.settings_screen)
        self._update_tab_selection('settings')

    def switch_to_control_screen(self):
        """
        Sets the current page to the control page (Material/Nozzle tab)
        """
        logger.debug("Switching to control screen")
        try:
            self.switch_screen(self.control_screen)
            self._update_tab_selection('control')
            # Update temperature values from printer model
            if self.printer_model and hasattr(self.printer_model, 'temperatures'):
                if self.control_screen.toolToggleTemperatureButton.isChecked():
                    self.control_screen.toolTempSpinBox.setProperty(
                        "value", float(self.printer_model.temperatures.get("tool1", 0))
                    )
                else:
                    self.control_screen.toolTempSpinBox.setProperty(
                        "value", float(self.printer_model.temperatures.get("tool0", 0))
                    )
                self.control_screen.bedTempSpinBox.setProperty(
                    "value", float(self.printer_model.temperatures.get("bed", 0))
                )
        except Exception as e:
            logger.error("Error in MainWindow.switch_to_control_screen: {}".format(e))
            dialog.WarningOk(self, "Error in MainWindow.switch_to_control_screen: {}".format(e), overlay=True)

    def switch_to_print_location_screen(self):
        logger.debug("Switching to print location screen")
        self.switch_screen(self.print_location_screen)
        self._update_tab_selection('print')

    def switch_to_calibrate_screen(self):
        logger.debug("Switching to calibration screen")
        self.switch_screen(self.calibrate_screen)
        self._update_tab_selection('calibrate')

    def checkKlipperPrinterCFG(self):
        """
        Delegate to controller for Klipper config check.
        """
        if self.controller:
            self.controller.check_klipper_printer_cfg()

    def printRestoreMessageBox(self, file):
        """
        Displays a message box alerting the user of a filament error
        """
        logger.info("MainWindow.printRestoreMessageBox started")
        if WarningYesNo(self, file + " Did not finish, would you like to restore?"):
            response = self.controller.restore_print()
            if response and response.get("status"):
                WarningOk(self, response["status"])

    def onServerConnected(self):
        """
        When the server is connected, delegate to controller for handling
        """
        logger.info("MainWindow.onServerConnected started")
        if self.controller:
            # Handle any UI-specific updates here
            # Controller will handle the core logic
            restore_info = self.controller.handle_print_restore("")
            if restore_info:
                self.printRestoreMessageBox(restore_info['filename'])

    def isFilamentSensorInstalled(self):
        """
        Delegate filament sensor check to controller
        """
        logger.info("MainWindow.isFilamentSensorInstalled started")
        if self.controller:
            return self.controller.is_filament_sensor_installed()
        return False

    def showProbingFailed(self, msg='Probing Failed, Calibrate bed again or check for hardware issue', overlay=True):
        """
        Handle probing failure - now just shows dialog, controller handles logic
        """
        logger.info("MainWindow.showProbingFailed started")
        return WarningOk(self, msg, overlay=overlay)

    def showPrinterError(self, msg='Printer error, Check Terminal', overlay=False):
        """
        Handle printer error - now just shows dialog, controller handles logic  
        """
        logger.info("MainWindow.showPrinterError started")
        if not self.dialogShown:
            self.dialogShown = True
            if WarningOk(self, msg, overlay=overlay):
                self.dialogShown = False


    def _create_fallback_controller(self):
        """Create fallback controller for backward compatibility."""
        logger.warning("Creating controller in MainWindow - this should be avoided. Controller should own the view.")
        from controllers.main_controller import MainController
        return MainController()

