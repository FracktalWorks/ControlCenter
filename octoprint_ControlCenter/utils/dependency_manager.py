"""
Dependency Manager
==================

Handles automatic installation of required dependencies during application startup.
This module is designed to work with the loading screen to provide progress feedback
during dependency installation.

Features:
- Automatic dependency detection and installation
- Progress reporting for UI feedback
- Graceful error handling with user-friendly messages
- Support for PyYAML, OpenCV, and other optional dependencies
"""

import sys
import subprocess
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal

from utils.logger import get_logger


class DependencyInstaller(QObject):
    """Handles automatic installation of required dependencies with progress reporting."""
    
    # Signals for communication with the loading screen
    progress_signal = pyqtSignal(int, str)  # Progress percentage and message
    installation_complete_signal = pyqtSignal(bool)  # Success/failure
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.dependencies_to_install = []
        self.total_dependencies = 0
        self.installed_count = 0
        
    def check_and_install_dependencies(self):
        """Check for missing dependencies and install them if needed."""
        self.logger.info("Starting dependency check...")
        
        # List of dependencies to check
        dependencies = [
            {
                'name': 'PyYAML',
                'import_name': 'yaml',
                'package_name': 'PyYAML',
                'description': 'YAML parser for configuration files'
            },
            {
                'name': 'OpenCV',
                'import_name': 'cv2',
                'package_name': 'opencv-python',
                'description': 'Computer vision library for camera functionality'
            }
        ]
        
        # Check which dependencies are missing
        missing_dependencies = []
        for dep in dependencies:
            if not self._is_dependency_available(dep['import_name']):
                missing_dependencies.append(dep)
                self.logger.info(f"Missing dependency: {dep['name']}")
        
        if not missing_dependencies:
            self.logger.info("All dependencies are available")
            self.progress_signal.emit(100, "All dependencies ready")
            self.installation_complete_signal.emit(True)
            return
        
        # Install missing dependencies
        self.dependencies_to_install = missing_dependencies
        self.total_dependencies = len(missing_dependencies)
        self.installed_count = 0
        
        self.progress_signal.emit(0, f"Installing {self.total_dependencies} missing dependencies...")
        
        # Start installation in a separate thread to avoid blocking UI
        installation_thread = threading.Thread(target=self._install_dependencies_thread)
        installation_thread.daemon = True
        installation_thread.start()
    
    def _is_dependency_available(self, import_name):
        """Check if a dependency is available by trying to import it."""
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False
    
    def _install_dependencies_thread(self):
        """Install dependencies in a separate thread with progress reporting."""
        success = True
        
        for i, dep in enumerate(self.dependencies_to_install):
            try:
                # Update progress
                base_progress = int((i / self.total_dependencies) * 100)
                self.progress_signal.emit(base_progress, f"Installing {dep['name']} - {dep['description']}")
                
                # Attempt installation
                if self._install_single_dependency(dep):
                    self.installed_count += 1
                    progress = int(((i + 1) / self.total_dependencies) * 100)
                    self.progress_signal.emit(progress, f"✓ {dep['name']} installed successfully")
                    time.sleep(0.5)  # Brief pause to show success message
                else:
                    success = False
                    self.progress_signal.emit(base_progress, f"✗ Failed to install {dep['name']}")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error installing {dep['name']}: {e}")
                success = False
                self.progress_signal.emit(base_progress, f"✗ Error installing {dep['name']}: {str(e)}")
                break
        
        if success:
            self.progress_signal.emit(100, "All dependencies installed successfully")
        
        self.installation_complete_signal.emit(success)
    
    def _install_single_dependency(self, dependency):
        """Install a single dependency using pip."""
        package_name = dependency['package_name']
        
        try:
            self.logger.info(f"Installing {package_name}...")
            
            # Try standard pip install first
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully installed {package_name}")
                return True
            else:
                self.logger.warning(f"Standard pip install failed for {package_name}, trying with sudo...")
                
                # Try with sudo if standard install failed (Linux/macOS)
                try:
                    result = subprocess.run(
                        ['sudo', 'pip', 'install', package_name],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        self.logger.info(f"Successfully installed {package_name} with sudo")
                        return True
                    else:
                        self.logger.error(f"Failed to install {package_name} even with sudo")
                        return False
                        
                except FileNotFoundError:
                    # sudo not available (Windows or restricted environment)
                    self.logger.error(f"Standard pip install failed for {package_name} and sudo not available")
                    return False
                    
        except subprocess.TimeoutExpired:
            self.logger.error(f"Installation of {package_name} timed out")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error installing {package_name}: {e}")
            return False


class SimplifiedDependencyChecker:
    """Simplified dependency checker for use in modules that need immediate dependency access."""
    
    @staticmethod
    def import_with_install(import_name, package_name, description=""):
        """Import a module and install it if not available. Returns the module or None if failed."""
        logger = get_logger("DependencyChecker")
        
        try:
            # Try to import the module
            module = __import__(import_name)
            logger.debug(f"Module {import_name} is already available")
            return module
        except ImportError:
            logger.info(f"{import_name} not found. This should have been installed during startup.")
            logger.warning(f"Attempting emergency install of {package_name}...")
            
            try:
                # Emergency installation
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
                module = __import__(import_name)
                logger.info(f"Emergency installation of {package_name} successful")
                return module
            except (subprocess.CalledProcessError, ImportError) as e:
                logger.error(f"Emergency installation of {package_name} failed: {e}")
                return None
    
    @staticmethod
    def is_available(import_name):
        """Check if a module is available without attempting installation."""
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False
