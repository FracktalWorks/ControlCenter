import os
import re
import shutil
import logging
from typing import List, Dict, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

FIRMWARE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firmware")
PRINTER_CFG_PATH = '/home/pi/printer.cfg'
KLIPPER_CONFIG_PATH = '/home/pi/'  # Klipper configuration directory


def get_available_printers() -> List[str]:
    """Get list of available printer configurations from the firmware folder."""
    available_printers = []
    
    try:
        # Look for PRINTER_*.cfg files in the firmware directory
        if os.path.exists(FIRMWARE_PATH):
            for file in os.listdir(FIRMWARE_PATH):
                if file.startswith("PRINTER_") and file.endswith(".cfg"):
                    # Extract just the printer name (remove PRINTER_ prefix and .cfg suffix)
                    printer_name = file[8:-4]  # Remove "PRINTER_" (8 chars) and ".cfg" (4 chars)
                    available_printers.append(printer_name)
        
        # Sort the list for consistent ordering
        available_printers.sort()
        logger.info(f"Found {len(available_printers)} available printer configurations")
        return available_printers
        
    except Exception as e:
        logger.error(f"Error scanning for printer configurations: {e}")
        return []


def get_printer_display_name(printer_name: str) -> str:
    """Convert printer name to display name."""
    # The printer_name is already without PRINTER_ prefix and .cfg suffix
    # Replace underscores with spaces and format nicely
    display_name = printer_name.replace("_", " ")
    return display_name


def get_printer_filename(printer_name: str) -> str:
    """Convert printer name back to filename format."""
    return f"PRINTER_{printer_name}.cfg"


def get_firmware_files() -> List[str]:
    """Get list of all firmware configuration files."""
    firmware_files = []
    
    try:
        if os.path.exists(FIRMWARE_PATH):
            for file in os.listdir(FIRMWARE_PATH):
                if file.endswith('.cfg'):
                    firmware_files.append(file)
        
        firmware_files.sort()
        return firmware_files
        
    except Exception as e:
        logger.error(f"Error scanning firmware files: {e}")
        return []


def parse_printer_cfg(config_path: str) -> Dict[str, str]:
    """Parse printer.cfg file and extract printer selection section and MCU config."""
    printer_selections = {}
    mcu_config = {}
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            
        # Extract printer selection section
        printer_section_match = re.search(
            r'########################################\s*\n'
            r'# Select Any One Printer Configuration\s*\n'
            r'(.*?)'
            r'########################################',
            content, re.DOTALL
        )
        
        if printer_section_match:
            printer_section = printer_section_match.group(1)
            # Find all include lines (commented and uncommented)
            include_lines = re.findall(r'(#?\s*\[include\s+(\S+\.cfg)\])', printer_section)
            for full_line, filename in include_lines:
                is_active = not full_line.strip().startswith('#')
                printer_selections[filename] = is_active
        
        # Extract MCU config section
        mcu_section_match = re.search(
            r'########################################\s*\n'
            r'# MCU Config\s*\n'
            r'########################################\s*\n'
            r'(.*?)(?=\n########################################|\Z)',
            content, re.DOTALL
        )
        
        if mcu_section_match:
            mcu_section = mcu_section_match.group(1)
            # Extract MCU configurations
            mcu_matches = re.findall(r'\[mcu([^\]]*)\]\s*\n([^[]*)', mcu_section)
            for mcu_name, mcu_content in mcu_matches:
                mcu_key = f"[mcu{mcu_name}]"
                mcu_config[mcu_key] = mcu_content.strip()
                
    except Exception as e:
        logger.error(f"Error parsing printer.cfg: {e}")
        
    return {
        'printer_selections': printer_selections,
        'mcu_config': mcu_config
    }


def update_printer_cfg(source_path: str, dest_path: str, selected_printer: str, preserve_mcu: bool = True) -> bool:
    """
    Update printer.cfg with new printer selection while preserving MCU config.
    
    Args:
        source_path: Path to source printer.cfg (firmware folder)
        dest_path: Path to destination printer.cfg (/home/pi/printer.cfg)
        selected_printer: Name of the printer config to activate (without PRINTER_ prefix and .cfg suffix)
        preserve_mcu: Whether to preserve existing MCU configuration
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert printer name to full filename
        selected_printer_file = get_printer_filename(selected_printer)
        
        # Parse existing config if it exists and preserve_mcu is True
        existing_mcu_config = {}
        if preserve_mcu and os.path.exists(dest_path):
            existing_data = parse_printer_cfg(dest_path)
            existing_mcu_config = existing_data.get('mcu_config', {})
            logger.info(f"Preserving MCU config from existing printer.cfg")
        
        # Read the source configuration
        with open(source_path, 'r') as f:
            content = f.read()
        
        # Update printer selection section
        def replace_printer_selection(match):
            section_header = match.group(1)
            section_content = match.group(2)
            section_footer = match.group(3)
            
            # Process each line in the printer selection section
            lines = section_content.split('\n')
            updated_lines = []
            
            for line in lines:
                if line.strip() and '[include' in line:
                    # Extract the filename from the include line
                    include_match = re.search(r'\[include\s+(\S+\.cfg)\]', line)
                    if include_match:
                        filename = include_match.group(1)
                        if filename == selected_printer_file:
                            # Uncomment this line (make it active)
                            updated_line = re.sub(r'^#?\s*', '', line)
                            updated_lines.append(updated_line)
                        else:
                            # Comment out this line (make it inactive)
                            if not line.strip().startswith('#'):
                                updated_line = '# ' + line
                            else:
                                updated_line = line
                            updated_lines.append(updated_line)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            return section_header + '\n'.join(updated_lines) + section_footer
        
        # Apply the printer selection update
        content = re.sub(
            r'(########################################\s*\n# Select Any One Printer Configuration\s*\n)'
            r'(.*?)'
            r'(########################################)',
            replace_printer_selection,
            content,
            flags=re.DOTALL
        )
        
        # If we have existing MCU config to preserve, replace the MCU section
        if existing_mcu_config:
            mcu_section_content = "\n\n"
            for mcu_key, mcu_content in existing_mcu_config.items():
                mcu_section_content += f"{mcu_key}\n{mcu_content}\n\n"
            
            # Replace MCU config section
            content = re.sub(
                r'(########################################\s*\n# MCU Config\s*\n########################################\s*\n)'
                r'(.*?)(?=\n########################################|\Z)',
                r'\1' + mcu_section_content.rstrip(),
                content,
                flags=re.DOTALL
            )
        
        # Create backup of existing file if it exists
        if os.path.exists(dest_path):
            backup_path = f"{dest_path}.backup"
            shutil.copy2(dest_path, backup_path)
            logger.info(f"Created backup at {backup_path}")
        
        # Write the updated configuration
        with open(dest_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Successfully updated printer.cfg with {selected_printer}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating printer.cfg: {e}")
        return False


def copy_firmware_files(selected_printer: str) -> bool:
    """
    Copy all firmware files from firmware folder to Klipper config directory,
    updating printer.cfg with the selected printer configuration.
    
    Args:
        selected_printer: Name of the printer config to activate
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        source_printer_cfg = os.path.join(FIRMWARE_PATH, "printer.cfg")
        
        if not os.path.exists(source_printer_cfg):
            logger.error(f"Source printer.cfg not found at {source_printer_cfg}")
            return False
        
        # First, copy all .cfg files from firmware directory to Klipper config directory
        logger.info("Copying all firmware configuration files...")
        
        # Get list of all .cfg files in firmware directory
        firmware_files = []
        if os.path.exists(FIRMWARE_PATH):
            for file in os.listdir(FIRMWARE_PATH):
                if file.endswith('.cfg'):
                    firmware_files.append(file)
        
        logger.info(f"Found {len(firmware_files)} configuration files to copy")
        
        # Copy each .cfg file to the Klipper config directory
        copied_files = []
        for filename in firmware_files:
            source_file = os.path.join(FIRMWARE_PATH, filename)
            dest_file = os.path.join(KLIPPER_CONFIG_PATH, filename)
            
            try:
                # Skip copying printer.cfg for now - we'll handle it specially
                if filename == 'printer.cfg':
                    continue
                    
                shutil.copy2(source_file, dest_file)
                copied_files.append(filename)
                logger.debug(f"Copied {filename} to Klipper config directory")
                
            except Exception as e:
                logger.warning(f"Failed to copy {filename}: {e}")
        
        logger.info(f"Successfully copied {len(copied_files)} configuration files")
        
        # Now update printer.cfg with the selected printer configuration
        success = update_printer_cfg(source_printer_cfg, PRINTER_CFG_PATH, selected_printer)
        
        if success:
            logger.info(f"Printer setup completed successfully for {selected_printer}")
            logger.info(f"Copied files: {', '.join(copied_files)}")
        else:
            logger.error(f"Failed to setup printer configuration for {selected_printer}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error copying firmware files: {e}")
        return False


def get_current_printer_selection() -> Optional[str]:
    """Get the currently active printer configuration from printer.cfg."""
    try:
        if not os.path.exists(PRINTER_CFG_PATH):
            return None
            
        data = parse_printer_cfg(PRINTER_CFG_PATH)
        printer_selections = data.get('printer_selections', {})
        
        for printer_file, is_active in printer_selections.items():
            if is_active:
                # Convert filename back to printer name (remove PRINTER_ prefix and .cfg suffix)
                if printer_file.startswith("PRINTER_") and printer_file.endswith(".cfg"):
                    return printer_file[8:-4]  # Remove "PRINTER_" (8 chars) and ".cfg" (4 chars)
                
        return None
        
    except Exception as e:
        logger.error(f"Error getting current printer selection: {e}")
        return None


def check_klipper_config_files() -> Dict[str, bool]:
    """
    Check which firmware files are present in the Klipper config directory.
    
    Returns:
        Dict mapping filename to presence status
    """
    firmware_files = get_firmware_files()
    file_status = {}
    
    for filename in firmware_files:
        dest_path = os.path.join(KLIPPER_CONFIG_PATH, filename)
        file_status[filename] = os.path.exists(dest_path)
    
    return file_status


def get_missing_config_files() -> List[str]:
    """Get list of firmware files missing from Klipper config directory."""
    file_status = check_klipper_config_files()
    missing_files = [filename for filename, exists in file_status.items() if not exists]
    return missing_files
