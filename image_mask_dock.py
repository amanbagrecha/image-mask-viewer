import os
import csv
import pandas as pd
from datetime import datetime
from pathlib import Path
from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.core import (QgsRasterLayer, QgsProject, Qgis, QgsMultiBandColorRenderer, 
                      QgsLayerTreeLayer, QgsSingleBandPseudoColorRenderer, 
                      QgsColorRampShader, QgsRasterShader, QgsGradientColorRamp)
from qgis.PyQt.QtWidgets import (QDockWidget, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QLineEdit, QPushButton, 
                                 QGroupBox, QMessageBox, QWidget,
                                 QProgressBar, QSpacerItem, QSizePolicy,
                                 QCheckBox, QRadioButton, QButtonGroup,
                                 QSpinBox)


class ImageMaskDock(QDockWidget):
    
    def __init__(self, iface, parent=None):
        super(ImageMaskDock, self).__init__("Image Mask Reviewer", parent)
        self.iface = iface
        self.image_dir = ""
        self.mask_dir = ""
        self.mask_veg_dir = ""
        self.output_dir = ""
        self.mask_suffix = "_rf_classified"
        self.mask_veg_suffix = "_vegmask_ndvi"
        self.all_pairs = []
        self.filtered_pairs = []
        self.current_index = 0
        self.csv_path = ""
        self.current_triplet_layers = []  # Track current triplet layers
        
        self.setupUi()
        self.connectSignals()
        
    def setupUi(self):
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # Directory selection
        dir_group = QGroupBox("Setup")
        dir_layout = QVBoxLayout()
        
        # Image directory
        image_layout = QHBoxLayout()
        image_layout.addWidget(QLabel("Images:"))
        self.image_dir_edit = QLineEdit()
        image_layout.addWidget(self.image_dir_edit)
        self.browse_image_btn = QPushButton("...")
        self.browse_image_btn.setMaximumWidth(30)
        image_layout.addWidget(self.browse_image_btn)
        dir_layout.addLayout(image_layout)
        
        # Mask directory
        mask_layout = QHBoxLayout()
        mask_layout.addWidget(QLabel("Masks:"))
        self.mask_dir_edit = QLineEdit()
        mask_layout.addWidget(self.mask_dir_edit)
        self.browse_mask_btn = QPushButton("...")
        self.browse_mask_btn.setMaximumWidth(30)
        mask_layout.addWidget(self.browse_mask_btn)
        dir_layout.addLayout(mask_layout)
        
        # Mask Veg directory
        mask_veg_layout = QHBoxLayout()
        mask_veg_layout.addWidget(QLabel("Mask Veg:"))
        self.mask_veg_dir_edit = QLineEdit()
        mask_veg_layout.addWidget(self.mask_veg_dir_edit)
        self.browse_mask_veg_btn = QPushButton("...")
        self.browse_mask_veg_btn.setMaximumWidth(30)
        mask_veg_layout.addWidget(self.browse_mask_veg_btn)
        dir_layout.addLayout(mask_veg_layout)
        
        # Output directory
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output:"))
        self.output_dir_edit = QLineEdit()
        output_layout.addWidget(self.output_dir_edit)
        self.browse_output_btn = QPushButton("...")
        self.browse_output_btn.setMaximumWidth(30)
        output_layout.addWidget(self.browse_output_btn)
        dir_layout.addLayout(output_layout)
        
        # Suffixes
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("Mask Suffix:"))
        self.suffix_edit = QLineEdit(self.mask_suffix)
        suffix_layout.addWidget(self.suffix_edit)
        suffix_layout.addWidget(QLabel("Veg Suffix:"))
        self.veg_suffix_edit = QLineEdit(self.mask_veg_suffix)
        suffix_layout.addWidget(self.veg_suffix_edit)
        dir_layout.addLayout(suffix_layout)
        
        self.load_btn = QPushButton("Load Triplets")
        self.load_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; }")
        dir_layout.addWidget(self.load_btn)
        
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        # Filter options
        filter_group = QGroupBox("Filter Options")
        filter_layout = QVBoxLayout()
        
        self.show_reviewed_cb = QCheckBox("Show Reviewed")
        self.show_reviewed_cb.setEnabled(False)
        filter_layout.addWidget(self.show_reviewed_cb)
        
        # Go to index
        goto_layout = QHBoxLayout()
        goto_layout.addWidget(QLabel("Go to Index:"))
        self.goto_spinbox = QSpinBox()
        self.goto_spinbox.setMinimum(1)
        self.goto_spinbox.setMaximum(1)
        self.goto_spinbox.setEnabled(False)
        goto_layout.addWidget(self.goto_spinbox)
        
        self.goto_btn = QPushButton("Go")
        self.goto_btn.setEnabled(False)
        self.goto_btn.setMaximumWidth(40)
        goto_layout.addWidget(self.goto_btn)
        filter_layout.addLayout(goto_layout)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Review section
        review_group = QGroupBox("Review")
        review_layout = QVBoxLayout()
        
        # Progress
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("0 / 0")
        progress_layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        review_layout.addLayout(progress_layout)
        
        # Current file with status
        self.current_file_label = QLabel("No file loaded")
        self.current_file_label.setWordWrap(True)
        review_layout.addWidget(self.current_file_label)
        
        self.status_indicator = QLabel("")
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.status_indicator.setStyleSheet("QLabel { padding: 5px; border-radius: 3px; }")
        review_layout.addWidget(self.status_indicator)
        
        # Mask type selection
        mask_type_group = QGroupBox("Save Decision For:")
        mask_type_layout = QHBoxLayout()
        
        self.mask_type_group = QButtonGroup()
        self.mask_radio = QRadioButton("Mask")
        self.mask_veg_radio = QRadioButton("Mask Veg")
        self.mask_veg_radio.setChecked(True)  # Default to mask_veg
        
        self.mask_type_group.addButton(self.mask_radio, 0)
        self.mask_type_group.addButton(self.mask_veg_radio, 1)
        
        mask_type_layout.addWidget(self.mask_radio)
        mask_type_layout.addWidget(self.mask_veg_radio)
        mask_type_group.setLayout(mask_type_layout)
        review_layout.addWidget(mask_type_group)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Next →")
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)
        review_layout.addLayout(nav_layout)
        
        # Review buttons
        review_btn_layout = QHBoxLayout()
        self.correct_btn = QPushButton("✓ Correct")
        self.correct_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; }")
        self.correct_btn.setEnabled(False)
        review_btn_layout.addWidget(self.correct_btn)
        
        self.incorrect_btn = QPushButton("✗ Incorrect")
        self.incorrect_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 10px; }")
        self.incorrect_btn.setEnabled(False)
        review_btn_layout.addWidget(self.incorrect_btn)
        
        self.unreview_btn = QPushButton("↶ Reset")
        self.unreview_btn.setStyleSheet("QPushButton { background-color: #ff9800; color: white; padding: 10px; }")
        self.unreview_btn.setEnabled(False)
        review_btn_layout.addWidget(self.unreview_btn)
        review_layout.addLayout(review_btn_layout)
        
        review_group.setLayout(review_layout)
        layout.addWidget(review_group)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: #666; padding: 5px; }")
        layout.addWidget(self.status_label)
        
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        main_widget.setLayout(layout)
        self.setWidget(main_widget)
        
    def connectSignals(self):
        self.browse_image_btn.clicked.connect(self.browse_image_directory)
        self.browse_mask_btn.clicked.connect(self.browse_mask_directory)
        self.browse_mask_veg_btn.clicked.connect(self.browse_mask_veg_directory)
        self.browse_output_btn.clicked.connect(self.browse_output_directory)
        self.load_btn.clicked.connect(self.load_pairs)
        self.show_reviewed_cb.toggled.connect(self.filter_pairs)
        self.goto_btn.clicked.connect(self.goto_index)
        self.prev_btn.clicked.connect(self.previous_pair)
        self.next_btn.clicked.connect(self.next_pair)
        self.correct_btn.clicked.connect(lambda: self.review_current('correct'))
        self.incorrect_btn.clicked.connect(lambda: self.review_current('incorrect'))
        self.unreview_btn.clicked.connect(lambda: self.review_current('not_reviewed'))
        
    def browse_image_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Image Directory", self.image_dir_edit.text())
        if directory:
            self.image_dir_edit.setText(directory)
            
    def browse_mask_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Mask Directory", self.mask_dir_edit.text())
        if directory:
            self.mask_dir_edit.setText(directory)
            
    def browse_mask_veg_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Mask Veg Directory", self.mask_veg_dir_edit.text())
        if directory:
            self.mask_veg_dir_edit.setText(directory)
            
    def browse_output_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir_edit.text())
        if directory:
            self.output_dir_edit.setText(directory)
            
    def load_pairs(self):
        self.image_dir = self.image_dir_edit.text()
        self.mask_dir = self.mask_dir_edit.text()
        self.mask_veg_dir = self.mask_veg_dir_edit.text()
        self.output_dir = self.output_dir_edit.text()
        self.mask_suffix = self.suffix_edit.text()
        self.mask_veg_suffix = self.veg_suffix_edit.text()
        
        if not all([self.image_dir, self.mask_dir, self.mask_veg_dir, self.output_dir]):
            QMessageBox.warning(self, "Warning", "Please select all directories!")
            return
            
        if not all(os.path.exists(d) for d in [self.image_dir, self.mask_dir, self.mask_veg_dir]):
            QMessageBox.warning(self, "Warning", "One or more directories do not exist!")
            return
            
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup CSV with new structure
        self.csv_path = os.path.join(self.output_dir, 'review_log.csv')
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'image_file', 'mask_file', 'mask_veg_file', 'mask_type', 'status', 'notes'])
        
        self.load_review_data()
        self.find_pairs()
        self.update_pair_statuses()
        self.filter_pairs()
        
        if self.filtered_pairs:
            self.current_index = 0
            self.load_current_pair()
            self.update_ui()
            
        # Always enable show_reviewed checkbox if we have any pairs
        self.show_reviewed_cb.setEnabled(len(self.all_pairs) > 0)
        
        # Enable go to index controls
        if self.filtered_pairs:
            self.goto_spinbox.setEnabled(True)
            self.goto_btn.setEnabled(True)
            self.goto_spinbox.setMaximum(len(self.filtered_pairs))
            self.goto_spinbox.setValue(1)
        else:
            self.goto_spinbox.setEnabled(False)
            self.goto_btn.setEnabled(False)
            
    def load_review_data(self):
        self.review_data = {}
        if os.path.exists(self.csv_path):
            try:
                print(f"Loading CSV from: {self.csv_path}")
                df = pd.read_csv(self.csv_path)
                print(f"CSV columns: {list(df.columns)}")
                print(f"CSV shape: {df.shape}")
                
                if not df.empty and 'image_file' in df.columns:
                    # Handle both old and new CSV formats
                    if 'mask_type' in df.columns:
                        # New format with mask_type
                        for _, row in df.iterrows():
                            key = (row['image_file'], row.get('mask_file', ''), row.get('mask_veg_file', ''), row['mask_type'])
                            self.review_data[key] = {
                                'status': row['status'],
                                'timestamp': row['timestamp'],
                                'mask_type': row['mask_type'],
                                'notes': row.get('notes', '')
                            }
                            print(f"Loaded: {key} -> {row['status']}")
                    else:
                        # Old format - convert to new format
                        status_col = 'status' if 'status' in df.columns else 'decision'
                        for _, row in df.iterrows():
                            # Assume old entries are for regular masks
                            key = (row['image_file'], row['mask_file'], '', 'mask')
                            self.review_data[key] = {
                                'status': row[status_col],
                                'timestamp': row['timestamp'],
                                'mask_type': 'mask',
                                'notes': row.get('notes', '')
                            }
                    print(f"Total loaded {len(self.review_data)} review records from CSV")
                else:
                    print("CSV is empty or missing required columns")
            except Exception as e:
                print(f"Error loading review data: {e}")
                import traceback
                traceback.print_exc()
                
    def find_pairs(self):
        self.all_pairs = []
        image_extensions = ['.tif', '.tiff', '.jpg', '.jpeg', '.png', '.bmp']
        
        image_files = [f for f in os.listdir(self.image_dir) 
                      if any(f.lower().endswith(ext) for ext in image_extensions)
                      and self.mask_suffix not in f
                      and self.mask_veg_suffix not in f]
        
        for image_file in sorted(image_files):
            image_path = os.path.join(self.image_dir, image_file)
            base_name = os.path.splitext(image_file)[0]
            ext = os.path.splitext(image_file)[1]
            
            # Find regular mask
            mask_found = False
            mask_path = None
            mask_file = None
            
            possible_masks = [
                base_name + self.mask_suffix + ext,
                base_name + self.mask_suffix + '.tif',
                base_name + self.mask_suffix + '.png',
            ]
            
            for mask_name in possible_masks:
                mask_test_path = os.path.join(self.mask_dir, mask_name)
                if os.path.exists(mask_test_path):
                    mask_path = mask_test_path
                    mask_file = mask_name
                    mask_found = True
                    break
            
            # Find mask_veg
            mask_veg_found = False
            mask_veg_path = None
            mask_veg_file = None
            
            possible_mask_vegs = [
                base_name + self.mask_veg_suffix + ext,
                base_name + self.mask_veg_suffix + '.tif',
                base_name + self.mask_veg_suffix + '.png',
            ]
            
            for mask_veg_name in possible_mask_vegs:
                mask_veg_test_path = os.path.join(self.mask_veg_dir, mask_veg_name)
                if os.path.exists(mask_veg_test_path):
                    mask_veg_path = mask_veg_test_path
                    mask_veg_file = mask_veg_name
                    mask_veg_found = True
                    break
            
            # Only add if we have both mask and mask_veg
            if mask_found and mask_veg_found:
                print(f"Found triplet: {image_file} + {mask_file} + {mask_veg_file}")
                self.all_pairs.append({
                    'image_path': image_path,
                    'mask_path': mask_path,
                    'mask_veg_path': mask_veg_path,
                    'image_file': image_file,
                    'mask_file': mask_file,
                    'mask_veg_file': mask_veg_file,
                    'status': 'not_reviewed'  # Will be updated later
                })
            else:
                print(f"Incomplete triplet for {image_file}: mask={mask_found}, mask_veg={mask_veg_found}")
                
        print(f"Total triplets found: {len(self.all_pairs)}")
                    
    def update_pair_statuses(self):
        """Update pair statuses from loaded review data."""
        print(f"Updating statuses for {len(self.all_pairs)} pairs")
        print(f"Review data contains {len(self.review_data)} entries")
        
        for pair in self.all_pairs:
            # Check both mask types for this triplet
            mask_key = (pair['image_file'], pair['mask_file'], pair['mask_veg_file'], 'mask')
            mask_veg_key = (pair['image_file'], pair['mask_file'], pair['mask_veg_file'], 'mask_veg')
            
            # If either has been reviewed, mark as reviewed (prefer mask_veg)
            if mask_veg_key in self.review_data:
                pair['status'] = self.review_data[mask_veg_key]['status']
                print(f"  Updated from mask_veg: {pair['status']}")
            elif mask_key in self.review_data:
                pair['status'] = self.review_data[mask_key]['status']
                print(f"  Updated from mask: {pair['status']}")
            else:
                print(f"  No review data found for: {pair['image_file']}")
                
        print("Status update complete")
        
    def filter_pairs(self):
        if self.show_reviewed_cb.isChecked():
            self.filtered_pairs = self.all_pairs.copy()
        else:
            self.filtered_pairs = [p for p in self.all_pairs if p['status'] == 'not_reviewed']
            
        # Reset index if current is out of bounds
        if self.current_index >= len(self.filtered_pairs):
            self.current_index = 0
            
        # Update counts
        total_pairs = len(self.all_pairs)
        unreviewed_pairs = len([p for p in self.all_pairs if p['status'] == 'not_reviewed'])
        correct_pairs = len([p for p in self.all_pairs if p['status'] == 'correct'])
        incorrect_pairs = len([p for p in self.all_pairs if p['status'] == 'incorrect'])
        
        self.status_label.setText(
            f"Total: {total_pairs} | Unreviewed: {unreviewed_pairs} | "
            f"Correct: {correct_pairs} | Incorrect: {incorrect_pairs}"
        )
        
        if self.filtered_pairs:
            self.load_current_pair()
            self.update_ui()
        else:
            self.clear_display()
            
        # Update go to index controls
        if self.filtered_pairs:
            self.goto_spinbox.setEnabled(True)
            self.goto_btn.setEnabled(True)
            self.goto_spinbox.setMaximum(len(self.filtered_pairs))
            # Keep current position if valid, otherwise reset to 1
            if self.current_index < len(self.filtered_pairs):
                self.goto_spinbox.setValue(self.current_index + 1)
            else:
                self.goto_spinbox.setValue(1)
        else:
            self.goto_spinbox.setEnabled(False)
            self.goto_btn.setEnabled(False)
            self.goto_spinbox.setMaximum(1)
            
    def clear_display(self):
        self.clear_current_triplet()
        self.current_file_label.setText("No pairs to review")
        self.status_indicator.setText("")
        self.status_indicator.setStyleSheet("QLabel { padding: 5px; border-radius: 3px; }")
        self.progress_label.setText("0 / 0")
        self.progress_bar.setValue(0)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.correct_btn.setEnabled(False)
        self.incorrect_btn.setEnabled(False)
        self.unreview_btn.setEnabled(False)
        self.goto_spinbox.setEnabled(False)
        self.goto_btn.setEnabled(False)
        
    def clear_current_triplet(self):
        """Remove only the current triplet layers, preserve other layers."""
        for layer in self.current_triplet_layers[:]:  # Create copy to iterate safely
            try:
                if layer is not None:
                    layer_id = layer.id()
                    if QgsProject.instance().mapLayer(layer_id):
                        QgsProject.instance().removeMapLayer(layer_id)
            except RuntimeError:
                # Layer already deleted, skip
                pass
        self.current_triplet_layers.clear()
        
    def load_current_pair(self):
        if not self.filtered_pairs or self.current_index >= len(self.filtered_pairs):
            return
            
        # Clear only previous triplet layers
        self.clear_current_triplet()
        
        current_pair = self.filtered_pairs[self.current_index]
        image_path = current_pair['image_path']
        mask_path = current_pair['mask_path']
        mask_veg_path = current_pair['mask_veg_path']
        base_name = os.path.splitext(current_pair['image_file'])[0]
        
        # Load image
        image_layer = QgsRasterLayer(image_path, f"{base_name}_image")
        if image_layer.isValid():
            self.configure_image_bands(image_layer)
            QgsProject.instance().addMapLayer(image_layer)
            self.current_triplet_layers.append(image_layer)
            
        # Load mask (initially hidden)
        mask_layer = QgsRasterLayer(mask_path, f"{base_name}_mask")
        if mask_layer.isValid():
            QgsProject.instance().addMapLayer(mask_layer)
            mask_layer.setOpacity(0.6)
            self.configure_mask_symbology(mask_layer)
            self.current_triplet_layers.append(mask_layer)
            # Hide mask layer using layer tree
            root = QgsProject.instance().layerTreeRoot()
            layer_tree_layer = root.findLayer(mask_layer.id())
            if layer_tree_layer:
                layer_tree_layer.setItemVisibilityChecked(False)
            print(f"Loaded mask: {mask_path}")
        else:
            print(f"Failed to load mask: {mask_path}")
            
        # Load mask_veg (initially visible)
        mask_veg_layer = QgsRasterLayer(mask_veg_path, f"{base_name}_mask_veg")
        if mask_veg_layer.isValid():
            QgsProject.instance().addMapLayer(mask_veg_layer)
            mask_veg_layer.setOpacity(0.6)
            self.configure_mask_symbology(mask_veg_layer)
            self.current_triplet_layers.append(mask_veg_layer)
            # Ensure mask_veg layer is visible
            root = QgsProject.instance().layerTreeRoot()
            layer_tree_layer = root.findLayer(mask_veg_layer.id())
            if layer_tree_layer:
                layer_tree_layer.setItemVisibilityChecked(True)
            print(f"Loaded mask_veg: {mask_veg_path}")
        else:
            print(f"Failed to load mask_veg: {mask_veg_path}")
            
        # Zoom to image layer
        if image_layer.isValid():
            self.iface.setActiveLayer(image_layer)
            self.iface.zoomToActiveLayer()
            
    def update_ui(self):
        if not self.filtered_pairs:
            self.clear_display()
            return
            
        current_pair = self.filtered_pairs[self.current_index]
        image_name = current_pair['image_file']
        mask_name = current_pair['mask_file']
        mask_veg_name = current_pair['mask_veg_file']
        status = current_pair['status']
        
        self.current_file_label.setText(f"Image: {image_name}\nMask: {mask_name}\nMask Veg: {mask_veg_name}")
        
        # Update status indicator
        if status == 'correct':
            self.status_indicator.setText("✓ CORRECT")
            self.status_indicator.setStyleSheet("QLabel { background-color: #4CAF50; color: white; padding: 5px; border-radius: 3px; }")
        elif status == 'incorrect':
            self.status_indicator.setText("✗ INCORRECT")
            self.status_indicator.setStyleSheet("QLabel { background-color: #f44336; color: white; padding: 5px; border-radius: 3px; }")
        else:
            self.status_indicator.setText("⚬ NOT REVIEWED")
            self.status_indicator.setStyleSheet("QLabel { background-color: #9E9E9E; color: white; padding: 5px; border-radius: 3px; }")
        
        # Update progress
        show_type = "All" if self.show_reviewed_cb.isChecked() else "Unreviewed"
        self.progress_label.setText(f"{self.current_index + 1} / {len(self.filtered_pairs)} ({show_type})")
        self.progress_bar.setMaximum(len(self.filtered_pairs))
        self.progress_bar.setValue(self.current_index + 1)
        
        # Update navigation buttons
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.filtered_pairs) - 1)
        
        # Update review buttons
        self.correct_btn.setEnabled(True)
        self.incorrect_btn.setEnabled(True)
        self.unreview_btn.setEnabled(status != 'not_reviewed')
        
        # Update go to spinbox to current position
        self.goto_spinbox.setValue(self.current_index + 1)
        
    def goto_index(self):
        """Jump to specified index in filtered pairs."""
        if not self.filtered_pairs:
            return
            
        target_index = self.goto_spinbox.value() - 1  # Convert to 0-based index
        
        if 0 <= target_index < len(self.filtered_pairs):
            self.current_index = target_index
            self.load_current_pair()
            self.update_ui()
        else:
            QMessageBox.warning(self, "Invalid Index", 
                              f"Index must be between 1 and {len(self.filtered_pairs)}")
            self.goto_spinbox.setValue(self.current_index + 1)  # Reset to current
        
    def previous_pair(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_pair()
            self.update_ui()
            
    def next_pair(self):
        if self.current_index < len(self.filtered_pairs) - 1:
            self.current_index += 1
            self.load_current_pair()
            self.update_ui()
            
    def goto_index(self):
        """Jump to specified index in filtered pairs."""
        if not self.filtered_pairs:
            return
            
        target_index = self.goto_spinbox.value() - 1  # Convert to 0-based index
        
        if 0 <= target_index < len(self.filtered_pairs):
            self.current_index = target_index
            self.load_current_pair()
            self.update_ui()
        else:
            QMessageBox.warning(self, "Invalid Index", 
                              f"Index must be between 1 and {len(self.filtered_pairs)}")
            self.goto_spinbox.setValue(self.current_index + 1)  # Reset to current
            
    def review_current(self, decision):
        if not self.filtered_pairs or self.current_index >= len(self.filtered_pairs):
            return
            
        current_pair = self.filtered_pairs[self.current_index]
        image_file = current_pair['image_file']
        mask_file = current_pair['mask_file']
        mask_veg_file = current_pair['mask_veg_file']
        
        # Get selected mask type
        mask_type = 'mask_veg' if self.mask_veg_radio.isChecked() else 'mask'
        
        # Create key for the selected mask type
        key = (image_file, mask_file, mask_veg_file, mask_type)
        
        # Update review data in memory
        self.review_data[key] = {
            'status': decision,
            'timestamp': datetime.now().isoformat(),
            'mask_type': mask_type,
            'notes': ''
        }
        
        # Save to CSV
        self.save_review_data()
        
        # Update pair status
        current_pair['status'] = decision
        
        # Update all_pairs as well
        for pair in self.all_pairs:
            if (pair['image_file'] == image_file and 
                pair['mask_file'] == mask_file and 
                pair['mask_veg_file'] == mask_veg_file):
                pair['status'] = decision
                break
        
        self.status_label.setText(f"Marked {mask_type} as {decision}")
        
        # If not showing reviewed and current is now reviewed, re-filter
        if not self.show_reviewed_cb.isChecked() and decision != 'not_reviewed':
            # Remove current pair from filtered list
            self.filtered_pairs.pop(self.current_index)
            
            # Adjust index
            if self.current_index >= len(self.filtered_pairs) and self.filtered_pairs:
                self.current_index = len(self.filtered_pairs) - 1
                
            # Load next pair or finish
            if self.filtered_pairs:
                self.load_current_pair()
                self.update_ui()
            else:
                self.clear_display()
                self.status_label.setText("All pairs reviewed! Toggle 'Show Reviewed' to see them.")
        else:
            # Just update UI to reflect new status
            self.update_ui()
            
        # Update counts in status
        self.filter_pairs()
        
    def save_review_data(self):
        """Save all review data to CSV, avoiding duplicates."""
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'image_file', 'mask_file', 'mask_veg_file', 'mask_type', 'status', 'notes'])
            
            for (image_file, mask_file, mask_veg_file, mask_type), data in self.review_data.items():
                writer.writerow([
                    data['timestamp'],
                    image_file,
                    mask_file,
                    mask_veg_file,
                    mask_type,
                    data['status'],
                    data.get('notes', '')
                ])
        
    def configure_image_bands(self, image_layer):
        """Configure image layer to use 4-3-2 band order for multi-band images."""
        if image_layer.bandCount() >= 4:
            try:
                # Create multi-band color renderer with 4-3-2 band order
                renderer = QgsMultiBandColorRenderer(
                    image_layer.dataProvider(), 
                    4,  # Red band
                    3,  # Green band  
                    2   # Blue band
                )
                image_layer.setRenderer(renderer)
                image_layer.triggerRepaint()
            except Exception as e:
                print(f"Error setting band order: {e}")
                # Fallback to default if error occurs
                
    def configure_mask_symbology(self, mask_layer):
        """Configure mask layer to display value 1 as white."""
        try:
            # Create a pseudocolor renderer
            renderer = QgsSingleBandPseudoColorRenderer(mask_layer.dataProvider(), 1)
            
            # Create color ramp shader
            shader = QgsRasterShader()
            ramp_shader = QgsColorRampShader()
            ramp_shader.setColorRampType(QgsColorRampShader.Discrete)
            
            # Define color map: value 0 = transparent, value 1 = white
            color_list = [
                QgsColorRampShader.ColorRampItem(0, QtCore.Qt.transparent, '0'),
                QgsColorRampShader.ColorRampItem(1, QtCore.Qt.white, '1')
            ]
            
            ramp_shader.setColorRampItemList(color_list)
            shader.setRasterShaderFunction(ramp_shader)
            renderer.setShader(shader)
            
            # Apply renderer to layer
            mask_layer.setRenderer(renderer)
            mask_layer.triggerRepaint()
            
        except Exception as e:
            print(f"Error setting mask symbology: {e}")