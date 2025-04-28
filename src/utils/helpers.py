from utils import logger

def format_printer_status(status):
    """Format the printer status for display."""
    return f"Status: {status['state']['text']}, Progress: {status['progress']['completion']}%"

def handle_api_error(error):
    """Handle errors from the OctoPrint API."""
    logger.error(f"API Error: {error}")

def validate_ip_address(ip):
    """Validate the format of an IP address."""
    import re
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    return re.match(pattern, ip) is not None

def convert_to_percentage(value, total):
    """Convert a value to a percentage of a total."""
    if total == 0:
        return 0
    return (value / total) * 100

def check_ui_elements(ui_class, elements_dict, screen_name):
    """
    Check if UI elements exist and print warnings for missing ones.
    
    Args:
        ui_class: The class instance containing the UI elements
        elements_dict: Dictionary of {element_name: element_object}
        screen_name: Name of the screen for logging purposes
    
    Returns:
        A dict containing only the elements that were found (not None)
    """
    found_elements = {}
    missing_elements = []
    
    for name, element in elements_dict.items():
        if element is None:
            missing_elements.append(name)
        else:
            found_elements[name] = element
    
    if missing_elements:
        logger.warning(f"The following UI elements are missing from {screen_name}:")
        for name in missing_elements:
            logger.warning(f"  - {name}")
    
    return found_elements