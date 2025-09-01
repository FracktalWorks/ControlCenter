"""
Printer Configuration Manager
Unified utility for managing both Klipper and OctoPrint configuration files, 
printer selection, variable parsing, and backup operations.
"""
import os
import shutil
import glob
import re
import json
from typing import List, Dict, Optional, Any

try:
    import yaml
except ImportError as e:
    raise ImportError(
        "PyYAML is required for OctoPrint configuration management. "
        "Please install it with: pip install PyYAML"
    ) from e

from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration paths
FIRMWARE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firmware")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
PRINTER_CFG_PATH = '/home/pi/printer.cfg'
KLIPPER_CONFIG_PATH = '/home/pi/'
OCTOPRINT_CONFIG_PATH = '/home/pi/.octoprint/'
BACKUP_CFG_PATTERN = '/home/pi/printer-*.cfg'

# Fallback values when configuration cannot be read
FALLBACK_CONFIG = {
    'name': 'Unknown Printer',
    'extruder_count': 1,
    'bed_width': 200,
    'bed_depth': 200,
    'bed_height': 200,
    'is_dual': False
}


class PrinterConfigManager:
    """Unified manager for all printer configuration operations."""
    
    def __init__(self):
        self.firmware_path = FIRMWARE_PATH
        self.config_path = CONFIG_PATH
        self.printer_cfg_path = PRINTER_CFG_PATH
        self.klipper_config_path = KLIPPER_CONFIG_PATH
        self.octoprint_config_path = OCTOPRINT_CONFIG_PATH
        self.backup_pattern = BACKUP_CFG_PATTERN

    # ========================================================================
    # PRINTER DISCOVERY AND MANAGEMENT
    # ========================================================================
    
    def get_available_printers(self) -> List[str]:
        """Get list of available printer configurations from the firmware folder."""
        available_printers = []
        
        try:
            if os.path.exists(self.firmware_path):
                for file in os.listdir(self.firmware_path):
                    if file.startswith("PRINTER_") and file.endswith(".cfg"):
                        printer_name = file[8:-4]  # Remove "PRINTER_" prefix and ".cfg" suffix
                        available_printers.append(printer_name)
                        
                logger.debug(f"Found {len(available_printers)} printer configurations")
            else:
                logger.warning(f"Firmware path not found: {self.firmware_path}")
                
        except Exception as e:
            logger.error(f"Error getting available printers: {e}")
            
        return sorted(available_printers)
    
    def get_printer_display_name(self, printer_name: str) -> str:
        """Convert printer name to display name by extracting from Klipper config."""
        # Try to get name from printer configuration variables
        config_file = os.path.join(self.firmware_path, f"PRINTER_{printer_name}.cfg")
        if os.path.exists(config_file):
            # Extract a reasonable display name from the printer name
            # Convert DRAGON_400 -> Dragon 400, TWINDRAGON_600 -> Twin Dragon 600, etc.
            display_name = printer_name.replace("_", " ").title()
            if display_name.startswith("Twindragon"):
                display_name = display_name.replace("Twindragon", "Twin Dragon")
            return display_name
        
        # Fallback to simple conversion
        return printer_name.replace("_", " ").title()
    
    def get_printer_filename(self, printer_name: str) -> str:
        """Convert printer name back to filename format."""
        return f"PRINTER_{printer_name}.cfg"
    
    def get_firmware_files(self) -> List[str]:
        """Get list of all firmware configuration files."""
        firmware_files = []
        
        try:
            if os.path.exists(self.firmware_path):
                firmware_files = [f for f in os.listdir(self.firmware_path) if f.endswith('.cfg')]
                logger.debug(f"Found {len(firmware_files)} firmware files")
            else:
                logger.warning(f"Firmware path not found: {self.firmware_path}")
                
        except Exception as e:
            logger.error(f"Error getting firmware files: {e}")
            
        return firmware_files

    # ========================================================================
    # PRINTER.CFG PARSING AND MANAGEMENT
    # ========================================================================
    
    def get_current_printer_selection(self) -> Optional[str]:
        """Get the currently active printer configuration from printer.cfg."""
        try:
            if os.path.exists(self.printer_cfg_path):
                with open(self.printer_cfg_path, 'r') as f:
                    content = f.read()
                    
                # Look for active include statements
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('[include PRINTER_') and not line.startswith('#'):
                        match = re.search(r'PRINTER_(\w+)\.cfg', line)
                        if match:
                            return match.group(1)
                            
        except Exception as e:
            logger.error(f"Error getting current printer selection: {e}")
            
        return None

    # ========================================================================
    # PRINTER_VARIABLES PARSING
    # ========================================================================
    
    def parse_printer_variables_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse PRINTER_VARIABLES macro from a specific configuration file."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return None
                
            with open(file_path, 'r') as f:
                content = f.read()
                
            variables = {}
            in_printer_variables = False
            
            for line in content.split('\n'):
                line = line.strip()
                
                if line.startswith('[gcode_macro PRINTER_VARIABLES]'):
                    in_printer_variables = True
                    continue
                    
                if in_printer_variables:
                    if line.startswith('[') and not line.startswith('[gcode_macro'):
                        break
                        
                    if line.startswith('variable_'):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            var_name = parts[0].replace('variable_', '').strip()
                            var_value = parts[1].split('#')[0].strip()  # Remove comments
                            variables[var_name] = self._parse_variable_value(var_value)
                            
            return variables if variables else None
            
        except Exception as e:
            logger.error(f"Error parsing PRINTER_VARIABLES from {file_path}: {e}")
            return None
    
    def _parse_variable_value(self, value_str: str) -> Any:
        """Parse a variable value string into its appropriate Python type."""
        value_str = value_str.strip()
        
        # Handle string values (quoted)
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            return value_str[1:-1]
        
        # Handle numeric values first (before boolean check)
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # Handle boolean values (only if not numeric)
        if value_str.lower() == 'true':
            return True
        elif value_str.lower() == 'false':
            return False
        
        # Default to string if we can't parse it
        return value_str
    
    def get_printer_variables_from_active_config(self) -> Optional[Dict[str, Any]]:
        """Get PRINTER_VARIABLES from the currently active printer configuration."""
        current_printer = self.get_current_printer_selection()
        if current_printer:
            config_file = os.path.join(self.firmware_path, f"PRINTER_{current_printer}.cfg")
            return self.parse_printer_variables_from_file(config_file)
        return None

    def get_printer_config_from_variables(self, printer_name: str) -> Dict[str, Any]:
        """Get printer configuration by parsing PRINTER_VARIABLES from the firmware file."""
        config_file = os.path.join(self.firmware_path, f"PRINTER_{printer_name}.cfg")
        variables = self.parse_printer_variables_from_file(config_file)
        
        if not variables:
            logger.warning(f"No PRINTER_VARIABLES found for {printer_name}, using fallback config")
            return FALLBACK_CONFIG.copy()
        
        # Extract configuration from variables
        config = {
            'name': self.get_printer_display_name(printer_name),
            'bed_width': variables.get('bed_x_max', FALLBACK_CONFIG['bed_width']) - variables.get('bed_x_min', 0),
            'bed_depth': variables.get('bed_y_max', FALLBACK_CONFIG['bed_depth']) - variables.get('bed_y_min', 0),
            'bed_height': variables.get('bed_z_max', FALLBACK_CONFIG['bed_height']) - variables.get('bed_z_min', 0),
            'is_dual': bool(variables.get('is_dual_nozzle', 0)),
            'extruder_count': 2 if bool(variables.get('is_dual_nozzle', 0)) else 1,
            # Store raw variables for further use
            'variables': variables
        }
        
        logger.debug(f"Extracted config for {printer_name}: {config}")
        return config

    # ========================================================================
    # CONFIGURATION EXTRACTION AND TRANSFORMATION
    # ========================================================================
    
    def extract_printer_configuration(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Extract configuration from PRINTER_VARIABLES in the format expected by config.py."""
        if not variables:
            return {}
            
        config = {
            # Bed size information
            'bed_size': {
                'x_min': variables.get('bed_x_min', 0),
                'x_max': variables.get('bed_x_max', 200),
                'y_min': variables.get('bed_y_min', 0),
                'y_max': variables.get('bed_y_max', 200),
                'z_min': variables.get('bed_z_min', 0),
                'z_max': variables.get('bed_z_max', 200),
            },
            'is_dual_nozzle': bool(variables.get('is_dual_nozzle', 0)),
            'has_chamber_cooling': 'fan1' in variables,
            
            # Machine build size (compatible with config.py format)
            'machineBuildSize': {
                'X': variables.get('bed_x_max', 200) - variables.get('bed_x_min', 0),
                'Y': variables.get('bed_y_max', 200) - variables.get('bed_y_min', 0),
                'Z': variables.get('bed_z_max', 200) - variables.get('bed_z_min', 0),
            },
            
            # Calibration positions
            'calibrationPosition': {
                'X1': variables.get('bed_calibration_x1', 50),
                'Y1': variables.get('bed_calibration_y1', 50),
                'X2': variables.get('bed_calibration_x2', 150),
                'Y2': variables.get('bed_calibration_y2', 50),
                'X3': variables.get('bed_calibration_x3', 100),
                'Y3': variables.get('bed_calibration_y3', 150),
                'X4': variables.get('bed_calibration_x4', 100),
                'Y4': variables.get('bed_calibration_y4', 100),
            },
            
            # Tool positions
            'tool0PurgePosition': {
                'X': variables.get('tool0_pause_position_x', -30),
                'Y': variables.get('tool0_pause_position_y', -77),
            },
            'tool1PurgePosition': {
                'X': variables.get('tool1_pause_position_x', 655),
                'Y': variables.get('tool1_pause_position_y', -77),
            },
            
            # Other settings
            'ptfeTubeLength': variables.get('ptfe_tube_length', 1500),
            'IS_DUAL_NOZZLE': bool(variables.get('is_dual_nozzle', 0)),
        }
        
        # Calculate bed dimensions for backwards compatibility
        config['bed_width'] = config['machineBuildSize']['X']
        config['bed_depth'] = config['machineBuildSize']['Y']
        config['bed_height'] = config['machineBuildSize']['Z']
        
        return config
    
    def get_printer_config_from_klipper(self) -> Optional[Dict[str, Any]]:
        """Get complete printer configuration from active Klipper config."""
        variables = self.get_printer_variables_from_active_config()
        if variables:
            return self.extract_printer_configuration(variables)
        return None

    # ========================================================================
    # OCTOPRINT CONFIGURATION MANAGEMENT
    # ========================================================================
    
    def update_octoprint_config(self, printer_name: str) -> bool:
        """Update OctoPrint config.yaml with printer-specific settings."""
        try:
            source_config = os.path.join(self.config_path, 'config.yaml')
            dest_config = os.path.join(self.octoprint_config_path, 'config.yaml')
            
            if not os.path.exists(source_config):
                logger.error(f"Source config not found: {source_config}")
                return False
                
            # Load the template config
            with open(source_config, 'r') as f:
                config_data = yaml.safe_load(f)
                
            # Update appearance name with current printer
            if 'appearance' not in config_data:
                config_data['appearance'] = {}
                
            config_data['appearance']['name'] = self.get_printer_display_name(printer_name)
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dest_config), exist_ok=True)
            
            # Write updated config
            with open(dest_config, 'w') as f:
                yaml.safe_dump(config_data, f, default_flow_style=False)
                
            logger.info(f"Updated OctoPrint config with printer: {printer_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating OctoPrint config: {e}")
            return False
    
    def update_octoprint_printer_profile(self, printer_name: str) -> bool:
        """Update OctoPrint printer profile with printer-specific settings."""
        try:
            source_profile = os.path.join(self.config_path, '_default.profile')
            dest_profile = os.path.join(self.octoprint_config_path, 'printerProfiles', '_default.profile')
            
            if not os.path.exists(source_profile):
                logger.error(f"Source profile not found: {source_profile}")
                return False
                
            # Load the template profile
            with open(source_profile, 'r') as f:
                profile_data = yaml.safe_load(f)
                
            # Get printer configuration from Klipper variables
            printer_config = self.get_printer_config_from_variables(printer_name)
            
            # Update profile with dynamic configuration
            profile_data['name'] = printer_config['name']
            profile_data['extruder']['count'] = printer_config['extruder_count']
            profile_data['volume']['width'] = float(printer_config['bed_width'])
            profile_data['volume']['depth'] = float(printer_config['bed_depth'])
            profile_data['volume']['height'] = float(printer_config['bed_height'])
            
            # Update offsets for dual extruder
            if printer_config['extruder_count'] == 2:
                profile_data['extruder']['offsets'] = [
                    [0.0, 0.0],
                    [0.0, 0.0]
                ]
            else:
                profile_data['extruder']['offsets'] = [
                    [0.0, 0.0]
                ]
                    
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dest_profile), exist_ok=True)
            
            # Write updated profile
            with open(dest_profile, 'w') as f:
                yaml.safe_dump(profile_data, f, default_flow_style=False)
                
            logger.info(f"Updated OctoPrint printer profile for: {printer_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating OctoPrint printer profile: {e}")
            return False
    
    def restore_octoprint_configs(self, printer_name: str) -> bool:
        """Restore all OctoPrint configuration files for the selected printer."""
        try:
            success = True
            
            # Copy basic config files
            config_files = [
                ('users.yaml', 'users.yaml'),
                ('dhcpcd.conf', '/etc/dhcpcd.conf')
            ]
            
            for source_file, dest_path in config_files:
                source = os.path.join(self.config_path, source_file)
                if os.path.exists(source):
                    try:
                        if dest_path.startswith('/etc/'):
                            # System files need sudo
                            os.system(f'sudo cp -f "{source}" "{dest_path}"')
                        else:
                            # OctoPrint files
                            dest = os.path.join(self.octoprint_config_path, dest_path)
                            os.makedirs(os.path.dirname(dest), exist_ok=True)
                            shutil.copy2(source, dest)
                        logger.debug(f"Copied {source_file} to {dest_path}")
                    except Exception as e:
                        logger.error(f"Error copying {source_file}: {e}")
                        success = False
                        
            # Update printer-specific configs
            if not self.update_octoprint_config(printer_name):
                success = False
                
            if not self.update_octoprint_printer_profile(printer_name):
                success = False
                
            # Clean up old files
            try:
                os.system('sudo rm -rf /home/pi/.octoprint/scripts/gcode')
                os.system('sudo rm -rf /home/pi/.octoprint/print_restore.json')
            except Exception as e:
                logger.warning(f"Error cleaning up old files: {e}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error restoring OctoPrint configs: {e}")
            return False

    # ========================================================================
    # FILE DEPLOYMENT AND MANAGEMENT
    # ========================================================================
    
    def update_printer_cfg(self, source_path: str, dest_path: str, selected_printer: str, preserve_mcu: bool = True) -> bool:
        """Update printer.cfg with new printer selection while preserving MCU config."""
        try:
            if not os.path.exists(source_path):
                logger.error(f"Source file not found: {source_path}")
                return False
                
            # Read the template
            with open(source_path, 'r') as f:
                content = f.read()
                
            # Update the include statement to point to the selected printer
            lines = content.split('\n')
            updated_lines = []
            
            for line in lines:
                if 'PRINTER_' in line and '.cfg' in line:
                    if line.strip().startswith('#'):
                        # This is a commented printer config
                        if f'PRINTER_{selected_printer}.cfg' in line:
                            # Uncomment this line
                            updated_lines.append(line.replace('#', '', 1))
                        else:
                            # Keep other printer configs commented
                            updated_lines.append(line)
                    else:
                        # This is an active include, comment it out unless it's our target
                        if f'PRINTER_{selected_printer}.cfg' in line:
                            updated_lines.append(line)
                        else:
                            updated_lines.append('#' + line)
                else:
                    updated_lines.append(line)
                    
            # Write the updated content
            with open(dest_path, 'w') as f:
                f.write('\n'.join(updated_lines))
                
            logger.info(f"Updated printer.cfg for {selected_printer}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating printer.cfg: {e}")
            return False
    
    def copy_firmware_files(self, selected_printer: str) -> bool:
        """Copy all firmware files and update printer selection."""
        try:
            if not os.path.exists(self.firmware_path):
                logger.error(f"Firmware path not found: {self.firmware_path}")
                return False
                
            # Copy all .cfg files to Klipper config directory
            firmware_files = self.get_firmware_files()
            for file in firmware_files:
                source = os.path.join(self.firmware_path, file)
                dest = os.path.join(self.klipper_config_path, file)
                try:
                    shutil.copy2(source, dest)
                    logger.debug(f"Copied {file} to Klipper config")
                except Exception as e:
                    logger.error(f"Error copying {file}: {e}")
                    return False
                    
            # Update printer.cfg with the selected printer
            source_printer_cfg = os.path.join(self.firmware_path, 'printer.cfg')
            dest_printer_cfg = self.printer_cfg_path
            
            if not self.update_printer_cfg(source_printer_cfg, dest_printer_cfg, selected_printer):
                return False
                
            # Update OctoPrint configurations
            if not self.restore_octoprint_configs(selected_printer):
                logger.warning("Failed to update OctoPrint configs, but Klipper config was successful")
                
            logger.info(f"Successfully configured printer: {selected_printer}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying firmware files: {e}")
            return False

    # ========================================================================
    # BACKUP AND RECOVERY OPERATIONS
    # ========================================================================
    
    def is_config_valid(self, config_path: str = None) -> bool:
        """Check if configuration file is valid."""
        if config_path is None:
            config_path = self.printer_cfg_path
            
        try:
            return os.path.exists(config_path) and os.path.getsize(config_path) > 0
        except Exception as e:
            logger.error(f"Error checking config validity: {e}")
            return False
    
    def get_backup_files(self, pattern: str = None) -> List[str]:
        """Get list of backup configuration files."""
        if pattern is None:
            pattern = self.backup_pattern
            
        try:
            return sorted(glob.glob(pattern), reverse=True)
        except Exception as e:
            logger.error(f"Error getting backup files: {e}")
            return []
    
    def restore_backup_config(self, config_path: str = None, backup_pattern: str = None) -> bool:
        """Restore configuration from the most recent backup."""
        if config_path is None:
            config_path = self.printer_cfg_path
        if backup_pattern is None:
            backup_pattern = self.backup_pattern
            
        try:
            backups = self.get_backup_files(backup_pattern)
            if not backups:
                logger.warning("No backup files found")
                return False
                
            latest_backup = backups[0]
            shutil.copy2(latest_backup, config_path)
            logger.info(f"Restored config from backup: {latest_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def cleanup_old_backups(self, keep: int = 5, backup_pattern: str = None) -> None:
        """Remove old backup files, keeping only the specified number."""
        if backup_pattern is None:
            backup_pattern = self.backup_pattern
            
        try:
            backups = self.get_backup_files(backup_pattern)
            if len(backups) > keep:
                for backup in backups[keep:]:
                    os.remove(backup)
                    logger.debug(f"Removed old backup: {backup}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
    
    def check_klipper_config_files(self) -> Dict[str, bool]:
        """Check if all required Klipper configuration files exist."""
        required_files = [
            'printer.cfg',
            'CORE_GCODE_MACROS.cfg',
            'variables.cfg'
        ]
        
        status = {}
        for file in required_files:
            file_path = os.path.join(self.klipper_config_path, file)
            status[file] = os.path.exists(file_path)
            
        return status
    
    def get_missing_config_files(self) -> List[str]:
        """Get list of missing configuration files."""
        status = self.check_klipper_config_files()
        return [file for file, exists in status.items() if not exists]


# ============================================================================
# SINGLETON INSTANCE AND CONVENIENCE FUNCTIONS
# ============================================================================

# Create singleton instance
_printer_config_manager = None

def get_printer_config_manager() -> PrinterConfigManager:
    """Get singleton instance of PrinterConfigManager."""
    global _printer_config_manager
    if _printer_config_manager is None:
        _printer_config_manager = PrinterConfigManager()
    return _printer_config_manager


# Convenience functions for backwards compatibility
def get_available_printers() -> List[str]:
    """Get list of available printer configurations."""
    return get_printer_config_manager().get_available_printers()

def get_printer_display_name(printer_name: str) -> str:
    """Convert printer name to display name."""
    return get_printer_config_manager().get_printer_display_name(printer_name)

def get_printer_filename(printer_name: str) -> str:
    """Convert printer name back to filename format."""
    return get_printer_config_manager().get_printer_filename(printer_name)

def get_current_printer_selection() -> Optional[str]:
    """Get the currently active printer configuration."""
    return get_printer_config_manager().get_current_printer_selection()

def copy_firmware_files(selected_printer: str) -> bool:
    """Copy all firmware files and update printer selection."""
    return get_printer_config_manager().copy_firmware_files(selected_printer)

def get_printer_config_from_klipper() -> Optional[Dict[str, Any]]:
    """Get complete printer configuration from active Klipper config."""
    return get_printer_config_manager().get_printer_config_from_klipper()

def parse_printer_variables_from_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Parse PRINTER_VARIABLES from a specific file."""
    return get_printer_config_manager().parse_printer_variables_from_file(file_path)

def extract_printer_configuration(variables: Dict[str, Any]) -> Dict[str, Any]:
    """Extract configuration from PRINTER_VARIABLES."""
    return get_printer_config_manager().extract_printer_configuration(variables)

def restore_octoprint_configs(printer_name: str) -> bool:
    """Restore all OctoPrint configuration files for the selected printer."""
    return get_printer_config_manager().restore_octoprint_configs(printer_name)
