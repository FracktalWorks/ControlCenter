import os
import time
import logging
from concurrent.futures import Future
from PyQt5.QtCore import QObject, pyqtSignal

from layerManager.layerQueueManager import LayerQueueManager
from layerManager.printStateManager import PrintStateManager
from utils.helpers import run_async

class MultiLayerPrintController(QObject):
    """
    Controller for managing multi-layer printing process.
    Coordinates the layer queue, print state, and automation processes.
    """
    
    # Signals
    progress_update_signal = pyqtSignal(int)
    status_update_signal = pyqtSignal(str)
    layer_changed_signal = pyqtSignal(int, str)  # layer_index, layer_file
    print_completed_signal = pyqtSignal()
    print_paused_signal = pyqtSignal()
    print_resumed_signal = pyqtSignal()
    print_aborted_signal = pyqtSignal(str)  # reason
    
    def __init__(self, main_window):
        """
        Initialize the multi-layer print controller.
        
        Args:
            main_window: The main application window
        """
        super().__init__()
        self.main_window = main_window
        self.layer_manager = LayerQueueManager()
        self.state_manager = PrintStateManager()
        
        # Get references to necessary components
        self.process_automation = main_window.process_automation_controller
        self.scancard = main_window.scancard
        
        # State variables
        self.print_in_progress = False
        self.paused = False
        self.aborted = False
        self.current_operation = "idle"
        self.current_state_file = None
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
    def load_layer_files(self, folder_path):
        """
        Load layer files from a folder.
        
        Args:
            folder_path (str): Path to the folder containing layer files
            
        Returns:
            list: List of layer file paths
        """
        self.logger.info(f"Loading layer files from folder: {folder_path}")
        layer_files = self.layer_manager.load_from_folder(folder_path)
        return layer_files
    
    @run_async
    def start_multi_layer_print(self):
        """
        Start the multi-layer print process.
        """
        if len(self.layer_manager.layer_files) == 0:
            self.logger.error("No layer files loaded")
            self.print_aborted_signal.emit("No layer files loaded")
            return
            
        if self.print_in_progress:
            self.logger.warning("Print already in progress")
            return
            
        self.print_in_progress = True
        self.paused = False
        self.aborted = False
        
        # Reset layer manager to start from the beginning
        self.layer_manager.reset()
        
        # Save initial state
        self._save_current_state()
        
        self.logger.info("Starting multi-layer print process")
        self.status_update_signal.emit("Starting print process")
        
        try:
            # Initial setup
            yield from self._perform_initial_setup()
            
            if self.aborted:
                self.logger.info("Print aborted during initial setup")
                self.print_aborted_signal.emit("Aborted during initial setup")
                return
                
            # Process each layer
            while self.layer_manager.get_next_layer() is not None:
                if self.aborted:
                    self.logger.info("Print aborted")
                    self.print_aborted_signal.emit("Aborted by user")
                    return
                    
                # Handle pause state
                yield from self._handle_pause_state()
                
                if self.aborted:
                    self.logger.info("Print aborted during pause")
                    self.print_aborted_signal.emit("Aborted during pause")
                    return
                
                # Process the current layer
                current_layer = self.layer_manager.get_current_layer()
                current_index = self.layer_manager.current_layer_index
                
                # Update UI
                self.progress_update_signal.emit(self.layer_manager.progress_percentage())
                self.layer_changed_signal.emit(current_index, current_layer)
                
                # Process the layer
                yield from self._process_layer(current_layer)
                
                # Save state after each layer
                self._save_current_state()
                
            # Finalize print
            if not self.aborted:
                yield from self._finalize_print()
                self.print_completed_signal.emit()
                
        except Exception as e:
            self.logger.error(f"Error in multi-layer print: {e}", exc_info=True)
            self.print_aborted_signal.emit(f"Error: {str(e)}")
            
        finally:
            self.print_in_progress = False
            self.current_operation = "idle"
            self.status_update_signal.emit("Print process ended")
    
    @run_async
    def resume_multi_layer_print(self, state_file=None):
        """
        Resume printing from a saved state.
        
        Args:
            state_file (str, optional): Path to the state file to resume from.
                If None, uses the most recently saved state.
        """
        # If no state file provided, use the current one
        if state_file is None:
            state_file = self.current_state_file
            
        if state_file is None:
            saved_states = self.state_manager.list_saved_states()
            if not saved_states:
                self.logger.error("No saved states found to resume from")
                self.print_aborted_signal.emit("No saved states found")
                return
                
            # Use the most recent state
            state_file = saved_states[0]['file_path']
            
        # Load the state
        state = self.state_manager.load_print_state(state_file)
        if not state:
            self.logger.error(f"Failed to load state from {state_file}")
            self.print_aborted_signal.emit("Failed to load state")
            return
            
        # Restore the state
        self.layer_manager.layer_files = state['layer_files']
        self.layer_manager.total_layers = state['total_layers']
        current_layer_index = state['current_layer_index']
        
        # Set the current layer
        self.layer_manager.set_current_layer_index(current_layer_index)
        
        # Start/resume the print
        self.current_state_file = state_file
        self.print_in_progress = True
        self.paused = False
        self.aborted = False
        
        self.logger.info(f"Resuming print from layer {current_layer_index + 1} of {self.layer_manager.total_layers}")
        self.status_update_signal.emit(f"Resuming print from layer {current_layer_index + 1}")
        self.print_resumed_signal.emit()
        
        try:
            # Update UI
            self.progress_update_signal.emit(self.layer_manager.progress_percentage())
            current_layer = self.layer_manager.get_current_layer()
            if current_layer:
                self.layer_changed_signal.emit(current_layer_index, current_layer)
            
            # Process each remaining layer
            while self.layer_manager.get_next_layer() is not None:
                if self.aborted:
                    self.logger.info("Print aborted")
                    self.print_aborted_signal.emit("Aborted by user")
                    return
                    
                # Handle pause state
                yield from self._handle_pause_state()
                
                if self.aborted:
                    self.logger.info("Print aborted during pause")
                    self.print_aborted_signal.emit("Aborted during pause")
                    return
                
                # Process the current layer
                current_layer = self.layer_manager.get_current_layer()
                current_index = self.layer_manager.current_layer_index
                
                # Update UI
                self.progress_update_signal.emit(self.layer_manager.progress_percentage())
                self.layer_changed_signal.emit(current_index, current_layer)
                
                # Process the layer
                yield from self._process_layer(current_layer)
                
                # Save state after each layer
                self._save_current_state()
                
            # Finalize print
            if not self.aborted:
                yield from self._finalize_print()
                self.print_completed_signal.emit()
                
        except Exception as e:
            self.logger.error(f"Error in resuming multi-layer print: {e}", exc_info=True)
            self.print_aborted_signal.emit(f"Error: {str(e)}")
            
        finally:
            self.print_in_progress = False
            self.current_operation = "idle"
            self.status_update_signal.emit("Print process ended")
    
    def pause_print(self):
        """Pause the print process."""
        if self.print_in_progress and not self.paused:
            self.paused = True
            self.logger.info("Print paused")
            self.status_update_signal.emit("Print paused")
            self.print_paused_signal.emit()
    
    def resume_print(self):
        """Resume a paused print."""
        if self.print_in_progress and self.paused:
            self.paused = False
            self.logger.info("Print resumed")
            self.status_update_signal.emit("Print resumed")
            self.print_resumed_signal.emit()