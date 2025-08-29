"""
Klipper Configuration Manager
Unified utility for managing Klipper configuration files, printer selection, 
variable parsing, and backup operations.
"""
import os
import re
import glob
import shutil
from typing import List, Dict, Optional, Any
from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration paths
FIRMWARE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firmware")
PRINTER_CFG_PATH = '/home/pi/printer.cfg'
KLIPPER_CONFIG_PATH = '/home/pi/'
BACKUP_CFG_PATTERN = '/home/pi/printer-*.cfg'


class KlipperConfigManager:
    """Unified manager for all Klipper configuration operations."""
    
    def __init__(self):
        self.firmware_path = FIRMWARE_PATH
        self.printer_cfg_path = PRINTER_CFG_PATH
        self.klipper_config_path = KLIPPER_CONFIG_PATH
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
                        # Extract printer name (remove PRINTER_ prefix and .cfg suffix)
                        printer_name = file[8:-4]
                        available_printers.append(printer_name)
            
            available_printers.sort()
            logger.info(f"Found {len(available_printers)} available printer configurations")
            return available_printers
            
        except Exception as e:
            logger.error(f"Error scanning for printer configurations: {e}")
            return []
    
    def get_printer_display_name(self, printer_name: str) -> str:
        """Convert printer name to display name."""
        return printer_name.replace("_", " ")
    
    def get_printer_filename(self, printer_name: str) -> str:
        """Convert printer name back to filename format."""
        return f"PRINTER_{printer_name}.cfg"
    
    def get_firmware_files(self) -> List[str]:
        """Get list of all firmware configuration files."""
        firmware_files = []
        
        try:
            if os.path.exists(self.firmware_path):
                for file in os.listdir(self.firmware_path):
                    if file.endswith('.cfg'):
                        firmware_files.append(file)
            
            firmware_files.sort()
            return firmware_files
            
        except Exception as e:
            logger.error(f"Error scanning firmware files: {e}")
            return []

    # ========================================================================
    # PRINTER.CFG PARSING AND MANAGEMENT
    # ========================================================================
    
    def parse_printer_cfg(self, config_path: str = None) -> Dict[str, Any]:
        """Parse printer.cfg file and extract printer selection section and MCU config."""
        if config_path is None:
            config_path = self.printer_cfg_path
            
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
                include_lines = re.findall(r'(#?\s*\[include\s+(\S+\.cfg)\])', printer_section)
                for full_line, filename in include_lines:
                    is_active = not full_line.strip().startswith('#')
                    printer_selections[filename] = is_active
            
            # Extract MCU config section
            mcu_section_match = re.search(
                r'########################################\s*\n'
                r'# MCU Config\s*\n'
                r'########################################\s*\n'
                r'(.*?)(?=\n########################################|\n#\*# <---------------------- SAVE_CONFIG|\Z)',
                content, re.DOTALL
            )
            
            if mcu_section_match:
                mcu_section = mcu_section_match.group(1)
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
    
    def get_current_printer_selection(self) -> Optional[str]:
        """Get the currently active printer configuration from printer.cfg."""
        try:
            if not os.path.exists(self.printer_cfg_path):
                return None
                
            data = self.parse_printer_cfg()
            printer_selections = data.get('printer_selections', {})
            
            for printer_file, is_active in printer_selections.items():
                if is_active:
                    if printer_file.startswith("PRINTER_") and printer_file.endswith(".cfg"):
                        return printer_file[8:-4]  # Remove "PRINTER_" and ".cfg"
                    
            return None
            
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
                logger.warning(f"Configuration file not found: {file_path}")
                return None
                
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Find the PRINTER_VARIABLES macro section
            printer_vars_match = re.search(
                r'\[gcode_macro\s+PRINTER_VARIABLES\]\s*\n(.*?)(?=\n\[|\ngcode:|\Z)',
                content,
                re.DOTALL | re.IGNORECASE
            )
            
            if not printer_vars_match:
                logger.debug(f"No PRINTER_VARIABLES macro found in {file_path}")
                return None
                
            variables_section = printer_vars_match.group(1)
            variables = {}
            
            # Parse each variable line
            for line in variables_section.split('\n'):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                    
                # Match variable definitions: variable_name: value
                var_match = re.match(r'variable_(\w+):\s*(.+?)(?:\s*#.*)?$', line)
                if var_match:
                    var_name = var_match.group(1)
                    var_value = var_match.group(2).strip()
                    
                    # Parse the value based on its type
                    parsed_value = self._parse_variable_value(var_value)
                    variables[var_name] = parsed_value
                    logger.debug(f"Parsed variable {var_name}: {parsed_value}")
                    
            logger.info(f"Successfully parsed {len(variables)} variables from {file_path}")
            return variables
            
        except Exception as e:
            logger.error(f"Error parsing PRINTER_VARIABLES from {file_path}: {e}")
            return None
    
    def _parse_variable_value(self, value_str: str) -> Any:
        """Parse a variable value string into its appropriate Python type."""
        value_str = value_str.strip()
        
        # Handle string values (quoted)
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            return value_str[1:-1]  # Remove quotes
        
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
        try:
            current_printer = self.get_current_printer_selection()
            if current_printer:
                printer_file = self.get_printer_filename(current_printer)
                
                # First try Klipper config directory (deployed location)
                klipper_printer_file_path = os.path.join(self.klipper_config_path, printer_file)
                variables = self.parse_printer_variables_from_file(klipper_printer_file_path)
                if variables:
                    logger.info(f"Found PRINTER_VARIABLES in Klipper config: {printer_file}")
                    return variables
                
                # Fallback to firmware directory
                firmware_printer_file_path = os.path.join(self.firmware_path, printer_file)
                variables = self.parse_printer_variables_from_file(firmware_printer_file_path)
                if variables:
                    logger.info(f"Found PRINTER_VARIABLES in firmware directory: {printer_file}")
                    return variables
            else:
                logger.warning("Could not determine current printer selection from printer.cfg")
                    
            logger.warning("Could not find PRINTER_VARIABLES in any configuration file")
            return None
            
        except Exception as e:
            logger.error(f"Error getting printer variables from active config: {e}")
            return None

    # ========================================================================
    # CONFIGURATION EXTRACTION AND TRANSFORMATION
    # ========================================================================
    
    def extract_printer_configuration(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Extract printer configuration values from PRINTER_VARIABLES."""
        try:
            config = {}
            
            # Build size configuration
            if all(k in variables for k in ['bed_x_min', 'bed_x_max', 'bed_y_min', 'bed_y_max', 'bed_z_min', 'bed_z_max']):
                config['machineBuildSize'] = {
                    'X': variables['bed_x_max'] - variables['bed_x_min'],
                    'Y': variables['bed_y_max'] - variables['bed_y_min'],
                    'Z': variables['bed_z_max'] - variables['bed_z_min']
                }
            elif all(k in variables for k in ['bed_x_min', 'bed_x_max', 'bed_y_min', 'bed_y_max']):
                # Fallback for backwards compatibility (Z defaults to 400)
                config['machineBuildSize'] = {
                    'X': variables['bed_x_max'] - variables['bed_x_min'],
                    'Y': variables['bed_y_max'] - variables['bed_y_min'],
                    'Z': 400  # Default Z height for backwards compatibility
                }
                
            # Calibration positions (explicit preferred, calculated fallback)
            if all(k in variables for k in ['bed_calibration_x1', 'bed_calibration_y1', 'bed_calibration_x2', 'bed_calibration_y2',
                                            'bed_calibration_x3', 'bed_calibration_y3', 'bed_calibration_x4', 'bed_calibration_y4']):
                config['calibrationPosition'] = {
                    'X1': variables['bed_calibration_x1'],
                    'Y1': variables['bed_calibration_y1'],
                    'X2': variables['bed_calibration_x2'],
                    'Y2': variables['bed_calibration_y2'],
                    'X3': variables['bed_calibration_x3'],
                    'Y3': variables['bed_calibration_y3'],
                    'X4': variables['bed_calibration_x4'],
                    'Y4': variables['bed_calibration_y4']
                }
            elif all(k in variables for k in ['calibration_x1', 'calibration_y1', 'calibration_x2', 'calibration_y2',
                                              'calibration_x3', 'calibration_y3', 'calibration_x4', 'calibration_y4']):
                # Backwards compatibility
                config['calibrationPosition'] = {
                    'X1': variables['calibration_x1'],
                    'Y1': variables['calibration_y1'],
                    'X2': variables['calibration_x2'],
                    'Y2': variables['calibration_y2'],
                    'X3': variables['calibration_x3'],
                    'Y3': variables['calibration_y3'],
                    'X4': variables['calibration_x4'],
                    'Y4': variables['calibration_y4']
                }
            elif 'machineBuildSize' in config:
                # Calculated fallback
                bed_x = config['machineBuildSize']['X']
                bed_y = config['machineBuildSize']['Y']
                
                config['calibrationPosition'] = {
                    'X1': bed_x * 0.18,  'Y1': bed_y * 0.06,
                    'X2': bed_x * 0.85,  'Y2': bed_y * 0.06,
                    'X3': bed_x * 0.52,  'Y3': bed_y * 0.94,
                    'X4': bed_x * 0.52,  'Y4': bed_y * 0.59
                }
                
            # Purge positions
            if all(k in variables for k in ['tool0_pause_position_x', 'tool0_pause_position_y']):
                config['tool0PurgePosition'] = {
                    'X': variables['tool0_pause_position_x'],
                    'Y': variables['tool0_pause_position_y']
                }
                
            # Tool1 only for dual nozzle printers
            if all(k in variables for k in ['tool1_pause_position_x', 'tool1_pause_position_y']):
                config['tool1PurgePosition'] = {
                    'X': variables['tool1_pause_position_x'],
                    'Y': variables['tool1_pause_position_y']
                }
                
            # PTFE tube length (explicit value from configuration)
            if 'ptfe_tube_length' in variables:
                config['ptfeTubeLength'] = variables['ptfe_tube_length']
            else:
                # Fallback to default if not specified
                config['ptfeTubeLength'] = 1500
                
            # Dual nozzle detection
            if 'is_dual_nozzle' in variables:
                config['IS_DUAL_NOZZLE'] = bool(variables['is_dual_nozzle'])
            else:
                # Fallback to fan detection
                config['IS_DUAL_NOZZLE'] = 'fan1' in variables and variables.get('fan1') is not None
            
            logger.info(f"Extracted printer configuration: {config}")
            return config
            
        except Exception as e:
            logger.error(f"Error extracting printer configuration: {e}")
            return {}
    
    def get_printer_config_from_klipper(self) -> Optional[Dict[str, Any]]:
        """Get complete printer configuration extracted from Klipper PRINTER_VARIABLES."""
        try:
            variables = self.get_printer_variables_from_active_config()
            if not variables:
                logger.warning("No PRINTER_VARIABLES found, unable to extract configuration")
                return None
                
            config = self.extract_printer_configuration(variables)
            if not config:
                logger.warning("No configuration could be extracted from PRINTER_VARIABLES")
                return None
                
            # Add raw variables for reference
            config['_raw_variables'] = variables
            
            return config
            
        except Exception as e:
            logger.error(f"Error getting printer config from Klipper: {e}")
            return None

    # ========================================================================
    # FILE DEPLOYMENT AND MANAGEMENT
    # ========================================================================
    
    def update_printer_cfg(self, source_path: str, dest_path: str, selected_printer: str, preserve_mcu: bool = True) -> bool:
        """Update printer.cfg with new printer selection while preserving MCU config."""
        try:
            selected_printer_file = self.get_printer_filename(selected_printer)
            
            # Parse existing config if preserving MCU
            existing_mcu_config = {}
            if preserve_mcu and os.path.exists(dest_path):
                existing_data = self.parse_printer_cfg(dest_path)
                existing_mcu_config = existing_data.get('mcu_config', {})
                logger.info("Preserving MCU config from existing printer.cfg")
            
            # Read source configuration
            with open(source_path, 'r') as f:
                content = f.read()
            
            # Update printer selection section
            def replace_printer_selection(match):
                section_header = match.group(1)
                section_content = match.group(2)
                section_footer = match.group(3)
                
                lines = section_content.split('\n')
                updated_lines = []
                
                for line in lines:
                    if line.strip() and '[include' in line:
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
            
            # Apply printer selection update
            content = re.sub(
                r'(########################################\s*\n# Select Any One Printer Configuration\s*\n)'
                r'(.*?)'
                r'(########################################)',
                replace_printer_selection,
                content,
                flags=re.DOTALL
            )
            
            # Replace MCU config if preserving
            if existing_mcu_config:
                mcu_section_content = "\n\n"
                for mcu_key, mcu_content in existing_mcu_config.items():
                    mcu_section_content += f"{mcu_key}\n{mcu_content}\n\n"
                
                content = re.sub(
                    r'(########################################\s*\n# MCU Config\s*\n########################################\s*\n)'
                    r'(.*?)(?=\n########################################|\n#\*# <---------------------- SAVE_CONFIG|\Z)',
                    r'\1' + mcu_section_content.rstrip(),
                    content,
                    flags=re.DOTALL
                )
            
            # Create backup
            if os.path.exists(dest_path):
                backup_path = f"{dest_path}.backup"
                shutil.copy2(dest_path, backup_path)
                logger.info(f"Created backup at {backup_path}")
            
            # Write updated configuration
            with open(dest_path, 'w') as f:
                f.write(content)
            
            # Set proper permissions for editing
            os.chmod(dest_path, 0o664)  # rw-rw-r--
            
            logger.info(f"Successfully updated printer.cfg with {selected_printer}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating printer.cfg: {e}")
            return False
    
    def copy_firmware_files(self, selected_printer: str) -> bool:
        """Copy all firmware files from firmware folder to Klipper config directory."""
        try:
            source_printer_cfg = os.path.join(self.firmware_path, "printer.cfg")
            
            if not os.path.exists(source_printer_cfg):
                logger.error(f"Source printer.cfg not found at {source_printer_cfg}")
                return False
            
            # Copy all .cfg files except printer.cfg (handled specially)
            firmware_files = []
            if os.path.exists(self.firmware_path):
                for file in os.listdir(self.firmware_path):
                    if file.endswith('.cfg'):
                        firmware_files.append(file)
            
            logger.info(f"Found {len(firmware_files)} configuration files to copy")
            
            copied_files = []
            for filename in firmware_files:
                if filename == 'printer.cfg':
                    continue  # Handle separately
                    
                source_file = os.path.join(self.firmware_path, filename)
                dest_file = os.path.join(self.klipper_config_path, filename)
                
                try:
                    shutil.copy2(source_file, dest_file)
                    
                    # Set proper permissions for editing
                    # Make file readable and writable by owner and group, readable by others
                    # This allows both pi user and web interfaces to edit the files
                    os.chmod(dest_file, 0o664)  # rw-rw-r--
                    
                    copied_files.append(filename)
                    logger.debug(f"Copied {filename} to Klipper config directory with proper permissions")
                except Exception as e:
                    logger.warning(f"Failed to copy {filename}: {e}")
            
            logger.info(f"Successfully copied {len(copied_files)} configuration files")
            
            # Update printer.cfg with selected printer
            success = self.update_printer_cfg(source_printer_cfg, self.printer_cfg_path, selected_printer)
            
            if success:
                logger.info(f"Printer setup completed successfully for {selected_printer}")
                logger.info(f"Copied files: {', '.join(copied_files)}")
            else:
                logger.error(f"Failed to setup printer configuration for {selected_printer}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error copying firmware files: {e}")
            return False

    # ========================================================================
    # BACKUP AND RECOVERY OPERATIONS
    # ========================================================================
    
    def is_config_valid(self, config_path: str = None) -> bool:
        """Check if the printer.cfg file contains the required MCU config marker."""
        if config_path is None:
            config_path = self.printer_cfg_path
            
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                return "# MCU Config" in content
        except Exception as e:
            logger.error(f"Could not read {config_path}: {e}")
            return False
    
    def get_backup_files(self, pattern: str = None) -> List[str]:
        """Return a list of backup config files sorted by modification time (newest first)."""
        if pattern is None:
            pattern = self.backup_pattern
            
        return sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    
    def restore_backup_config(self, config_path: str = None, backup_pattern: str = None) -> bool:
        """Try to restore the most recent valid backup config file."""
        if config_path is None:
            config_path = self.printer_cfg_path
        if backup_pattern is None:
            backup_pattern = self.backup_pattern
            
        backup_files = self.get_backup_files(backup_pattern)
        for backup_file in backup_files:
            try:
                with open(backup_file, 'r') as f:
                    content = f.read()
                    if "# MCU Config" in content:
                        try:
                            if os.path.exists(config_path):
                                os.remove(config_path)
                        except Exception as e:
                            logger.error(f"Failed to delete {config_path}: {e}")
                        try:
                            os.rename(backup_file, config_path)
                            logger.info("Printer Config File Restored from backup: %s", backup_file)
                            return True
                        except Exception as e:
                            logger.error(f"Failed to rename {backup_file} to {config_path}: {e}")
            except Exception as e:
                logger.error(f"Failed to read backup file {backup_file}: {e}")
        return False
    
    def cleanup_old_backups(self, keep: int = 5, backup_pattern: str = None) -> None:
        """Remove old backup files, keeping only the most recent 'keep' files."""
        if backup_pattern is None:
            backup_pattern = self.backup_pattern
            
        backup_files = self.get_backup_files(backup_pattern)
        for old_file in backup_files[keep:]:
            try:
                os.remove(old_file)
                logger.info(f"Deleted old backup file: {old_file}")
            except Exception as e:
                logger.error(f"Failed to delete old backup file {old_file}: {e}")
    
    def check_klipper_config_files(self) -> Dict[str, bool]:
        """Check which firmware files are present in the Klipper config directory."""
        firmware_files = self.get_firmware_files()
        file_status = {}
        
        for filename in firmware_files:
            dest_path = os.path.join(self.klipper_config_path, filename)
            file_status[filename] = os.path.exists(dest_path)
        
        return file_status
    
    def get_missing_config_files(self) -> List[str]:
        """Get list of firmware files missing from Klipper config directory."""
        file_status = self.check_klipper_config_files()
        return [filename for filename, exists in file_status.items() if not exists]
    
    def fix_config_permissions(self) -> Dict[str, bool]:
        """Fix permissions on configuration files in Klipper config directory."""
        results = {}
        
        try:
            # Fix printer.cfg permissions
            if os.path.exists(self.printer_cfg_path):
                try:
                    os.chmod(self.printer_cfg_path, 0o664)
                    results['printer.cfg'] = True
                    logger.info("Fixed permissions for printer.cfg")
                except Exception as e:
                    results['printer.cfg'] = False
                    logger.error(f"Failed to fix permissions for printer.cfg: {e}")
            
            # Fix all firmware config files
            firmware_files = self.get_firmware_files()
            for filename in firmware_files:
                if filename == 'printer.cfg':
                    continue  # Already handled above
                    
                dest_path = os.path.join(self.klipper_config_path, filename)
                if os.path.exists(dest_path):
                    try:
                        os.chmod(dest_path, 0o664)
                        results[filename] = True
                        logger.debug(f"Fixed permissions for {filename}")
                    except Exception as e:
                        results[filename] = False
                        logger.warning(f"Failed to fix permissions for {filename}: {e}")
                else:
                    results[filename] = False  # File doesn't exist
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            logger.info(f"Fixed permissions for {success_count}/{total_count} configuration files")
            
            return results
            
        except Exception as e:
            logger.error(f"Error fixing config permissions: {e}")
            return {}


# ============================================================================
# SINGLETON INSTANCE AND CONVENIENCE FUNCTIONS
# ============================================================================

# Create singleton instance
_klipper_config_manager = None

def get_klipper_config_manager() -> KlipperConfigManager:
    """Get singleton instance of KlipperConfigManager."""
    global _klipper_config_manager
    if _klipper_config_manager is None:
        _klipper_config_manager = KlipperConfigManager()
    return _klipper_config_manager


# Convenience functions for backwards compatibility
def get_available_printers() -> List[str]:
    """Get list of available printer configurations."""
    return get_klipper_config_manager().get_available_printers()

def get_printer_display_name(printer_name: str) -> str:
    """Convert printer name to display name."""
    return get_klipper_config_manager().get_printer_display_name(printer_name)

def get_printer_filename(printer_name: str) -> str:
    """Convert printer name back to filename format."""
    return get_klipper_config_manager().get_printer_filename(printer_name)

def get_current_printer_selection() -> Optional[str]:
    """Get the currently active printer configuration."""
    return get_klipper_config_manager().get_current_printer_selection()

def copy_firmware_files(selected_printer: str) -> bool:
    """Copy all firmware files and update printer selection."""
    return get_klipper_config_manager().copy_firmware_files(selected_printer)

def get_printer_config_from_klipper() -> Optional[Dict[str, Any]]:
    """Get complete printer configuration from active Klipper config."""
    return get_klipper_config_manager().get_printer_config_from_klipper()

def parse_printer_variables_from_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Parse PRINTER_VARIABLES from a specific file."""
    return get_klipper_config_manager().parse_printer_variables_from_file(file_path)

def extract_printer_configuration(variables: Dict[str, Any]) -> Dict[str, Any]:
    """Extract configuration from PRINTER_VARIABLES."""
    return get_klipper_config_manager().extract_printer_configuration(variables)

def fix_config_permissions() -> Dict[str, bool]:
    """Fix permissions on configuration files in Klipper config directory."""
    return get_klipper_config_manager().fix_config_permissions()
