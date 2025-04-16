from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, 
                             QFormLayout, QLabel, QDoubleSpinBox, QSpinBox, 
                             QComboBox, QCheckBox, QDialogButtonBox, QGroupBox,
                             QScrollArea, QMessageBox, QProgressDialog, QHBoxLayout)
from PyQt5.QtCore import Qt
import yaml
import os

class LaserParametersDialog(QDialog):
    def __init__(self, scancard, parent=None, layer_count=0):
        super().__init__(parent)
        
        # Dialog setup
        self.setWindowTitle("Laser Marking Parameters")
        self.setGeometry(100, 100, 700, 900)

        # Store the layer count from the layer queue manager
        self.layer_count = layer_count
        
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Tab Widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Marking Parameters Tab
        marking_tab = QWidget()
        marking_layout = QVBoxLayout(marking_tab)
        
        # Create a scroll area for marking parameters
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        marking_layout.addWidget(scroll_area)
        
        # Container widget for the scroll area
        marking_container = QWidget()
        scroll_area.setWidget(marking_container)
        marking_form = QFormLayout(marking_container)
        
        # Motion Parameters Group
        motion_group = QGroupBox("Motion Parameters")
        motion_form = QFormLayout(motion_group)
        
        # Marking Speed
        self.mark_speed_spinbox = QDoubleSpinBox()
        self.mark_speed_spinbox.setRange(0, 10000)
        self.mark_speed_spinbox.setSingleStep(100)
        self.mark_speed_spinbox.setValue(3000)
        self.mark_speed_spinbox.setSuffix(" mm/s")
        motion_form.addRow("Marking Speed:", self.mark_speed_spinbox)
        
        # Jump Speed
        self.jump_speed_spinbox = QDoubleSpinBox()
        self.jump_speed_spinbox.setRange(0, 10000)
        self.jump_speed_spinbox.setSingleStep(100)
        self.jump_speed_spinbox.setValue(5000)
        self.jump_speed_spinbox.setSuffix(" mm/s")
        motion_form.addRow("Jump Speed:", self.jump_speed_spinbox)
        
        marking_form.addRow(motion_group)
        
        # Timing Parameters Group
        timing_group = QGroupBox("Timing Parameters")
        timing_form = QFormLayout(timing_group)
        
        # Jump Delay
        self.jump_delay_spinbox = QSpinBox()
        self.jump_delay_spinbox.setRange(0, 10000)
        self.jump_delay_spinbox.setSingleStep(10)
        self.jump_delay_spinbox.setValue(100)
        self.jump_delay_spinbox.setSuffix(" μs")
        timing_form.addRow("Jump Delay:", self.jump_delay_spinbox)
        
        # Laser On Delay
        self.laser_on_delay_spinbox = QSpinBox()
        self.laser_on_delay_spinbox.setRange(0, 10000)
        self.laser_on_delay_spinbox.setSingleStep(10)
        self.laser_on_delay_spinbox.setValue(100)
        self.laser_on_delay_spinbox.setSuffix(" μs")
        timing_form.addRow("Laser On Delay:", self.laser_on_delay_spinbox)
        
        # Polygon Delay
        self.polygon_delay_spinbox = QSpinBox()
        self.polygon_delay_spinbox.setRange(0, 10000)
        self.polygon_delay_spinbox.setSingleStep(10)
        self.polygon_delay_spinbox.setValue(100)
        self.polygon_delay_spinbox.setSuffix(" μs")
        timing_form.addRow("Polygon Delay:", self.polygon_delay_spinbox)
        
        # Laser Off Delay
        self.laser_off_delay_spinbox = QSpinBox()
        self.laser_off_delay_spinbox.setRange(0, 10000)
        self.laser_off_delay_spinbox.setSingleStep(10)
        self.laser_off_delay_spinbox.setValue(100)
        self.laser_off_delay_spinbox.setSuffix(" μs")
        timing_form.addRow("Laser Off Delay:", self.laser_off_delay_spinbox)
        
        # Polygon Killer Time
        self.polygon_killer_time_spinbox = QSpinBox()
        self.polygon_killer_time_spinbox.setRange(0, 10000)
        self.polygon_killer_time_spinbox.setSingleStep(10)
        self.polygon_killer_time_spinbox.setValue(100)
        self.polygon_killer_time_spinbox.setSuffix(" μs")
        timing_form.addRow("Polygon Killer Time:", self.polygon_killer_time_spinbox)
        
        marking_form.addRow(timing_group)
        
        # Laser Parameters Group
        laser_group = QGroupBox("Laser Parameters")
        laser_form = QFormLayout(laser_group)
        
        # Laser Frequency
        self.laser_frequency_spinbox = QSpinBox()
        self.laser_frequency_spinbox.setRange(0, 1000)
        self.laser_frequency_spinbox.setSingleStep(1)
        self.laser_frequency_spinbox.setValue(100)
        self.laser_frequency_spinbox.setSuffix(" kHz")
        laser_form.addRow("Laser Frequency:", self.laser_frequency_spinbox)
        
        # Current (YAG/SPI)
        self.current_spinbox = QSpinBox()
        self.current_spinbox.setRange(0, 1000)
        self.current_spinbox.setSingleStep(1)
        self.current_spinbox.setValue(100)
        self.current_spinbox.setSuffix(" A")
        laser_form.addRow("Current:", self.current_spinbox)
        
        # First Pulse Killer Length
        self.first_pulse_killer_length_spinbox = QSpinBox()
        self.first_pulse_killer_length_spinbox.setRange(0, 1000)
        self.first_pulse_killer_length_spinbox.setSingleStep(1)
        self.first_pulse_killer_length_spinbox.setValue(100)
        self.first_pulse_killer_length_spinbox.setSuffix(" μs")
        laser_form.addRow("First Pulse Killer Length:", self.first_pulse_killer_length_spinbox)
        
        # Pulse Width
        self.pulse_width_spinbox = QSpinBox()
        self.pulse_width_spinbox.setRange(0, 1000)
        self.pulse_width_spinbox.setSingleStep(1)
        self.pulse_width_spinbox.setValue(100)
        self.pulse_width_spinbox.setSuffix(" μs")
        laser_form.addRow("Pulse Width:", self.pulse_width_spinbox)
        
        # First Pulse Width
        self.first_pulse_width_spinbox = QSpinBox()
        self.first_pulse_width_spinbox.setRange(0, 100)
        self.first_pulse_width_spinbox.setSingleStep(1)
        self.first_pulse_width_spinbox.setValue(100)
        self.first_pulse_width_spinbox.setSuffix(" %")
        laser_form.addRow("First Pulse Width:", self.first_pulse_width_spinbox)
        
        # Increment Step
        self.increment_step_spinbox = QSpinBox()
        self.increment_step_spinbox.setRange(0, 100)
        self.increment_step_spinbox.setSingleStep(1)
        self.increment_step_spinbox.setValue(100)
        self.increment_step_spinbox.setSuffix(" %")
        laser_form.addRow("Increment Step:", self.increment_step_spinbox)
        
        marking_form.addRow(laser_group)
        
        self.tab_widget.addTab(marking_tab, "Marking Parameters")
        
        # Fill Parameters Tab
        fill_tab = QWidget()
        fill_layout = QVBoxLayout(fill_tab)
        
        # Create a scroll area for fill parameters
        fill_scroll_area = QScrollArea()
        fill_scroll_area.setWidgetResizable(True)
        fill_layout.addWidget(fill_scroll_area)
        
        # Container widget for the scroll area
        fill_container = QWidget()
        fill_scroll_area.setWidget(fill_container)
        fill_form = QFormLayout(fill_container)
        
        # Fill Parameters Group
        fill_group = QGroupBox("Entity Fill Properties")
        fill_param_form = QFormLayout(fill_group)
        
        # Fill Mode Combo Box
        self.fill_mode_combobox = QComboBox()
        self.fill_mode_combobox.addItems([
            "No Filling", 
            "One-way Filling", 
            "Two-way Filling", 
            "Bow-shaped Filling", 
            "Back-shaped Filling"
        ])
        fill_param_form.addRow("Fill Mode:", self.fill_mode_combobox)
        
        # Fill Parameters Checkboxes
        self.equal_distance_checkbox = QCheckBox()
        fill_param_form.addRow("Evenly Distribute Fill Lines:", self.equal_distance_checkbox)
        
        self.second_fill_checkbox = QCheckBox()
        fill_param_form.addRow("Enable Second Padding:", self.second_fill_checkbox)
        
        self.rotate_angle_checkbox = QCheckBox()
        fill_param_form.addRow("Automatic Rotation Angle:", self.rotate_angle_checkbox)
        
        self.fill_as_one_checkbox = QCheckBox()
        fill_param_form.addRow("Calculate Objects as a Whole:", self.fill_as_one_checkbox)
        
        self.more_intact_checkbox = QCheckBox()
        fill_param_form.addRow("Optimize Two-way Filling:", self.more_intact_checkbox)
        
        self.fill_3d_checkbox = QCheckBox()
        fill_param_form.addRow("Use Triangle Fill Mode:", self.fill_3d_checkbox)
        
        # Fill Parameters SpinBoxes
        self.loop_num_spinbox = QSpinBox()
        self.loop_num_spinbox.setRange(0, 100)
        self.loop_num_spinbox.setValue(1)
        fill_param_form.addRow("Number of Boundary Rings:", self.loop_num_spinbox)
        
        self.fill_mark_times_spinbox = QSpinBox()
        self.fill_mark_times_spinbox.setRange(1, 100)
        self.fill_mark_times_spinbox.setValue(1)
        fill_param_form.addRow("Number of Markings for Current Angle:", self.fill_mark_times_spinbox)
        
        self.cur_mark_times_spinbox = QSpinBox()
        self.cur_mark_times_spinbox.setRange(1, 100)
        self.cur_mark_times_spinbox.setValue(12)
        fill_param_form.addRow("Current Number of Markings:", self.cur_mark_times_spinbox)
        
        self.layer_id_spinbox = QSpinBox()
        self.layer_id_spinbox.setRange(0, 255)
        self.layer_id_spinbox.setValue(1)
        fill_param_form.addRow("Fill in Pen Number:", self.layer_id_spinbox)
        
        self.fill_space_spinbox = QDoubleSpinBox()
        self.fill_space_spinbox.setRange(0.01, 1000)
        self.fill_space_spinbox.setValue(100)
        fill_param_form.addRow("Fill Line Space:", self.fill_space_spinbox)
        
        self.fill_angle_spinbox = QDoubleSpinBox()
        self.fill_angle_spinbox.setRange(0, 360)
        self.fill_angle_spinbox.setValue(100)
        fill_param_form.addRow("Fill Angle:", self.fill_angle_spinbox)
        
        self.fill_edge_offset_spinbox = QDoubleSpinBox()
        self.fill_edge_offset_spinbox.setRange(0, 1000)
        self.fill_edge_offset_spinbox.setValue(100)
        fill_param_form.addRow("Fill Edge Offset:", self.fill_edge_offset_spinbox)
        
        self.fill_start_offset_spinbox = QDoubleSpinBox()
        self.fill_start_offset_spinbox.setRange(0, 1000)
        self.fill_start_offset_spinbox.setValue(100)
        fill_param_form.addRow("Fill Start Offset:", self.fill_start_offset_spinbox)
        
        self.fill_end_offset_spinbox = QDoubleSpinBox()
        self.fill_end_offset_spinbox.setRange(0, 1000)
        self.fill_end_offset_spinbox.setValue(100)
        fill_param_form.addRow("Fill End Offset:", self.fill_end_offset_spinbox)
        
        self.fill_line_reduction_spinbox = QDoubleSpinBox()
        self.fill_line_reduction_spinbox.setRange(0, 1000)
        self.fill_line_reduction_spinbox.setValue(100)
        fill_param_form.addRow("Fill Line Reduction:", self.fill_line_reduction_spinbox)
        
        self.loop_space_spinbox = QDoubleSpinBox()
        self.loop_space_spinbox.setRange(0, 1000)
        self.loop_space_spinbox.setValue(100)
        fill_param_form.addRow("Loop Space:", self.loop_space_spinbox)
        
        self.second_angle_spinbox = QDoubleSpinBox()
        self.second_angle_spinbox.setRange(0, 360)
        self.second_angle_spinbox.setValue(100)
        fill_param_form.addRow("Second Fill Angle:", self.second_angle_spinbox)
        
        self.rotate_angle_spinbox = QDoubleSpinBox()
        self.rotate_angle_spinbox.setRange(0, 360)
        self.rotate_angle_spinbox.setValue(100)
        fill_param_form.addRow("Angle of Each Increment:", self.rotate_angle_spinbox)
        
        fill_form.addRow(fill_group)
        
        self.tab_widget.addTab(fill_tab, "Fill Parameters")
        
        # Add "Apply to All Layers" option
        apply_options_layout = QHBoxLayout()
        self.apply_all_layers_checkbox = QCheckBox("Apply to All Layers")
        self.apply_all_layers_checkbox.setChecked(True)  # Default to checked
        apply_options_layout.addWidget(self.apply_all_layers_checkbox)
        
        # Add max layer input
        self.max_layer_label = QLabel("Maximum Layer:")
        self.max_layer_spinbox = QSpinBox()
        self.max_layer_spinbox.setRange(1, 255)

        # Use the provided layer count or default to 10
        self.max_layer_spinbox.setValue(self.layer_count if self.layer_count > 0 else 10)

        apply_options_layout.addWidget(self.max_layer_label)
        apply_options_layout.addWidget(self.max_layer_spinbox)
        
        # Add the options layout
        main_layout.addLayout(apply_options_layout)
        
        # Dialog Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save_parameters)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        # Initialize scancard and load parameters
        self.scancard = scancard
        self.load_parameters()
    
    def load_parameters(self):
        """Load parameters from scancard and update UI."""
        try:
            # Get the marking parameters for layer 1
            future = self.scancard.get_markParameters_by_layer(1)
            response = future.result()
            
            if response and response.get("ret_value") == 1:
                data = response.get("response", {}).get("data", {})
                
                # Update UI with marking parameters
                self.mark_speed_spinbox.setValue(data.get("markSpeed", 3000))
                self.jump_speed_spinbox.setValue(data.get("jumpSpeed", 5000))
                self.jump_delay_spinbox.setValue(data.get("jumpDelay", 100))
                self.laser_on_delay_spinbox.setValue(data.get("laserOnDelay", 100))
                self.polygon_delay_spinbox.setValue(data.get("polygonDelay", 100))
                self.laser_off_delay_spinbox.setValue(data.get("laserOffDelay", 100))
                self.polygon_killer_time_spinbox.setValue(data.get("polygonKillerTime", 100))
                self.laser_frequency_spinbox.setValue(data.get("laserFrequency", 100))
                self.current_spinbox.setValue(data.get("current", 100))
                self.first_pulse_killer_length_spinbox.setValue(data.get("firstPulseKillerLength", 100))
                self.pulse_width_spinbox.setValue(data.get("pulseWidth", 100))
                self.first_pulse_width_spinbox.setValue(data.get("firstPulseWidth", 100))
                self.increment_step_spinbox.setValue(data.get("incrementStep", 100))
            
            # Get the fill parameters for index 1
            future = self.scancard.get_entity_fill_property_by_index(1, 1)
            response = future.result()
            
            if response and response.get("ret_value") == 1:
                data = response.get("response", {}).get("data", {})
                
                # Update UI with fill parameters
                self.fill_mode_combobox.setCurrentIndex(data.get("fill_mode", 0))
                self.equal_distance_checkbox.setChecked(data.get("bEqualDistance", False))
                self.second_fill_checkbox.setChecked(data.get("bSecondFill", False))
                self.rotate_angle_checkbox.setChecked(data.get("bRotateAngle", False))
                self.fill_as_one_checkbox.setChecked(data.get("bFillAsOne", False))
                self.more_intact_checkbox.setChecked(data.get("bMoreIntact", False))
                self.fill_3d_checkbox.setChecked(data.get("bFill3D", False))
                self.loop_num_spinbox.setValue(data.get("loopNum", 1))
                self.fill_mark_times_spinbox.setValue(data.get("iFillMarkTimes", 1))
                self.cur_mark_times_spinbox.setValue(data.get("iCurMarkTimes", 12))
                self.layer_id_spinbox.setValue(data.get("layerId", 1))
                self.fill_space_spinbox.setValue(data.get("fillSpace", 100))
                self.fill_angle_spinbox.setValue(data.get("fillAngle", 100))
                self.fill_edge_offset_spinbox.setValue(data.get("fillEdgeOffset", 100))
                self.fill_start_offset_spinbox.setValue(data.get("fillStartOffset", 100))
                self.fill_end_offset_spinbox.setValue(data.get("fillEndOffset", 100))
                self.fill_line_reduction_spinbox.setValue(data.get("fillLineReduction", 100))
                self.loop_space_spinbox.setValue(data.get("loopSpace", 100))
                self.second_angle_spinbox.setValue(data.get("secondAngle", 100))
                self.rotate_angle_spinbox.setValue(data.get("dRotateAngle", 100))
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Parameter Load Error",
                f"Failed to load parameters from Scancard: {str(e)}"
            )
            self.reset_to_defaults()
    
    def reset_to_defaults(self):
        """Set default parameter values."""
        # Set default marking parameters
        self.mark_speed_spinbox.setValue(3000)
        self.jump_speed_spinbox.setValue(5000)
        self.jump_delay_spinbox.setValue(100)
        self.laser_on_delay_spinbox.setValue(100)
        self.polygon_delay_spinbox.setValue(100)
        self.laser_off_delay_spinbox.setValue(100)
        self.polygon_killer_time_spinbox.setValue(100)
        self.laser_frequency_spinbox.setValue(100)
        self.current_spinbox.setValue(100)
        self.first_pulse_killer_length_spinbox.setValue(100)
        self.pulse_width_spinbox.setValue(100)
        self.first_pulse_width_spinbox.setValue(100)
        self.increment_step_spinbox.setValue(100)
        
        # Set default fill parameters
        self.fill_mode_combobox.setCurrentIndex(0)
        self.equal_distance_checkbox.setChecked(False)
        self.second_fill_checkbox.setChecked(False)
        self.rotate_angle_checkbox.setChecked(False)
        self.fill_as_one_checkbox.setChecked(False)
        self.more_intact_checkbox.setChecked(False)
        self.fill_3d_checkbox.setChecked(False)
        self.loop_num_spinbox.setValue(1)
        self.fill_mark_times_spinbox.setValue(1)
        self.cur_mark_times_spinbox.setValue(12)
        self.layer_id_spinbox.setValue(1)
        self.fill_space_spinbox.setValue(100)
        self.fill_angle_spinbox.setValue(100)
        self.fill_edge_offset_spinbox.setValue(100)
        self.fill_start_offset_spinbox.setValue(100)
        self.fill_end_offset_spinbox.setValue(100)
        self.fill_line_reduction_spinbox.setValue(100)
        self.loop_space_spinbox.setValue(100)
        self.second_angle_spinbox.setValue(100)
        self.rotate_angle_spinbox.setValue(100)
    
    def save_parameters(self):
        """Save parameters to scancard with improved error handling and cancellation support."""
        # Collect marking parameters
        marking_params = {
            "markSpeed": self.mark_speed_spinbox.value(),
            "jumpSpeed": self.jump_speed_spinbox.value(),
            "jumpDelay": self.jump_delay_spinbox.value(),
            "laserOnDelay": self.laser_on_delay_spinbox.value(),
            "polygonDelay": self.polygon_delay_spinbox.value(),
            "laserOffDelay": self.laser_off_delay_spinbox.value(),
            "polygonKillerTime": self.polygon_killer_time_spinbox.value(),
            "laserFrequency": self.laser_frequency_spinbox.value(),
            "current": self.current_spinbox.value(),
            "firstPulseKillerLength": self.first_pulse_killer_length_spinbox.value(),
            "pulseWidth": self.pulse_width_spinbox.value(),
            "firstPulseWidth": self.first_pulse_width_spinbox.value(),
            "incrementStep": self.increment_step_spinbox.value()
        }
        
        # Collect fill parameters
        fill_params = {
            "fill_mode": self.fill_mode_combobox.currentIndex(),
            "bEqualDistance": self.equal_distance_checkbox.isChecked(),
            "bSecondFill": self.second_fill_checkbox.isChecked(),
            "bRotateAngle": self.rotate_angle_checkbox.isChecked(),
            "bFillAsOne": self.fill_as_one_checkbox.isChecked(),
            "bMoreIntact": self.more_intact_checkbox.isChecked(),
            "bFill3D": self.fill_3d_checkbox.isChecked(),
            "loopNum": self.loop_num_spinbox.value(),
            "iFillMarkTimes": self.fill_mark_times_spinbox.value(),
            "iCurMarkTimes": self.cur_mark_times_spinbox.value(),
            "layerId": self.layer_id_spinbox.value(),
            "fillSpace": self.fill_space_spinbox.value(),
            "fillAngle": self.fill_angle_spinbox.value(),
            "fillEdgeOffset": self.fill_edge_offset_spinbox.value(),
            "fillStartOffset": self.fill_start_offset_spinbox.value(),
            "fillEndOffset": self.fill_end_offset_spinbox.value(),
            "fillLineReduction": self.fill_line_reduction_spinbox.value(),
            "loopSpace": self.loop_space_spinbox.value(),
            "secondAngle": self.second_angle_spinbox.value(),
            "dRotateAngle": self.rotate_angle_spinbox.value()
        }
        
        try:
            # Check if we should apply to all layers
            apply_all = self.apply_all_layers_checkbox.isChecked()
            max_layer = self.max_layer_spinbox.value() if apply_all else 1
            
            if apply_all:
                # Create progress dialog
                progress = QProgressDialog("Validating layers...", "Cancel", 0, max_layer, self)
                progress.setWindowModality(Qt.WindowModal)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                progress.show()
                
                # First validate all layers and entities exist
                valid_layers = []
                invalid_layers = []
                
                for layer in range(1, max_layer + 1):
                    if progress.wasCanceled():
                        if valid_layers:
                            # Ask user if they want to proceed with validated layers only
                            reply = QMessageBox.question(
                                self, 
                                "Validation Canceled", 
                                f"Continue with {len(valid_layers)} validated layers only?",
                                QMessageBox.Yes | QMessageBox.No, 
                                QMessageBox.No
                            )
                            if reply != QMessageBox.Yes:
                                progress.close()
                                return
                        else:
                            progress.close()
                            return
                    
                    progress.setValue(layer)
                    progress.setLabelText(f"Validating layer {layer} of {max_layer}...")
                    
                    # Validate layer and entity
                    future = self.scancard.validate_layer_entity(layer)
                    result = future.result()
                    
                    if result.get("valid", False):
                        valid_layers.append(layer)
                    else:
                        invalid_layers.append((layer, result.get("message", "Unknown error")))
                
                # Report validation results
                if invalid_layers:
                    message = "The following layers could not be validated:\n\n"
                    message += "\n".join([f"Layer {layer}: {msg}" for layer, msg in invalid_layers])
                    message += "\n\nDo you want to continue with valid layers only?"
                    
                    reply = QMessageBox.question(
                        self, 
                        "Validation Results", 
                        message,
                        QMessageBox.Yes | QMessageBox.No, 
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        progress.close()
                        return
                
                # Proceed with valid layers only
                if not valid_layers:
                    QMessageBox.critical(
                        self,
                        "Validation Error",
                        "No valid layers found to apply parameters to."
                    )
                    progress.close()
                    return
                
                # Reset progress for applying parameters
                progress.setLabelText("Applying parameters...")
                progress.setRange(0, len(valid_layers))
                progress.setValue(0)
                
                # Track failures
                failures = []
                successful_layers = []
                
                # Apply to valid layers
                for i, layer in enumerate(valid_layers):
                    if progress.wasCanceled():
                        if successful_layers:
                            reply = QMessageBox.question(
                                self, 
                                "Operation Canceled", 
                                f"Parameters were applied to {len(successful_layers)} layers.\n\n"
                                "Do you want to download these changes to the device?",
                                QMessageBox.Yes | QMessageBox.No, 
                                QMessageBox.Yes
                            )
                            if reply == QMessageBox.Yes:
                                break  # Continue to download step
                            else:
                                progress.close()
                                return  # Cancel without downloading
                        else:
                            progress.close()
                            return
                    
                    progress.setValue(i)
                    progress.setLabelText(f"Applying parameters to layer {layer}...")
                    
                    # Update marking parameters for the current layer
                    future = self.scancard.set_markParameters_by_layer(layer, marking_params)
                    response = future.result()
                    
                    if not response or response.get("ret_value") != 1:
                        failures.append(f"Layer {layer} marking parameters")
                        continue
                    
                    # Update fill parameters for the current entity in the current layer
                    future = self.scancard.set_entity_fill_property_by_index(layer, 1, fill_params)
                    response = future.result()
                    
                    if not response or response.get("ret_value") != 1:
                        failures.append(f"Layer {layer} fill parameters")
                        continue
                    
                    successful_layers.append(layer)
                
                # Download parameters to apply changes
                progress.setLabelText("Downloading parameters to device...")
                progress.setValue(len(valid_layers))
                
                future = self.scancard.download_parameters()
                response = future.result()
                
                if not response or response.get("ret_value") != 1:
                    failures.append("Downloading parameters")
                
                progress.setValue(len(valid_layers))
                progress.close()
                
                # Report results
                if failures:
                    QMessageBox.warning(
                        self,
                        "Parameter Update Warning",
                        f"Parameters were applied to {len(successful_layers)} out of {len(valid_layers)} layers, but with some failures:\n" + 
                        "\n".join(failures)
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Parameters applied to {len(successful_layers)} layers successfully"
                    )
            else:
                # Apply only to layer 1 (original behavior)
                # Validate layer 1 first
                future = self.scancard.validate_layer_entity(1)
                result = future.result()
                
                if not result.get("valid", False):
                    QMessageBox.critical(
                        self,
                        "Validation Error",
                        f"Cannot apply parameters to layer 1: {result.get('message', 'Unknown error')}"
                    )
                    return
                
                future = self.scancard.set_markParameters_by_layer(1, marking_params)
                response = future.result()
                
                if not response or response.get("ret_value") != 1:
                    raise Exception("Failed to set marking parameters")
                
                future = self.scancard.set_entity_fill_property_by_index(1, 1, fill_params)
                response = future.result()
                
                if not response or response.get("ret_value") != 1:
                    raise Exception("Failed to set fill parameters")
                
                future = self.scancard.download_parameters()
                response = future.result()
                
                if not response or response.get("ret_value") != 1:
                    raise Exception("Failed to download parameters")
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Parameters saved to layer 1 successfully"
                )
            
            # Save to YAML for future reference
            self.save_to_yaml(marking_params, fill_params)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Parameter Update Error",
                f"Failed to update parameters: {str(e)}"
            )
    
    def save_to_yaml(self, marking_params, fill_params):
        """Save parameters to YAML file for future reference."""
        try:
            # Combine all parameters
            all_params = {
                "marking_parameters": marking_params,
                "fill_parameters": fill_params,
                "apply_to_all_layers": self.apply_all_layers_checkbox.isChecked(),
                "max_layer": self.max_layer_spinbox.value()
            }
            
            # Save to YAML
            with open('laser_parameters.yaml', 'w') as file:
                yaml.dump(all_params, file)
        except Exception as e:
            QMessageBox.warning(
                self,
                "YAML Save Error",
                f"Failed to save parameters to YAML: {str(e)}"
            )