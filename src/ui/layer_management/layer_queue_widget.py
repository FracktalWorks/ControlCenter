from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                          QListWidgetItem, QLabel, QProgressBar, QPushButton, 
                          QMenu, QAction, QMessageBox)
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QIcon, QColor, QBrush
import os
import logging

class LayerQueueWidget(QWidget):
    """
    Widget for displaying and managing a queue of layer files.
    """
    
    layer_selected = pyqtSignal(int, str)  # Index, filepath
    
    def __init__(self):
        """Initialize the layer queue widget."""
        super().__init__()
        self.layer_files = []
        self.current_layer_index = -1
        
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
        
        self.initUI()
        
    def initUI(self):
        """Initialize the user interface components."""
        layout = QVBoxLayout()
        
        # Layer count and controls
        header_layout = QHBoxLayout()
        
        self.count_label = QLabel("Layers: 0")
        header_layout.addWidget(self.count_label)
        
        header_layout.addStretch()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setToolTip("Refresh the layer list")
        self.refresh_button.clicked.connect(self.refresh_layer_list)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Layer list
        self.layer_list = QListWidget()
        self.layer_list.setSelectionMode(QListWidget.SingleSelection)
        self.layer_list.itemClicked.connect(self.on_layer_selected)
        self.layer_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.layer_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set size for items
        self.layer_list.setIconSize(QSize(16, 16))
        
        layout.addWidget(self.layer_list)
        
        # Current progress section
        progress_layout = QVBoxLayout()
        
        progress_layout.addWidget(QLabel("Current Layer:"))
        self.current_layer_label = QLabel("None")
        progress_layout.addWidget(self.current_layer_label)
        
        self.layer_progress = QProgressBar()
        self.layer_progress.setRange(0, 100)
        self.layer_progress.setValue(0)
        progress_layout.addWidget(self.layer_progress)
        
        layout.addLayout(progress_layout)
        
        self.setLayout(layout)
        
    def set_layer_files(self, layer_files):
        """
        Set the layer files to display.
        
        Args:
            layer_files (list): List of file paths to layer files
        """
        self.layer_files = layer_files
        self.refresh_layer_list()
        
    def refresh_layer_list(self):
        """Refresh the layer list display."""
        self.layer_list.clear()
        
        for i, filepath in enumerate(self.layer_files):
            filename = os.path.basename(filepath)
            item = QListWidgetItem(f"{i+1}: {filename}")
            
            # Set icon or styling based on layer status
            if i < self.current_layer_index:
                # Completed layer
                item.setForeground(QBrush(QColor(100, 100, 100)))  # Gray out completed
            elif i == self.current_layer_index:
                # Current layer
                item.setForeground(QBrush(QColor(0, 100, 0)))  # Green for current
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            self.layer_list.addItem(item)
            
        self.count_label.setText(f"Layers: {len(self.layer_files)}")
        
        # Update current layer label and progress
        self.update_current_layer(self.current_layer_index)
        
    def on_layer_selected(self, item):
        """
        Handle layer selection.
        
        Args:
            item (QListWidgetItem): The selected item
        """
        index = self.layer_list.row(item)
        if 0 <= index < len(self.layer_files):
            self.layer_selected.emit(index, self.layer_files[index])
            self.logger.debug(f"Layer {index} selected: {self.layer_files[index]}")
            
    def update_current_layer(self, index):
        """
        Update the UI to show the current layer.
        
        Args:
            index (int): Index of the current layer
        """
        self.current_layer_index = index
        
        # Update layer list selection
        if 0 <= index < self.layer_list.count():
            self.layer_list.setCurrentRow(index)
            
            # Update layer info
            filename = os.path.basename(self.layer_files[index])
            self.current_layer_label.setText(f"{index + 1}/{len(self.layer_files)}: {filename}")
            
            # Update progress
            progress = int((index + 1) / len(self.layer_files) * 100)
            self.layer_progress.setValue(progress)
        else:
            self.current_layer_label.setText("None")
            self.layer_progress.setValue(0)
            
        # Refresh the list to update styling
        self.refresh_layer_list()
        
    def show_context_menu(self, position):
        """
        Show a context menu for the layer list.
        
        Args:
            position: The position where to show the menu
        """
        if not self.layer_files:
            return
            
        menu = QMenu()
        
        # Get the item at position
        item = self.layer_list.itemAt(position)
        if item:
            index = self.layer_list.row(item)
            view_action = menu.addAction("View Layer Details")
            view_action.triggered.connect(lambda: self.show_layer_details(index))
            
            if index != self.current_layer_index:
                set_current_action = menu.addAction("Set as Current Layer")
                set_current_action.triggered.connect(lambda: self.set_as_current_layer(index))
        
        menu.exec_(self.layer_list.mapToGlobal(position))
        
    def show_layer_details(self, index):
        """
        Show details for a specific layer.
        
        Args:
            index (int): Index of the layer to show
        """
        if 0 <= index < len(self.layer_files):
            filepath = self.layer_files[index]
            filename = os.path.basename(filepath)
            
            details = f"Layer: {index + 1}/{len(self.layer_files)}\n"
            details += f"Filename: {filename}\n"
            details += f"Full path: {filepath}\n"
            details += f"Status: {'Completed' if index < self.current_layer_index else 'Current' if index == self.current_layer_index else 'Pending'}"
            
            QMessageBox.information(self, "Layer Details", details)
            
    def set_as_current_layer(self, index):
        """
        Set a layer as the current layer.
        
        Args:
            index (int): Index of the layer to set as current
        """
        if 0 <= index < len(self.layer_files):
            if index < self.current_layer_index:
                # Moving backward - confirm
                response = QMessageBox.question(
                    self, 
                    "Confirm Layer Change",
                    f"Are you sure you want to mark layer {index + 1} as the current layer?\n\n"
                    f"This will mean layers {index + 1} to {self.current_layer_index + 1} will need to be processed again.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if response != QMessageBox.Yes:
                    return
                    
            self.update_current_layer(index)
            self.layer_selected.emit(index, self.layer_files[index])
            self.logger.info(f"Set layer {index} as current layer")