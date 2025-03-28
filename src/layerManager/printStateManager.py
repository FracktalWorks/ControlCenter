import json
import os
import time
import logging
from datetime import datetime

class PrintStateManager:
    """
    Manages the saving and loading of print states to enable resumable printing.
    """
    
    def __init__(self, state_dir="print_states"):
        """
        Initialize the print state manager.
        
        Args:
            state_dir (str): Directory to store print state files
        """
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
        
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
        
    def save_print_state(self, state):
        """
        Save the current print state to a file.
        
        Args:
            state (dict): The print state to save, containing:
                - current_layer_index: Index of the current layer
                - total_layers: Total number of layers
                - layer_files: List of layer file paths
                - timestamp: When the state was saved (added automatically)
                
        Returns:
            str: Path to the saved state file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"print_state_{timestamp}.pstate"
        filepath = os.path.join(self.state_dir, filename)
        
        # Add timestamp to state
        state_with_timestamp = state.copy()
        state_with_timestamp['timestamp'] = timestamp
        state_with_timestamp['save_time'] = time.time()
        
        try:
            with open(filepath, 'w') as f:
                json.dump(state_with_timestamp, f, indent=2)
                
            self.logger.info(f"Print state saved to {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Error saving print state: {e}")
            return None
        
    def load_print_state(self, state_file):
        """
        Load a print state from a file.
        
        Args:
            state_file (str): Path to the state file to load
            
        Returns:
            dict: The loaded state, or None if loading failed
        """
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
                
            # Validate that the necessary keys are present
            required_keys = ['current_layer_index', 'total_layers', 'layer_files']
            if not all(key in state for key in required_keys):
                self.logger.error(f"Invalid state file: missing required keys")
                return None
                
            self.logger.info(f"Loaded print state from {state_file}")
            return state
        except Exception as e:
            self.logger.error(f"Error loading print state: {e}")
            return None
            
    def list_saved_states(self):
        """
        List all saved print states.
        
        Returns:
            list: List of dictionaries containing state information:
                - file_path: Path to the state file
                - timestamp: When the state was saved
                - current_layer: Current layer index
                - total_layers: Total number of layers
        """
        state_files = []
        
        try:
            for file in os.listdir(self.state_dir):
                if file.endswith(".pstate"):
                    file_path = os.path.join(self.state_dir, file)
                    
                    try:
                        with open(file_path, 'r') as f:
                            state = json.load(f)
                            
                        state_info = {
                            'file_path': file_path,
                            'timestamp': state.get('timestamp', 'Unknown'),
                            'current_layer': state.get('current_layer_index', -1) + 1,
                            'total_layers': state.get('total_layers', 0),
                            'save_time': state.get('save_time', 0)
                        }
                        
                        state_files.append(state_info)
                    except Exception as e:
                        self.logger.warning(f"Error reading state file {file}: {e}")
            
            # Sort by save time, newest first
            state_files.sort(key=lambda x: x['save_time'], reverse=True)
            
            return state_files
        except Exception as e:
            self.logger.error(f"Error listing saved states: {e}")
            return []
    
    def delete_state_file(self, state_file):
        """
        Delete a state file.
        
        Args:
            state_file (str): Path to the state file to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if os.path.exists(state_file):
                os.remove(state_file)
                self.logger.info(f"Deleted state file {state_file}")
                return True
            else:
                self.logger.warning(f"State file not found: {state_file}")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting state file: {e}")
            return False