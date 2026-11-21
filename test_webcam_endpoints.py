#!/usr/bin/env python3
"""
Regression tests for webcam endpoint handling in utils/printer_config_manager.py.

The printer has no reverse proxy, so OctoPrint's webcam must use an absolute
LAN URL. A failed IP probe during a WiFi change used to write 127.0.0.1, which
removed the feed for every remote browser (and never recovered until redeployment).
"""

import os
import shutil
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


class WebcamEndpointTest(unittest.TestCase):

    def setUp(self):
        self.manager = PrinterConfigManager()

    @staticmethod
    def _config(stream, snapshot):
        return {
            'webcam': {'stream': stream, 'snapshot': snapshot},
            'plugins': {'classicwebcam': {'stream': stream, 'snapshot': snapshot}},
        }

    def test_lan_ip_sets_absolute_urls(self):
        self.manager._get_lan_ip = lambda: '192.168.1.50'
        config = self._config('http://127.0.0.1:8080/?action=stream',
                              'http://127.0.0.1:8080/?action=snapshot')

        self.manager._apply_webcam_endpoints(config)

        self.assertEqual(config['plugins']['classicwebcam']['stream'],
                         'http://192.168.1.50:8080/?action=stream')
        self.assertEqual(config['plugins']['classicwebcam']['snapshot'],
                         'http://192.168.1.50:8080/?action=snapshot')
        self.assertEqual(config['webcam']['stream'],
                         'http://192.168.1.50:8080/?action=stream')

    def test_unknown_ip_keeps_previous_endpoints(self):
        self.manager._get_lan_ip = lambda: None
        config = self._config('http://10.0.0.5:8080/?action=stream',
                              'http://10.0.0.5:8080/?action=snapshot')

        self.manager._apply_webcam_endpoints(config)

        self.assertEqual(config['plugins']['classicwebcam']['stream'],
                         'http://10.0.0.5:8080/?action=stream')
        self.assertEqual(config['webcam']['snapshot'],
                         'http://10.0.0.5:8080/?action=snapshot')

    def test_refresh_does_nothing_without_lan_ip(self):
        self.manager._get_lan_ip = lambda: None
        self.assertFalse(self.manager.refresh_webcam_endpoints())


class OctoPrintConfigDeployTest(unittest.TestCase):
    """Deploying config.yaml must not reset the timelapse recording configuration."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='op-config-')
        templates = os.path.join(self.temp_dir, 'templates')
        octoprint = os.path.join(self.temp_dir, 'octoprint')
        os.makedirs(templates)
        os.makedirs(octoprint)
        self.dest = os.path.join(octoprint, 'config.yaml')

        with open(os.path.join(templates, 'config.yaml'), 'w') as handle:
            yaml.safe_dump({
                'webcam': {
                    'ffmpeg': '/usr/bin/ffmpeg',
                    'timelapseEnabled': True,
                    'timelapse': {'type': 'zchange', 'fps': 25},
                }
            }, handle)

        self.manager = PrinterConfigManager()
        self.manager.config_path = templates
        self.manager.octoprint_config_path = octoprint
        self.manager.firmware_path = templates

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _deploy(self):
        self.assertTrue(self.manager.update_octoprint_config('TWINDRAGON_400_HT'))
        with open(self.dest, 'r') as handle:
            return yaml.safe_load(handle)

    def test_deploy_preserves_live_timelapse(self):
        with open(self.dest, 'w') as handle:
            yaml.safe_dump({
                'api': {'key': 'ABCDEF0123456789'},
                'webcam': {
                    'timelapseEnabled': True,
                    'timelapse': {'type': 'timed', 'fps': 30,
                                  'options': {'interval': 30}},
                },
            }, handle)

        deployed = self._deploy()

        self.assertEqual(deployed['webcam']['timelapse']['type'], 'timed')
        self.assertEqual(deployed['webcam']['timelapse']['options']['interval'], 30)
        self.assertEqual(deployed['api']['key'], 'ABCDEF0123456789')

    def test_template_timelapse_used_when_none_configured(self):
        with open(self.dest, 'w') as handle:
            yaml.safe_dump({'webcam': {'ffmpeg': '/usr/bin/ffmpeg'}}, handle)

        deployed = self._deploy()

        self.assertEqual(deployed['webcam']['timelapse']['type'], 'zchange')


if __name__ == '__main__':
    unittest.main()
