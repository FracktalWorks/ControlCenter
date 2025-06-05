import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from ui.main_window import MainWindow
from utils import logger

def main():
    # Initialize application-wide logger
    app_version = "1.0.0"  # You can update this with your actual version
    logger.info(f"Starting Control Center application v{app_version}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Running on: {os.name} platform")
    
    try:
        app = QApplication(sys.argv)
        logger.info("QApplication initialized")
        
        window = MainWindow()
        logger.info("Main window created")
        
        window.show()
        logger.info("Main window displayed")
        
        # Log application exit
        exit_code = app.exec_()
        logger.info(f"Application exiting with code {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.exception("Failed to start application")
        raise

if __name__ == "__main__":
    main()