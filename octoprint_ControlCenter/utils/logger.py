import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logger
def setup_logger(name, log_file=None, level=logging.INFO):
    """Set up and return a logger instance with console and file handlers."""
    if log_file is None:
        # Generate a timestamped log file if none is provided
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(LOG_DIR, f"{name}_{date_str}.log")
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers if any (prevents duplicate handlers)
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Create file handler (rotating log files to control disk usage)
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5*1024*1024,  # 5MB per file
        backupCount=10  # Keep 10 backup files
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create a default application logger
app_logger = setup_logger('controlcenter')

# Convenience methods for commonly used log levels
def debug(message, *args, **kwargs):
    app_logger.debug(message, *args, **kwargs)

def info(message, *args, **kwargs):
    app_logger.info(message, *args, **kwargs)

def warning(message, *args, **kwargs):
    app_logger.warning(message, *args, **kwargs)

def error(message, *args, **kwargs):
    app_logger.error(message, *args, **kwargs)

def critical(message, *args, **kwargs):
    app_logger.critical(message, *args, **kwargs)

def exception(message, *args, **kwargs):
    """Log exception info with traceback"""
    app_logger.exception(message, *args, **kwargs)

# Function to log uncaught exceptions
def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    """Handler for uncaught exceptions that logs them and shows an error message"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't log keyboard interrupt (Ctrl+C)
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    app_logger.critical("Uncaught exception", 
                       exc_info=(exc_type, exc_value, exc_traceback))
    
    # You could add code here to show an error dialog to the user

# Set the hook for uncaught exceptions
sys.excepthook = log_uncaught_exceptions