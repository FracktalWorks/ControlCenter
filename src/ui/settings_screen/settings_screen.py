import os
import importlib.util
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QVBoxLayout, QScrollArea
from PyQt5.QtGui import QFont

class SettingsScreen(QWidget):
    def __init__(self, main_window):
        """
        Initialize the SettingsScreen widget.

        Args:
            main_window (QMainWindow): The main window of the application.
        """
        super(SettingsScreen, self).__init__()
        self.main_window = main_window
        uic.loadUi('src/ui/settings_screen/settings_screen.ui', self)

        # Find the stacked widget
        self.stackedWidget = self.findChild(QStackedWidget, 'mainSettingsStackedWidget')

        # Find the main settings page
        self.mainSettingsPage = self.findChild(QWidget, 'mainSettingsPage')

        # Find the scroll area and its contents
        self.scrollArea = self.findChild(QScrollArea, 'scrollArea')
        self.scrollAreaWidgetContents = self.scrollArea.findChild(QWidget, 'scrollAreaWidgetContents')
        self.verticalLayout = self.scrollAreaWidgetContents.findChild(QVBoxLayout, 'verticalLayout')

        # Add the back button to the main layout
        self.settingsBackButton = self.findChild(QPushButton, 'settingsBackButton')
        self.settingsBackButton.clicked.connect(self.go_back)
        self.verticalLayout.insertWidget(0, self.settingsBackButton)

        # Find the new buttons
        self.restorePrintSettingsButton = self.findChild(QPushButton, 'restorePrintSettingsButton')
        self.restoreFactoryDefaultsButton = self.findChild(QPushButton, 'restoreFactoryDefaultsButton')
        self.restartButton = self.findChild(QPushButton, 'restartButton')

        # Connect the new buttons to their respective functions
        self.restorePrintSettingsButton.clicked.connect(self.restore_print_settings)
        self.restoreFactoryDefaultsButton.clicked.connect(self.restore_factory_defaults)
        self.restartButton.clicked.connect(self.restart_system)

        # Scan the "Settings Screen" folder for subfolders containing .ui files
        self.load_settings_widgets()

        # Set the default page to mainSettingsPage
        self.stackedWidget.setCurrentWidget(self.mainSettingsPage)

    def go_back(self):
        """
        Switch back to the main menu screen.
        """
        self.main_window.switch_screen(self.main_window.menu_screen)

    def load_settings_widgets(self):
        """
        Load settings widgets from subfolders in the "Settings Screen" folder.
        """
        settings_folder = 'src/ui/settings_screen'
        for subfolder in os.listdir(settings_folder):
            subfolder_path = os.path.join(settings_folder, subfolder)
            if os.path.isdir(subfolder_path):
                ui_file = os.path.join(subfolder_path, f'{subfolder}.ui')
                py_file = os.path.join(subfolder_path, f'{subfolder}.py')
                if os.path.exists(ui_file) and os.path.exists(py_file):
                    print(f"Loading widget: {subfolder}")
                    # Create a button for the subfolder
                    button = QPushButton(subfolder.replace('_', ' ').title())
                    button.setMinimumHeight(100)
                    button.setFont(QFont("Gotham Light", 16))
                    button.setStyleSheet("""
                        QPushButton {
                            border: 1px solid rgb(87, 87, 87);
                            background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0.188, stop:0 rgba(180, 180, 180, 255), stop:1 rgba(255, 255, 255, 255));
                        }
                        QPushButton:pressed {
                            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #dadbde, stop: 1 #f6f7fa);
                        }
                        QPushButton:flat {
                            border: none; /* no border for a flat push button */
                        }
                        QPushButton:default {
                            border-color: navy; /* make the default button prominent */
                        }
                    """)
                    button.clicked.connect(lambda _, sf=subfolder: self.load_widget(sf))
                    self.verticalLayout.addWidget(button)

                    # Load the widget and add it to the stacked widget
                    widget_instance = self.create_widget_instance(ui_file, py_file)
                    page = QWidget()
                    layout = QVBoxLayout(page)
                    layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
                    layout.setSpacing(0)  # Remove spacing
                    layout.addWidget(widget_instance)
                    self.stackedWidget.addWidget(page)
                    print(f"Added widget: {widget_instance.objectName()}")

        # Ensure the mainSettingsPage is set as the default page after loading all widgets
        self.stackedWidget.setCurrentWidget(self.mainSettingsPage)

        # Ensure the restart button is at the bottom of the button list
        self.verticalLayout.addWidget(self.restartButton)

    def load_widget(self, widget_name):
        """
        Switch to the specified widget in the stacked widget.

        Args:
            widget_name (str): The name of the widget to switch to.
        """
        print(f"Switching to widget: {widget_name}")
        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if widget.findChild(QWidget, widget_name):
                self.stackedWidget.setCurrentWidget(widget)
                print(f"Switched to widget: {widget_name}")
                break

    def create_widget_instance(self, ui_file, py_file):
        """
        Create an instance of a widget from the specified .ui and .py files.

        Args:
            ui_file (str): The path to the .ui file.
            py_file (str): The path to the .py file.

        Returns:
            QWidget: An instance of the dynamically loaded widget.
        """
        class DynamicWidget(QWidget):
            def __init__(self, parent):
                super(DynamicWidget, self).__init__(parent)
                uic.loadUi(ui_file, self)
                self.setObjectName(os.path.basename(ui_file).split('.')[0])
                self.load_backend(py_file, parent)

            def load_backend(self, py_file, parent):
                spec = importlib.util.spec_from_file_location("module.name", py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Assuming the class name in the .py file is the same as the subfolder name
                class_name = os.path.basename(py_file).split('.')[0].title().replace('_', '')
                backend_class = getattr(module, class_name)
                backend_instance = backend_class(self, parent)
                self.backend = backend_instance

        return DynamicWidget(self)

    def restore_print_settings(self):
        """
        Restore the print settings to their default values.
        """
        print("Restoring print settings to default values.")
        # Add logic to restore print settings

    def restore_factory_defaults(self):
        """
        Restore the system to factory default settings.
        """
        print("Restoring system to factory default settings.")
        # Add logic to restore factory default settings

    def restart_system(self):
        """
        Restart the system.
        """
        print("Restarting the system.")
        # Add logic to restart the system