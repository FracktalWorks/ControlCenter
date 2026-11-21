#!/usr/bin/env python3
"""
Regression tests for webcam endpoint handling in utils/printer_config_manager.py.

The printer has no reverse proxy, so OctoPrint's webcam must use an absolute
LAN URL. A failed IP probe during a WiFi change used to write 127.0.0.1, which
removed the feed for every remote browser (and never recovered until redeployment).
"""

import os
import sys
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


if __name__ == '__main__':
    unittest.main()
