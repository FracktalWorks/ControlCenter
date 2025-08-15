import os
from PyQt5.QtWidgets import QWidget, QToolButton, QPushButton, QStackedWidget
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5 import uic
from utils.helpers import check_ui_elements
from utils.logger import get_logger
from utils import dialog

# Import sub-screens
from ui.filament_nozzle_screen.changeFilamentWizard.changeFilamentWizard import ChangeFilamentWizard
from ui.filament_nozzle_screen.nozzleChangeWizard.nozzleChangeWizard import NozzleChangeWizard

logger = get_logger(__name__)

class ChangeFilamentNozzleScreen(QWidget):
    def __init__(self, main_window):
        """Initialize the combined Filament/Nozzle screen, create sub-screens,
        wire up controls, and set initial UI state.

        Args:
            main_window: Reference to the main window to access shared services and navigation.
        """
        super(ChangeFilamentNozzleScreen, self).__init__()
        self.main_window = main_window
        self.octoprint_client = main_window.octoprint_client
        self.logger = get_logger(self.__class__.__name__)

        # Load the UI
        try:
            # Use relative path from the current module's directory
            ui_file_path = os.path.join(os.path.dirname(__file__), "changeFilamentNozzleScreen.ui")
            uic.loadUi(ui_file_path, self)
            self.logger.info("ChangeFilamentNozzleScreen UI loaded successfully")
        except Exception as e:
            self.logger.exception(f"Failed to load ChangeFilamentNozzleScreen UI file: {e}")

        # Initialize UI components
        self.material_nozzle_stacked_widget = self.findChild(QStackedWidget, "mainMaterialNozzleStackedWidget")
        self.main_material_nozzle_page = self.findChild(QWidget, "mainMaterialNozzlePage")

        # Material buttons (simplified: one per tool)
        self.changeTool0MaterialBayA = self.findChild(QToolButton, "changeTool0MaterialBayA")
        self.changeTool1MaterialBayX = self.findChild(QToolButton, "changeTool1MaterialBayX")

        # Nozzle buttons
        self.changeTool0Button = self.findChild(QToolButton, "changeTool0Button")
        self.changeTool1Button = self.findChild(QToolButton, "changeTool1Button")

        # Back button
        self.materialNozzleBackButton = self.findChild(QPushButton, "materialNozzleBackButton")

        # Validate UI components
        check_ui_elements(self, [
            self.material_nozzle_stacked_widget, self.main_material_nozzle_page,
            self.changeTool0MaterialBayA, self.changeTool1MaterialBayX,
            self.changeTool0Button, self.changeTool1Button,
            self.materialNozzleBackButton
        ], "ChangeFilamentNozzleScreen")

        # Initialize all sub-screens
        self.screens = {}
        self._initialize_sub_screens()

        # Connect buttons to their respective methods (no bay parameter anymore)
        self.changeTool0MaterialBayA.clicked.connect(
            lambda: self.show_material_nozzle_screen(target_screen="filament_change", params={"tool": "tool0"})
        )
        self.changeTool1MaterialBayX.clicked.connect(
            lambda: self.show_material_nozzle_screen(target_screen="filament_change", params={"tool": "tool1"})
        )

        self.changeTool0Button.clicked.connect(
            lambda: self.show_material_nozzle_screen(target_screen="nozzle_change", params={"tool": "tool0"})
        )
        self.changeTool1Button.clicked.connect(
            lambda: self.show_material_nozzle_screen(target_screen="nozzle_change", params={"tool": "tool1"})
        )

        self.materialNozzleBackButton.clicked.connect(lambda: self.main_window.switch_to_menu_screen())

        # Show the main material/nozzle page initially
        self.material_nozzle_stacked_widget.setCurrentWidget(self.main_material_nozzle_page)
        self.logger.debug("Set current widget to mainMaterialNozzlePage")
        self._loading_dialog = None

    def showEvent(self, event):
        """Reset to main_material_nozzle_page whenever this widget is shown from main window navigation."""
        super().showEvent(event)
        try:
            self.material_nozzle_stacked_widget.setCurrentWidget(self.main_material_nozzle_page)
            self.logger.debug("Reset stacked widget to main_material_nozzle_page on show")
        except Exception as e:
            self.logger.error(f"Error resetting to main_material_nozzle_page: {e}")

    def _initialize_sub_screens(self):
        """Initialize all filament/nozzle sub-screens"""
        try:
            # Create instances of each sub-screen
            self.screens["filament_change"] = ChangeFilamentWizard(self.main_window)
            self.screens["nozzle_change"] = NozzleChangeWizard(self.main_window)

            # Add each screen to the stacked widget
            for name, screen in self.screens.items():
                self.material_nozzle_stacked_widget.addWidget(screen)
                self.logger.info(f"Added {name} screen to material/nozzle stacked widget")
            
        except Exception as e:
            self.logger.exception(f"Error initializing sub-screens: {e}")

    def _open_loading_dialog(self, message="Please wait, loading..."):
        """Show a lightweight non-blocking loading dialog using utils.dialog.

        Args:
            message: Message shown to the user while the sub-UI initializes.
        """
        try:
            if self._loading_dialog:
                return
            # Use centralized dialog helper (non-blocking, no buttons, with overlay)
            self._loading_dialog = dialog.dialog(
                self,
                message,
                buttons=QtWidgets.QMessageBox.NoButton,
                overlay=False,
                format_text=False
            )
            # Force a paint so the dialog is visible before doing heavy work
            QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
        except Exception as e:
            self.logger.error(f"Failed to show loading dialog: {e}")

    def _close_loading_dialog(self):
        """Safely hide and destroy the loading dialog if it is visible."""
        try:
            if self._loading_dialog:
                self._loading_dialog.hide()
                self._loading_dialog.deleteLater()
                self._loading_dialog = None
        except Exception as e:
            self.logger.error(f"Failed to close loading dialog: {e}")

    def _navigate_to_screen(self, screen, params, target_screen):
        """Finish navigation after the loading dialog has painted.

        Calls the sub-screen setup (if available), switches the stacked widget,
        and then closes the loading dialog.

        Args:
            screen: The QWidget sub-screen instance to show.
            params: Optional parameters forwarded to the sub-screen setup().
            target_screen: Name of the target screen for logging purposes.
        """
        try:
            if params and hasattr(screen, 'setup'):
                screen.setup(params)
            self.material_nozzle_stacked_widget.setCurrentWidget(screen)
            self.logger.info(f"Navigated to {target_screen}")
        except Exception as e:
            self.logger.exception(f"Failed navigating to {target_screen}: {e}")
        finally:
            self._close_loading_dialog()

    def show_material_nozzle_screen(self, target_screen=None, params=None):
        """Show a specific material/nozzle screen or the main page

        Args:
            target_screen: Optional string identifying which sub-screen to navigate to.
                           None means show the main page.
            params: Optional dictionary of parameters to pass to the screen.
        """
        self.logger.debug(f"show_material_nozzle_screen called with target_screen={target_screen}, params={params}")

        # Only switch to this screen in the main window if we're not already on it
        if self.main_window.current_screen != self:
            self.main_window.switch_screen(self)

        # If no specific target is requested, show the main page
        if not target_screen:
            self.material_nozzle_stacked_widget.setCurrentWidget(self.main_material_nozzle_page)
            self.logger.debug("Showing main material/nozzle page")
            return

        # Check if the requested screen exists
        if target_screen not in self.screens:
            self.logger.error(f"Requested screen '{target_screen}' not found in available screens")
            return

        # Navigate to the requested sub-screen
        screen = self.screens[target_screen]
        
        # Show loading dialog, yield to event loop, then finish navigation asynchronously
        self._open_loading_dialog("Please wait, loading...")
        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
        QtCore.QTimer.singleShot(0, lambda: self._navigate_to_screen(screen, params, target_screen))
        return


