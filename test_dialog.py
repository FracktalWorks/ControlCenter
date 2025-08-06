#!/usr/bin/env python3
"""
Test script to verify dialog box improvements
Run this script to test the enhanced dialog boxes with:
- Reduced font size (12pt instead of 14pt)
- Word wrapping enabled
- Better text formatting
- Maximum width constraints
"""

import sys
import os

# Add the octoprint_ControlCenter directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'octoprint_ControlCenter'))

try:
    from PyQt5 import QtWidgets, QtCore
    from utils import dialog
    
    def test_dialogs():
        app = QtWidgets.QApplication(sys.argv)
        
        print("Testing improved dialog boxes...")
        
        # Test short message
        print("1. Testing short message...")
        dialog.WarningOk(None, "Short message test")
        
        # Test long message that should wrap
        print("2. Testing long message with word wrapping...")
        long_message = ("This is a very long error message that should wrap properly within the dialog box. "
                       "It contains multiple sentences to test the word wrapping functionality. "
                       "The text should fit nicely within the dialog without overflowing or being cut off. "
                       "This helps ensure a better user experience when displaying error messages. "
                       "The font size has been reduced to 12pt for better fitting.")
        
        dialog.WarningOk(None, long_message)
        
        # Test message with line breaks (like actual error messages in the app)
        print("3. Testing message with line breaks...")
        multiline_message = ("Server Connection Error\n\n"
                            "The printer server is not reachable. Only basic features are available.\n\n"
                            "Please check your network connection and printer status.")
        
        dialog.WarningOk(None, multiline_message)
        
        # Test application error message format
        print("4. Testing application error message format...")
        app_error_message = ("Application Error\n\n"
                            "An error occurred while initializing the application: ConnectionTimeout: Unable to establish connection to printer server after 30 seconds. The server may be down or network connectivity issues may be preventing access.\n\n"
                            "Please check the logs for more details.")
        
        dialog.WarningOk(None, app_error_message)
        
        # Test extremely long message
        print("5. Testing extremely long message...")
        very_long_message = ("Error in MainUiClass.softwareUpdateProgress: " + 
                           "This is an extremely long error message that simulates what might happen when a very detailed error occurs in the system. " * 5 +
                           "Additional diagnostic information and stack trace details would normally appear here.")
        
        dialog.WarningOk(None, very_long_message)
        
        print("All dialog tests completed!")
        app.quit()
    
    if __name__ == "__main__":
        test_dialogs()
        
except ImportError as e:
    print(f"Could not import required modules: {e}")
    print("This test requires PyQt5 to be installed.")
    print("To run this test:")
    print("1. Ensure PyQt5 is installed: pip install PyQt5")
    print("2. Run the test: python test_dialog.py")
