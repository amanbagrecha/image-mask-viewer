import os
import csv
import pandas as pd
from datetime import datetime
from pathlib import Path
from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.core import QgsRasterLayer, QgsProject, Qgis, QgsMultiBandColorRenderer
from qgis.PyQt.QtWidgets import (QDockWidget, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QLineEdit, QPushButton, 
                                 QGroupBox, QMessageBox, QWidget,
                                 QProgressBar, QSpacerItem, QSizePolicy,
                                 QCheckBox)


class ImageMaskDock(QDockWidget):
    
    def __init__(self, iface, parent=None):
        super(ImageMaskDock, self).__init__("Image Mask Reviewer", parent)
        self.iface = iface
        self.image_dir = ""
        self.mask_dir = ""
        self.output_dir = ""
        self.mask_suffix = "_mask"
        self.all_pairs = []
        self.filtered_pairs = []
        self.current_index = 0
        self.csv_path = ""
        self.review_data = {}
        
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
        
        # Output directory
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output:"))
        self.output_dir_edit = QLineEdit()
        output_layout.addWidget(self.output_dir_edit)
        self.browse_output_btn = QPushButton("...")
        self.browse_output_btn.setMaximumWidth(30)
        output_layout.addWidget(self.browse_output_btn)
        dir_layout.addLayout(output_layout)
        
        # Mask suffix
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("Suffix:"))
        self.suffix_edit = QLineEdit(self.mask_suffix)
        suffix_layout.addWidget(self.suffix_edit)
        dir_layout.addLayout(suffix_layout)
        
        self.load_btn = QPushButton("Load Pairs")
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
        self.browse_output_btn.clicked.connect(self.browse_output_directory)
        self.load_btn.clicked.connect(self.load_pairs)
        self.show_reviewed_cb.toggled.connect(self.filter_pairs)
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
            
    def browse_output_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.output_dir_edit.text())
        if directory:
            self.output_dir_edit.setText(directory)
            
    def load_pairs(self):
        self.image_dir = self.image_dir_edit.text()
        self.mask_dir = self.mask_dir_edit.text()
        self.output_dir = self.output_dir_edit.text()
        self.mask_suffix = self.suffix_edit.text()
        
        if not all([self.image_dir, self.mask_dir, self.output_dir]):
            QMessageBox.warning(self, "Warning", "Please select all directories!")
            return
            
        if not all(os.path.exists(d) for d in [self.image_dir, self.mask_dir]):
            QMessageBox.warning(self, "Warning", "Image or mask directory does not exist!")
            return
            
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup CSV
        self.csv_path = os.path.join(self.output_dir, 'review_log.csv')
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'image_file', 'mask_file', 'status', 'notes'])
        
        self.load_review_data()
        self.find_pairs()
        self.update_pair_statuses()
        self.filter_pairs()
        
        if self.filtered_pairs:
            self.current_index = 0
            self.load_current_pair()
            self.update_ui()
            
        # Always enable show_reviewed checkbox if we have any pairs (reviewed or not)
        self.show_reviewed_cb.setEnabled(len(self.all_pairs) > 0)
            
    def load_review_data(self):
        self.review_data = {}
        if os.path.exists(self.csv_path):
            try:
                print(f"Loading CSV from: {self.csv_path}")
                df = pd.read_csv(self.csv_path)
                print(f"CSV columns: {list(df.columns)}")
                print(f"CSV shape: {df.shape}")
                
                if not df.empty and 'image_file' in df.columns:
                    # Handle both 'status' and 'decision' column names for backward compatibility
                    status_col = 'status' if 'status' in df.columns else 'decision'
                    print(f"Using status column: {status_col}")
                    
                    for _, row in df.iterrows():
                        key = (row['image_file'], row['mask_file'])
                        self.review_data[key] = {
                            'status': row[status_col],
                            'timestamp': row['timestamp'],
                            'notes': row.get('notes', '')
                        }
                        print(f"Loaded: {key} -> {row[status_col]}")
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
                      and self.mask_suffix not in f]
        
        for image_file in sorted(image_files):
            image_path = os.path.join(self.image_dir, image_file)
            base_name = os.path.splitext(image_file)[0]
            ext = os.path.splitext(image_file)[1]
            
            possible_masks = [
                base_name + self.mask_suffix + ext,
                base_name + self.mask_suffix + '.tif',
                base_name + self.mask_suffix + '.png',
            ]
            
            for mask_name in possible_masks:
                mask_path = os.path.join(self.mask_dir, mask_name)
                if os.path.exists(mask_path):
                    self.all_pairs.append({
                        'image_path': image_path,
                        'mask_path': mask_path,
                        'image_file': image_file,
                        'mask_file': mask_name,
                        'status': 'not_reviewed'  # Will be updated later
                    })
                    break
                    
    def update_pair_statuses(self):
        """Update pair statuses from loaded review data."""
        print(f"Updating statuses for {len(self.all_pairs)} pairs")
        print(f"Review data contains {len(self.review_data)} entries")
        
        for pair in self.all_pairs:
            key = (pair['image_file'], pair['mask_file'])
            print(f"Checking pair: {key}")
            
            if key in self.review_data:
                old_status = pair['status']
                pair['status'] = self.review_data[key]['status']
                print(f"  Updated: {old_status} -> {pair['status']}")
            else:
                print(f"  No review data found for: {key}")
                
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
            
    def clear_display(self):
        QgsProject.instance().clear()
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
        # Don't disable show_reviewed_cb - keep it enabled so user can toggle to see reviewed pairs
        
    def load_current_pair(self):
        if not self.filtered_pairs or self.current_index >= len(self.filtered_pairs):
            return
            
        QgsProject.instance().clear()
        
        current_pair = self.filtered_pairs[self.current_index]
        image_path = current_pair['image_path']
        mask_path = current_pair['mask_path']
        base_name = os.path.splitext(current_pair['image_file'])[0]
        
        # Load image
        image_layer = QgsRasterLayer(image_path, f"{base_name}_image")
        if image_layer.isValid():
            self.configure_image_bands(image_layer)
            QgsProject.instance().addMapLayer(image_layer)
            
        # Load mask
        mask_layer = QgsRasterLayer(mask_path, f"{base_name}_mask")
        if mask_layer.isValid():
            QgsProject.instance().addMapLayer(mask_layer)
            mask_layer.setOpacity(0.6)
            
        # Zoom to layer
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
        status = current_pair['status']
        
        self.current_file_label.setText(f"Image: {image_name}\nMask: {mask_name}")
        
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
            
    def review_current(self, decision):
        if not self.filtered_pairs or self.current_index >= len(self.filtered_pairs):
            return
            
        current_pair = self.filtered_pairs[self.current_index]
        image_file = current_pair['image_file']
        mask_file = current_pair['mask_file']
        key = (image_file, mask_file)
        
        # Update review data in memory
        self.review_data[key] = {
            'status': decision,
            'timestamp': datetime.now().isoformat(),
            'notes': ''
        }
        
        # Rewrite entire CSV to avoid duplicates
        self.save_review_data()
        
        # Update pair status
        current_pair['status'] = decision
        
        # Update all_pairs as well
        for pair in self.all_pairs:
            if pair['image_file'] == image_file and pair['mask_file'] == mask_file:
                pair['status'] = decision
                break
        
        self.status_label.setText(f"Marked {mask_file} as {decision}")
        
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
            writer.writerow(['timestamp', 'image_file', 'mask_file', 'status', 'notes'])
            
            for (image_file, mask_file), data in self.review_data.items():
                writer.writerow([
                    data['timestamp'],
                    image_file,
                    mask_file,
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