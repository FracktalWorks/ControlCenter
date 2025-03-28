#!/bin/bash

# Ensure the directory exists
mkdir -p src/ui/laser_parameters

# Create __init__.py (empty file)
touch src/ui/laser_parameters/__init__.py

# Create laser_parameters_dialog.py
cat > src/ui/laser_parameters/laser_parameters_dialog.py << 'EOF'
from PyQt5 import uic, QtWidgets
import os
import yaml

class LaserParametersDialog(QtWidgets.QDialog):
    def __init__(self, scancard, parent=None):
        super().__init__(parent)
        
        # Load UI file
        ui_path = os.path.join(os.path.dirname(__file__), 'laser_parameters_dialog.ui')
        uic.loadUi(ui_path, self)
        
        self.scancard = scancard
        
        # Connect buttons
        self.buttonBox.accepted.connect(self.save_parameters)
        self.buttonBox.rejected.connect(self.reject)
        
        # Load existing parameters
        self.load_parameters()
    
    def load_parameters(self):
        """Load parameters from YAML or set defaults."""
        try:
            with open('laser_parameters.yaml', 'r') as file:
                params = yaml.safe_load(file)
            
            # Load Marking Parameters
            self.markSpeedSpinBox.setValue(float(params.get('mark_speed', 3000)))
            # Add more parameter loading here
        
        except FileNotFoundError:
            self.reset_to_defaults()
    
    def reset_to_defaults(self):
        """Set default parameter values."""
        self.markSpeedSpinBox.setValue(3000)
        # Add more default parameter settings here
    
    def save_parameters(self):
        """Save parameters to YAML and update Scancard."""
        # Collect marking parameters
        marking_params = {
            'mark_speed': self.markSpeedSpinBox.value(),
            # Add more parameter collection here
        }
        
        # Save to YAML
        with open('laser_parameters.yaml', 'w') as file:
            yaml.dump(marking_params, file)
        
        # Update Scancard parameters
        self.update_scancard_parameters(marking_params)
        
        self.accept()
    
    def update_scancard_parameters(self, marking_params):
        """Update Scancard with marking parameters."""
        try:
            # Update marking parameters
            self.scancard.set_markParameters_by_layer(0, {
                'markSpeed': marking_params['mark_speed'],
                # Add more parameter updates here
            })
        
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, 
                "Parameter Update Error", 
                f"Failed to update Scancard parameters: {str(e)}"
            )
EOF

# Create laser_parameters_dialog.ui
cat > src/ui/laser_parameters/laser_parameters_dialog.ui << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>LaserParametersDialog</class>
 <widget class="QDialog" name="LaserParametersDialog">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>700</width>
    <height>900</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Laser Marking Parameters</string>
  </property>
  <layout class="QVBoxLayout" name="verticalLayout">
   <item>
    <widget class="QTabWidget" name="parameterTabWidget">
     <widget class="QWidget" name="markingParametersTab">
      <attribute name="title">
       <string>Marking Parameters</string>
      </attribute>
      <layout class="QVBoxLayout" name="verticalLayout_2">
       <item>
        <widget class="QGroupBox" name="markingParametersGroup">
         <property name="title">
          <string>Marking Parameters</string>
         </property>
         <layout class="QFormLayout" name="formLayout">
          <item row="0" column="0">
           <widget class="QLabel" name="markSpeedLabel">
            <property name="text">
             <string>Marking Speed (mm/s):</string>
            </property>
           </widget>
          </item>
          <item row="0" column="1">
           <widget class="QDoubleSpinBox" name="markSpeedSpinBox">
            <property name="maximum">
             <double>10000.000000000000000</double>
            </property>
           </widget>
          </item>
         </layout>
        </widget>
       </item>
      </layout>
     </widget>
     <widget class="QWidget" name="fillParametersTab">
      <attribute name="title">
       <string>Fill Parameters</string>
      </attribute>
      <layout class="QVBoxLayout" name="verticalLayout_3">
       <item>
        <widget class="QGroupBox" name="fillParametersGroup">
         <property name="title">
          <string>Entity Fill Properties</string>
         </property>
         <layout class="QFormLayout" name="fillParameterLayout">
          <item row="0" column="0">
           <widget class="QLabel" name="fillModeLabel">
            <property name="text">
             <string>Fill Mode:</string>
            </property>
           </widget>
          </item>
          <item row="0" column="1">
           <widget class="QComboBox" name="fillModeComboBox">
            <item>
             <property name="text">
              <string>No Filling</string>
             </property>
            </item>
            <item>
             <property name="text">
              <string>One-way Filling</string>
             </property>
            </item>
            <item>
             <property name="text">
              <string>Two-way Filling</string>
             </property>
            </item>
            <item>
             <property name="text">
              <string>Bow-shaped Filling</string>
             </property>
            </item>
            <item>
             <property name="text">
              <string>Back-shaped Filling</string>
             </property>
            </item>
           </widget>
          </item>
         </layout>
        </widget>
       </item>
      </layout>
     </widget>
    </widget>
   </item>
   <item>
    <widget class="QDialogButtonBox" name="buttonBox">
     <property name="orientation">
      <enum>Qt::Horizontal</enum>
     </property>
     <property name="standardButtons">
      <set>QDialogButtonBox::Cancel|QDialogButtonBox::Save</set>
     </property>
    </widget>
   </item>
  </layout>
 </widget>
 <resources/>
 <connections/>
</ui>
EOF

echo "Files created successfully in src/ui/laser_parameters/"