from PyQt5 import QtCore
import logging

logger = logging.getLogger(__name__)

class ThreadFileUpload(QtCore.QThread):
    """Thread to handle file uploads to OctoPrint without blocking UI"""
    
    upload_complete_signal = QtCore.pyqtSignal(bool, str)
    
    def __init__(self, file, print_after_upload=False):
        """Initialize the file upload thread"""
        super(ThreadFileUpload, self).__init__()
        self.file = file
        self.print_after_upload = print_after_upload
        logger.info(f"Initialized ThreadFileUpload for {file}")

    def run(self):
        """Run the file upload process"""
        from octoprint_client import octoprint_singleton
        
        logger.info(f"Starting file upload: {self.file}")
        try:
            # Check if there's a thumbnail image to upload
            if self.file.lower().endswith('.gcode'):
                thumbnail_file = self.file.replace(".gcode", ".png")
                try:
                    import os
                    if os.path.exists(thumbnail_file):
                        logger.info(f"Uploading thumbnail: {thumbnail_file}")
                        octoprint_singleton.get_client().uploadImage(thumbnail_file)
                except Exception as e:
                    logger.error(f"Failed to upload thumbnail: {e}")
            
            # Upload the gcode file
            if self.print_after_upload:
                logger.info(f"Uploading and printing file: {self.file}")
                octoprint_singleton.get_client().uploadGcode(file=self.file, select=True, prnt=True)
            else:
                logger.info(f"Uploading file: {self.file}")
                octoprint_singleton.get_client().uploadGcode(file=self.file, select=False, prnt=False)
                
            self.upload_complete_signal.emit(True, self.file)
            logger.info("File upload completed successfully")
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            self.upload_complete_signal.emit(False, str(e))
