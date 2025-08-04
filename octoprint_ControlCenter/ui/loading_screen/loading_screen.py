from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QLabel, QProgressBar, QApplication, QDesktopWidget
from PyQt5.QtCore import QTimer, Qt
from utils.helpers import check_ui_elements
from utils.logger import get_logger
import ui.resources.resource_rc  # Import resources for UI elements
import config
import os


logger = get_logger(__name__)


class LoadingScreen(QWidget):
    """
    Loading screen UI that displays progress during application startup and connection attempts.
    Shows progress bar and status updates while connection logic is handled by the MainController.
    """
    
    def __init__(self, controller):
        super(LoadingScreen, self).__init__()
        self.controller = controller
        
        # Progress tracking
        self.current_progress = 0
        self.max_progress = 100
        self.progress_steps = {
            'initializing': 10,
            'connecting': 30,
            'authenticating': 50,
            'loading_ui': 80,
            'finalizing': 100
        }
        
        # Use centralized logger
        self.logger = get_logger(self.__class__.__name__)
        
        # Set window properties for proper display
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        try:
            ui_file_path = os.path.join(os.path.dirname(__file__), 'loading_screen.ui')
            uic.loadUi(ui_file_path, self)
            self.logger.info("LoadingScreen UI loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load LoadingScreen UI file: {e}")

        # Find UI elements
        self.loading_label = self.findChild(QLabel, 'loading')  # The main loading status label
        self.progress_bar = self.findChild(QProgressBar, 'loadingProgressBar')  # Progress bar
        
        # Check if UI elements exist and report missing ones
        self._check_widgets_existence()
        
        # Initialize progress bar
        if self.progress_bar:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(self.max_progress)
            self.progress_bar.setValue(0)
            self.logger.debug("Progress bar initialized")
        
        # Set up the window to be fullscreen or properly centered
        self._setup_window_geometry()
        
        # Set initial status
        self.update_status("Initializing...", 'initializing')
    
    def _setup_window_geometry(self):
        """Set up the window to be properly centered and sized for the screen."""
        try:
            # Get the desktop widget to determine screen size
            desktop = QApplication.desktop()
            screen_rect = desktop.screenGeometry()
            
            # Option 1: Make it fullscreen
            # self.setGeometry(screen_rect)
            # self.showFullScreen()
            
            # Option 2: Center the window with a reasonable size
            window_width = config.SCREEN_WIDTH
            window_height = config.SCREEN_HEIGHT
            
            # Calculate center position
            x = (screen_rect.width() - window_width) // 2
            y = (screen_rect.height() - window_height) // 2
            
            # Set geometry and show normally
            self.setGeometry(x, y, window_width, window_height)
            
            self.logger.info(f"Loading screen positioned at ({x}, {y}) with size {window_width}x{window_height}")
            
        except Exception as e:
            self.logger.error(f"Failed to set window geometry: {e}")
            # Fallback to config values
            self.resize(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)

    def _check_widgets_existence(self):
        """Check if UI elements exist and report missing ones"""
        loading_widgets = {
            "loading": self.loading_label,
            "loadingProgressBar": self.progress_bar
        }
        
        # Use the helper function to check and report missing widgets
        check_ui_elements(self, loading_widgets, "LoadingScreen")

    def update_status(self, status_text, progress_step=None):
        """
        Update the status text and progress bar.
        
        Args:
            status_text (str): Text to display in the loading label
            progress_step (str): Optional progress step name to set progress bar value
        """
        # Update status text
        if self.loading_label:
            self.loading_label.setText(status_text)
            self.logger.debug(f"Loading screen status updated: {status_text}")
        
        # Update progress if step is provided
        if progress_step and progress_step in self.progress_steps:
            self.set_progress(self.progress_steps[progress_step])
    
    def set_progress(self, progress_value):
        """
        Set the progress bar value.
        
        Args:
            progress_value (int): Progress value (0-100)
        """
        if self.progress_bar:
            # Ensure progress is within bounds
            progress_value = max(0, min(progress_value, self.max_progress))
            
            # Update the progress bar
            self.progress_bar.setValue(progress_value)
            self.current_progress = progress_value
            
            # Force the GUI to update immediately
            QApplication.processEvents()
            
            self.logger.debug(f"Progress updated to: {progress_value}%")
        else:
            self.logger.warning("Progress bar not found - cannot update progress")
    
    def increment_progress(self, amount=5):
        """
        Increment the progress bar by a specified amount.
        
        Args:
            amount (int): Amount to increment progress by
        """
        new_progress = min(self.current_progress + amount, self.max_progress)
        self.set_progress(new_progress)
    
    def update_progress_with_message(self, progress_value, message):
        """
        Update both progress and status message simultaneously.
        
        Args:
            progress_value (int): Progress value (0-100)
            message (str): Status message to display
        """
        # Update status message first
        if self.loading_label:
            self.loading_label.setText(message)
        
        # Then update progress
        self.set_progress(progress_value)
        
        # Force GUI update
        QApplication.processEvents()
        
        self.logger.debug(f"Progress: {progress_value}% - {message}")
    
    def animate_progress_to(self, target_progress, message=None, duration_ms=1000):
        """
        Animate progress bar to target value smoothly.
        
        Args:
            target_progress (int): Target progress value (0-100)
            message (str): Optional message to display
            duration_ms (int): Animation duration in milliseconds
        """
        if not self.progress_bar:
            return
            
        if message and self.loading_label:
            self.loading_label.setText(message)
        
        # Calculate step size for smooth animation
        start_progress = self.current_progress
        diff = target_progress - start_progress
        steps = max(10, abs(diff))  # At least 10 steps for smooth animation
        step_size = diff / steps
        step_delay = duration_ms // steps
        
        def animate_step(step_count):
            if step_count <= steps:
                new_progress = start_progress + (step_size * step_count)
                self.set_progress(int(new_progress))
                
                # Schedule next step
                if step_count < steps:
                    QTimer.singleShot(step_delay, lambda: animate_step(step_count + 1))
        
        # Start animation
        animate_step(0)
    
    def reset_progress(self):
        """Reset progress bar to 0 and clear status."""
        self.set_progress(0)
        if self.loading_label:
            self.loading_label.setText("Initializing...")
    
    def complete_progress(self):
        """Set progress to 100% and show completion message."""
        self.animate_progress_to(100, "Loading complete!", 500)
    
    def show(self):
        """Override show to ensure proper positioning and focus."""
        super().show()
        self.raise_()  # Bring to front
        self.activateWindow()  # Give focus
        
        # Force geometry update
        QApplication.processEvents()
        
        self.logger.info("Loading screen displayed and brought to front")

    def closeEvent(self, event):
        """Handle close event."""
        self.logger.info("Loading screen closing")
        super().closeEvent(event)