import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from controllers.main_controller import MainController
from utils.logger import get_logger
from utils import dialog

def main():
    logger = get_logger(__name__)
    logger.info(f"Starting Control Center application")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Running on: {os.name} platform")
    
    app = None
    
    try:
        app = QApplication(sys.argv)
        logger.info("QApplication initialized")
        
        # Create main controller and start application flow
        controller = MainController()
        logger.info("Main controller created")
        
        # Start the application - this will show loading screen and begin connection
        controller.start_application()
        logger.info("Application started - loading screen displayed and connection check initiated")
        
        # Start the application event loop
        exit_code = app.exec_()
        logger.info(f"Application exiting with code {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.exception("Failed to start application")
        
        # Show error dialog if possible
        if app is not None:
            try:
                # Use the custom dialog system for consistent UI
                error_message = f"Failed to start Control Center application\n\nError: {str(e)}\n\nCheck the logs for more details."
                dialog.WarningOk(None, error_message, 
                                fontSize=12, 
                                overlay=True)
            except:
                pass  # If even the error dialog fails, just exit
        
        # Re-raise the exception for debugging
        raise

if __name__ == "__main__":
    main()