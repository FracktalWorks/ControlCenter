#!/usr/bin/env python3
"""
Regression tests for printer.cfg MCU validation in utils/printer_config_manager.py.

These cover the failure that halted the TwinDragon 400 HT: a deployed printer.cfg
whose [mcu] block held another machine's canbus_uuid values and had no
[mcu toolhead1] section, while the active printer config referenced toolhead1 pins.
"""

import os
import sys
import tempfile
import unittest

# Add the octoprint_ControlCenter directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'octoprint_ControlCenter'))

try:
    import yaml  # noqa: F401  (printer_config_manager requires it)
except ImportError:
    raise unittest.SkipTest("PyYAML is required to import printer_config_manager")

from utils.printer_config_manager import PrinterConfigManager


VALID_PRINTER_CFG = """\
[mcu]
canbus_uuid: 0a58f8645369

[mcu toolhead0]
canbus_uuid: ecda989b639d

[mcu toolhead1]
canbus_uuid: 27006611a2db
"""

# What a factory-restore of the stale template left behind on the printer
BROKEN_PRINTER_CFG = """\
[mcu]
canbus_uuid: d9d3f257e82c

[mcu toolhead0]
canbus_uuid: 2e49f7a5e543

#[mcu toolhead1]
#canbus_uuid: 3ec1b8773dd7
"""

TOOLHEAD1_INCLUDE = """\
[include TOOLHEADS_TD-01_TOOLHEAD1.cfg]
"""

TOOLHEAD1_CFG = """\
[tmc5160 stepper_x1]
cs_pin: toolhead1: gpio13

[extruder1]
heater_pin: toolhead1: gpio20
sensor_pin: toolhead1: gpio26
"""


class McuConfigValidationTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='mcu-validation-')
        self.manager = PrinterConfigManager()

    def tearDown(self):
        for name in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, name))
        os.rmdir(self.temp_dir)

    def _write(self, name, text):
        with open(os.path.join(self.temp_dir, name), 'w') as handle:
            handle.write(text)

    def test_complete_mcu_set_is_accepted(self):
        self._write('TOOLHEADS_TD-01_TOOLHEAD1.cfg', TOOLHEAD1_CFG)
        is_valid, reason = self.manager.validate_mcu_configuration(
            VALID_PRINTER_CFG + TOOLHEAD1_INCLUDE, self.temp_dir)
        self.assertTrue(is_valid, reason)

    def test_commented_toolhead1_is_rejected(self):
        self._write('TOOLHEADS_TD-01_TOOLHEAD1.cfg', TOOLHEAD1_CFG)
        is_valid, reason = self.manager.validate_mcu_configuration(
            BROKEN_PRINTER_CFG + TOOLHEAD1_INCLUDE, self.temp_dir)
        self.assertFalse(is_valid)
        self.assertIn('toolhead1', reason)

    def test_placeholder_canbus_uuid_is_rejected(self):
        config = VALID_PRINTER_CFG.replace('27006611a2db', 'XXXXXXXXXXX')
        is_valid, reason = self.manager.validate_mcu_configuration(config, self.temp_dir)
        self.assertFalse(is_valid)
        self.assertIn('canbus_uuid', reason)

    def test_serial_mcu_is_accepted(self):
        is_valid, reason = self.manager.validate_mcu_configuration(
            "[mcu]\nserial: /dev/ttyACM0\n", self.temp_dir)
        self.assertTrue(is_valid, reason)

    def test_missing_mainboard_is_rejected(self):
        is_valid, reason = self.manager.validate_mcu_configuration(
            "[mcu toolhead0]\ncanbus_uuid: ecda989b639d\n", self.temp_dir)
        self.assertFalse(is_valid)
        self.assertIn('[mcu]', reason)

    def test_mcu_without_uuid_or_serial_is_rejected(self):
        is_valid, reason = self.manager.validate_mcu_configuration(
            "[mcu]\nrestart_method: command\n", self.temp_dir)
        self.assertFalse(is_valid)
        self.assertIn('canbus_uuid', reason)


class BackupModelGuardTest(unittest.TestCase):
    """A backup from another printer model must never be restored over this unit."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='backup-guard-')
        self.manager = PrinterConfigManager()
        self.manager.printer_cfg_path = os.path.join(self.temp_dir, 'printer.cfg')
        self.manager.backup_pattern = os.path.join(self.temp_dir, 'printer-*.cfg')

        self._write('TOOLHEADS_TD-01_TOOLHEAD1.cfg', TOOLHEAD1_CFG)
        self._write('PRINTER_TWINDRAGON_400_HT.cfg', TOOLHEAD1_INCLUDE)
        self._write('PRINTER_DRAGON_400.cfg', '# single nozzle\n')

        self._write('printer.cfg',
                    VALID_PRINTER_CFG + '[include PRINTER_TWINDRAGON_400_HT.cfg]\n')
        # Newest backup belongs to another model, older one matches this unit
        self._write('printer-20260102_000000.cfg',
                    VALID_PRINTER_CFG + '[include PRINTER_DRAGON_400.cfg]\n')
        self._write('printer-20260101_000000.cfg',
                    VALID_PRINTER_CFG + '[include PRINTER_TWINDRAGON_400_HT.cfg]\n')

    def tearDown(self):
        for name in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, name))
        os.rmdir(self.temp_dir)

    def _write(self, name, text):
        with open(os.path.join(self.temp_dir, name), 'w') as handle:
            handle.write(text)

    def test_restore_skips_backups_for_other_models(self):
        self.assertTrue(self.manager.restore_backup_config())

        with open(self.manager.printer_cfg_path, 'r') as handle:
            restored = handle.read()
        self.assertIn('PRINTER_TWINDRAGON_400_HT.cfg', restored)
        self.assertNotIn('[include PRINTER_DRAGON_400.cfg]', restored)


if __name__ == '__main__':
    unittest.main()
