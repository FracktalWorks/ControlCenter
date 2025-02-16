def format_printer_status(status):
    """Format the printer status for display."""
    return f"Status: {status['state']['text']}, Progress: {status['progress']['completion']}%"

def handle_api_error(error):
    """Handle errors from the OctoPrint API."""
    print(f"API Error: {error}")

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