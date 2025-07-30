import os
import glob
import logging

logger = logging.getLogger(__name__)

PRINTER_CFG_PATH = '/home/pi/printer.cfg'
BACKUP_CFG_PATTERN = '/home/pi/printer-*.cfg'


def is_config_valid(config_path=PRINTER_CFG_PATH):
    """Check if the printer.cfg file contains the required MCU config marker."""
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            return "# MCU Config" in content
    except Exception as e:
        logger.error(f"Could not read {config_path}: {e}")
        return False


def get_backup_files(pattern=BACKUP_CFG_PATTERN):
    """Return a list of backup config files sorted by modification time (newest first)."""
    return sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)


def restore_backup_config(config_path=PRINTER_CFG_PATH, backup_pattern=BACKUP_CFG_PATTERN):
    """Try to restore the most recent valid backup config file."""
    backup_files = get_backup_files(backup_pattern)
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


def cleanup_old_backups(keep=5, backup_pattern=BACKUP_CFG_PATTERN):
    """Remove old backup files, keeping only the most recent 'keep' files."""
    backup_files = get_backup_files(backup_pattern)
    for old_file in backup_files[keep:]:
        try:
            os.remove(old_file)
            logger.info(f"Deleted old backup file: {old_file}")
        except Exception as e:
            logger.error(f"Failed to delete old backup file {old_file}: {e}")
