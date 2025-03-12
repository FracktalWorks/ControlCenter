"""
This code contains the error logger class to log errors wrt feeltek scancard. 
The logging level is set to 'INFO' and the logs are stored in a separate log file automatically.
It makes use of python logging library to implement this.

"""

# import neccessary libraries
import os
import logging
from datetime import datetime

class LaserErrorLogger:
    """
    A class for logging laser errors.
    Attributes:
        logger (logging.Logger): The custom logger for logging laser errors.
        formatter (logging.Formatter): The formatter for formatting log messages.
        file_handler (logging.FileHandler): The file handler for saving logs to a file.
    Methods:
        __init__(): Initializes the LaserErrorLogger class.
    """
    def __init__(self):

        # create custom logger and set a format for it
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.formatter = logging.Formatter(
        "{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%d-%m-%Y %H:%M:%S",
        )

         # if the logger has any handlers already present, delete them
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

         # this is to avoid duplication when called in parent class
        self.logger.propagate = False

        # Create 'laser_logs' directory if it doesn't exist in current working directory
        if not os.path.exists('laser_logs'):
            os.makedirs('laser_logs')

         # get the current timestamp and add it in log filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fixed_file_name = f"laser_log_{timestamp}" 
        
         # set the log file handler to save the logs in desired log file
        self.file_handler = logging.FileHandler(f"./laser_logs/{fixed_file_name}.log", mode="a", encoding="utf-8")
        self.file_handler.setFormatter(self.formatter)

        # add this file handler to our custom logger
        self.logger.addHandler(self.file_handler)

