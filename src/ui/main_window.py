from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from ui.home_screen.home_screen import HomeScreen
from ui.loading_screen.loading_screen import LoadingScreen
from ui.menu_screen.menu_screen import MenuScreen
from ui.settings_screen.settings_screen import SettingsScreen
from ui.control_screen.control_screen import ControlScreen
from ui.print_from_location.print_from_location import PrintFromLocation
from ui.calibrate_screen.calibrate_screen import CalibrateScreen
from utils import logger
import ui.resources.resource_rc  # Ensure resources are loaded

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        logger.info("Initializing MainWindow")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # Screen navigation history for back button functionality
        self.screen_history = []
        self.current_screen = None
        
        # Next screen for wizard-style multi-step flows
        self.next_screen = None

        try:
            # Load all screens
            self.load_home_screen()
            self.load_loading_screen()
            self.load_menu_screen()
            self.load_settings_screen()
            self.load_control_screen()
            self.load_print_location_screen()
            self.load_calibration_screens()

            # Start with the loading screen
            self.switch_screen(self.loading_screen)

            # Adjust the size of the main window to fit its contents
            self.adjustSize()
            logger.info("MainWindow initialized successfully")
        except Exception as e:
            logger.exception("Error during MainWindow initialization")
            self.show_error_dialog("Application Error", 
                                  f"An error occurred while initializing the application: {str(e)}\n\n"
                                  f"Please check the logs for more details.")

    # Screen Loading Methods
    def load_home_screen(self):
        logger.debug("Loading home screen")
        try:
            self.home_screen = HomeScreen(self)
            self.stacked_widget.addWidget(self.home_screen)
            logger.debug("Home screen loaded successfully")
        except Exception as e:
            logger.exception("Failed to load home screen")
            raise

    def load_loading_screen(self):
        logger.debug("Loading loading screen")
        try:
            self.loading_screen = LoadingScreen(self)
            self.stacked_widget.addWidget(self.loading_screen)
            logger.debug("Loading screen loaded successfully")
        except Exception as e:
            logger.exception("Failed to load loading screen")
            raise

    def load_menu_screen(self):
        logger.debug("Loading menu screen")
        try:
            self.menu_screen = MenuScreen(self)
            self.stacked_widget.addWidget(self.menu_screen)
            logger.debug("Menu screen loaded successfully")
        except Exception as e:
            logger.exception("Failed to load menu screen")
            raise

    def load_settings_screen(self):
        logger.debug("Loading settings screen")
        try:
            self.settings_screen = SettingsScreen(self)
            self.stacked_widget.addWidget(self.settings_screen)
            logger.debug("Settings screen loaded successfully")
        except Exception as e:
            logger.exception("Failed to load settings screen")
            raise

    def load_control_screen(self):
        logger.debug("Loading control screen")
        try:
            self.control_screen = ControlScreen(self)
            self.stacked_widget.addWidget(self.control_screen)
            logger.debug("Control screen loaded successfully")
        except Exception as e:
            logger.exception("Failed to load control screen")
            raise

    def load_print_location_screen(self):
        logger.debug("Loading print location screen")
        try:
            self.print_location_screen = PrintFromLocation(self)
            self.stacked_widget.addWidget(self.print_location_screen)
            logger.debug("Print location screen loaded successfully")
        except Exception as e:
            logger.exception("Failed to load print location screen")
            raise

    def load_calibration_screens(self):
        logger.debug("Loading calibration screens")
        try:
            # Main calibration screen
            self.calibrate_screen = CalibrateScreen(self)
            self.stacked_widget.addWidget(self.calibrate_screen)
            
            logger.debug("Calibration screen loaded successfully")
        except Exception as e:
            logger.exception("Failed to load calibration screens")
            raise

    # Screen Navigation Methods
    def switch_screen(self, widget):
        """Switch to the given screen and update navigation history."""
        logger.debug(f"Switching to screen: {widget.__class__.__name__}")
        logger.debug(f"Current screen before switch: {self.current_screen.__class__.__name__ if self.current_screen else None}")
        
        # Check if we're navigating between a main screen and its subscreens
        is_subscreen_navigation = False
        
        # Check if current screen has subscreens and the widget is one of those subscreens
        if self.current_screen and hasattr(self.current_screen, 'screens'):
            is_subscreen_navigation = any(widget == subscreen for subscreen in self.current_screen.screens.values())
        
        # Check if widget has subscreens and the current_screen is one of those subscreens
        if widget and hasattr(widget, 'screens') and self.current_screen:
            is_subscreen_navigation = is_subscreen_navigation or any(self.current_screen == subscreen for subscreen in widget.screens.values())
        
        # Only update history if not navigating between a screen and its subscreens
        if self.current_screen is not None and not is_subscreen_navigation:
            self.screen_history.append(self.current_screen)
            logger.debug(f"Added {self.current_screen.__class__.__name__} to history")
        
        self.current_screen = widget
        self.stacked_widget.setCurrentWidget(widget)
        
        logger.debug(f"History now contains: {[screen.__class__.__name__ for screen in self.screen_history]}")

    def switch_to_previous_screen(self):
        """Go back to the previous screen in history."""
        logger.debug("Switching to previous screen")
        if self.screen_history:
            previous_screen = self.screen_history.pop()
            self.current_screen = previous_screen
            self.stacked_widget.setCurrentWidget(previous_screen)
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
        self.switch_screen(self.home_screen)

    def switch_to_loading_screen(self):
        logger.debug("Switching to loading screen")
        self.switch_screen(self.loading_screen)

    def switch_to_menu_screen(self):
        logger.debug("Switching to menu screen")
        self.switch_screen(self.menu_screen)

    def switch_to_settings_screen(self):
        logger.debug("Switching to settings screen")
        self.switch_screen(self.settings_screen)

    def switch_to_control_screen(self):
        logger.debug("Switching to control screen")
        self.switch_screen(self.control_screen)

    def switch_to_print_location_screen(self):
        logger.debug("Switching to print location screen")
        self.switch_screen(self.print_location_screen)

    def switch_to_calibrate_screen(self):
        logger.debug("Switching to calibration screen")
        self.switch_screen(self.calibrate_screen)

    # Delegate subscreen navigation to main screens that contain those subscreens
    def switch_to_change_filament_screen(self):
        # Let the ControlScreen handle the navigation to Change Filament
        if hasattr(self.control_screen, 'open_change_filament_screen'):
            self.control_screen.open_change_filament_screen()

    def show_error_dialog(self, title, message):
        """Display an error dialog with the given title and message."""
        logger.debug(f"Showing error dialog: {title}")
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle(title)
        error_dialog.setText(message)
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec_()
        
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions in the UI thread."""
        logger.critical("Uncaught exception in UI thread", 
                      exc_info=(exc_type, exc_value, exc_traceback))
        
        # Display an error message to the user
        error_msg = f"An unexpected error occurred:\n{str(exc_value)}\n\nPlease check the logs for details."
        self.show_error_dialog("Application Error", error_msg)



