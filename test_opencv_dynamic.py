"""
Simple test for dynamic OpenCV import
"""

import sys
import subprocess

# Dynamic OpenCV import with automatic installation (same as in main file)
try:
    import cv2
    print(f"✓ OpenCV already available - version: {cv2.__version__}")
except ImportError:
    print("OpenCV not found. Attempting to install...")
    try:
        # Try to install opencv-python automatically
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'opencv-python'])
        import cv2
        print("✓ OpenCV installed successfully!")
    except subprocess.CalledProcessError:
        # If pip install fails, try with sudo
        try:
            subprocess.check_call(['sudo', 'pip', 'install', 'opencv-python'])
            import cv2
            print("✓ OpenCV installed successfully with sudo!")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Failed to automatically install OpenCV: {e}")
            print("Please install it manually with: pip install opencv-python or sudo pip install opencv-python")
            sys.exit(1)

# Test camera availability
print("Testing camera availability...")
camera_found = False
for i in range(3):
    try:
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                print(f"✓ Camera found at index {i}")
                camera_found = True
                break
    except Exception as e:
        print(f"Error testing camera {i}: {e}")

if not camera_found:
    print("ℹ No USB cameras detected - this is normal if no cameras are connected")

print("✓ Dynamic OpenCV import test completed successfully!")
