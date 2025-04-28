from utils import logger
import subprocess
import re
from threading import Thread
from functools import wraps


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

def run_async(func):
    """
    Function decorator to make methods run in a thread
    """
    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func


def getIP(interface):
    try:
        scan_result = (
            subprocess.Popen(
                "ifconfig | grep " + interface + " -A 1", stdout=subprocess.PIPE, shell=True
            ).communicate()[0]
        ).decode("utf-8")
        rInetAddr = r"inet\s*([\d.]+)"
        rInet6Addr = r"inet6"
        mt6Ip = re.search(rInet6Addr, scan_result)
        mtIp = re.search(rInetAddr, scan_result)
        if not mt6Ip and mtIp and len(mtIp.groups()) == 1:
            return str(mtIp.group(1))
    except Exception as e:
        logger.error("Error in getIP: {}".format(e))
        return None


def getMac(interface):
    logger.info("Getting MAC for interface: {}".format(interface))
    try:
        mac = subprocess.Popen(
            " cat /sys/class/net/" + interface + "/address",
            stdout=subprocess.PIPE,
            shell=True,
        ).communicate()[0].rstrip()
        if not mac:
            return "Not found"
        return mac.upper()
    except Exception as e:
        logger.error("Error in getMac: {}".format(e))
        return "Error"


def getWifiAp():
    logger.info("Getting Wifi AP")
    try:
        ap = subprocess.Popen(
            "iwgetid -r", stdout=subprocess.PIPE, shell=True
        ).communicate()[0].rstrip()
        if not ap:
            return "Not connected"
        return ap.decode("utf-8")
    except Exception as e:
        logger.error("Error in getWifiAp: {}".format(e))
        return "Error"


def getHostname():
    logger.info("Getting Hostname")
    try:
        hostname = subprocess.Popen(
            "cat /etc/hostname", stdout=subprocess.PIPE, shell=True
        ).communicate()[0].rstrip()
        if not hostname:
            return "Not connected"
        return hostname.decode("utf-8") + ".local"
    except Exception as e:
        logger.error("Error in getHostname: {}".format(e))
        return "Error"