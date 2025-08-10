# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ImageMaskDialog
                                 A QGIS plugin dialog
 Load and view paired images with their masks
                             -------------------
        begin                : 2024-01-01
        copyright            : (C) 2024 by Your Name
        email                : your.email@example.com
 ***************************************************************************/
"""

import os
from pathlib import Path
from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsRasterLayer, QgsProject, Qgis
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QLineEdit, QPushButton, 
                                 QListWidget, QGroupBox, QMessageBox,
                                 QListWidgetItem, QAbstractItemView)


class ImageMaskDialog(QDialog):
    
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(ImageMaskDialog, self).__init__(parent)
        self.iface = iface
        self.image_dir = ""
        self.mask_dir = ""
        self.mask_suffix = "_mask"  # Default suffix for mask files
        self.current_pairs = []  # Store (image_path, mask_path) tuples
        
        self.setupUi()
        self.connectSignals()
        
    def setupUi(self):
        """Set up the user interface."""
        self.setWindowTitle("Image-Mask Viewer")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Directory selection group
        dir_group = QGroupBox("Directories")
        dir_layout = QVBoxLayout()
        
        # Image directory
        image_layout = QHBoxLayout()
        image_layout.addWidget(QLabel("Images directory:"))
        self.image_dir_edit = QLineEdit()
        image_layout.addWidget(self.image_dir_edit)
        self.browse_image_btn = QPushButton("...")
        self.browse_image_btn.setMaximumWidth(30)
        image_layout.addWidget(self.browse_image_btn)
        dir_layout.addLayout(image_layout)
        
        # Mask directory
        mask_layout = QHBoxLayout()
        mask_layout.addWidget(QLabel("Masks directory:"))
        self.mask_dir_edit = QLineEdit()
        mask_layout.addWidget(self.mask_dir_edit)
        self.browse_mask_btn = QPushButton("...")
        self.browse_mask_btn.setMaximumWidth(30)
        mask_layout.addWidget(self.browse_mask_btn)
        dir_layout.addLayout(mask_layout)
        
        # Mask suffix
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("Mask suffix:"))
        self.suffix_edit = QLineEdit(self.mask_suffix)
        self.suffix_edit.setPlaceholderText("e.g., _mask, _label, etc.")
        suffix_layout.addWidget(self.suffix_edit)
        dir_layout.addLayout(suffix_layout)
        
        dir_group.setLayout(dir_layout)
        main_layout.addWidget(dir_group)
        
        # Load button
        self.load_btn = QPushButton("Load Image Pairs")
        self.load_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; }")
        main_layout.addWidget(self.load_btn)
        
        # File list
        list_group = QGroupBox("Image-Mask Pairs")
        list_layout = QVBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        list_layout.addWidget(self.file_list)
        
        list_group.setLayout(list_layout)
        main_layout.addWidget(list_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.add_selected_btn = QPushButton("Add Selected to Map")
        self.add_selected_btn.setEnabled(False)
        button_layout.addWidget(self.add_selected_btn)
        
        self.add_all_btn = QPushButton("Add All to Map")
        self.add_all_btn.setEnabled(False)
        button_layout.addWidget(self.add_all_btn)
        
        self.clear_btn = QPushButton("Clear Layers")
        button_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: #666; padding: 5px; }")
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
        
    def connectSignals(self):
        """Connect signals and slots."""
        self.browse_image_btn.clicked.connect(self.browse_image_directory)
        self.browse_mask_btn.clicked.connect(self.browse_mask_directory)
        self.load_btn.clicked.connect(self.load_image_pairs)
        self.add_selected_btn.clicked.connect(self.add_selected_to_map)
        self.add_all_btn.clicked.connect(self.add_all_to_map)
        self.clear_btn.clicked.connect(self.clear_layers)
        self.file_list.itemSelectionChanged.connect(self.on_selection_changed)
        
    def browse_image_directory(self):
        """Browse for image directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Image Directory", self.image_dir_edit.text())
        if directory:
            self.image_dir_edit.setText(directory)
            self.image_dir = directory
            # Auto-fill mask directory if empty
            if not self.mask_dir_edit.text():
                self.mask_dir_edit.setText(directory)
                self.mask_dir = directory
                
    def browse_mask_directory(self):
        """Browse for mask directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Mask Directory", self.mask_dir_edit.text())
        if directory:
            self.mask_dir_edit.setText(directory)
            self.mask_dir = directory
            
    def load_image_pairs(self):
        """Load and match image-mask pairs."""
        self.file_list.clear()
        self.current_pairs = []
        
        image_dir = self.image_dir_edit.text()
        mask_dir = self.mask_dir_edit.text()
        mask_suffix = self.suffix_edit.text()
        
        if not os.path.exists(image_dir):
            QMessageBox.warning(self, "Warning", "Image directory does not exist!")
            return
            
        if not os.path.exists(mask_dir):
            QMessageBox.warning(self, "Warning", "Mask directory does not exist!")
            return
            
        # Get all image files
        image_extensions = ['.tif', '.tiff', '.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        
        for file in os.listdir(image_dir):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                # Skip files that already have the mask suffix
                if mask_suffix and mask_suffix in file:
                    continue
                image_files.append(file)
                
        # Match with masks
        pairs_found = 0
        for image_file in sorted(image_files):
            image_path = os.path.join(image_dir, image_file)
            
            # Try to find corresponding mask
            base_name = os.path.splitext(image_file)[0]
            ext = os.path.splitext(image_file)[1]
            
            # Try different mask naming patterns
            possible_masks = [
                base_name + mask_suffix + ext,  # basename_mask.ext
                base_name + mask_suffix + '.tif',  # basename_mask.tif
                base_name + mask_suffix + '.png',  # basename_mask.png
            ]
            
            mask_found = False
            for mask_name in possible_masks:
                mask_path = os.path.join(mask_dir, mask_name)
                if os.path.exists(mask_path):
                    # Add to list
                    item = QListWidgetItem(f"✓ {image_file} → {mask_name}")
                    item.setData(QtCore.Qt.UserRole, (image_path, mask_path))
                    self.file_list.addItem(item)
                    self.current_pairs.append((image_path, mask_path))
                    pairs_found += 1
                    mask_found = True
                    break
                    
            if not mask_found:
                # Add image without mask
                item = QListWidgetItem(f"✗ {image_file} (no mask found)")
                item.setData(QtCore.Qt.UserRole, (image_path, None))
                item.setForeground(QtCore.Qt.gray)
                self.file_list.addItem(item)
                
        # Update status
        self.status_label.setText(f"Found {pairs_found} image-mask pairs out of {len(image_files)} images")
        
        # Enable/disable buttons
        self.add_all_btn.setEnabled(pairs_found > 0)
        self.on_selection_changed()
        
    def on_selection_changed(self):
        """Handle selection change in file list."""
        selected_items = self.file_list.selectedItems()
        # Enable add selected button only if valid pairs are selected
        has_valid = any(item.data(QtCore.Qt.UserRole)[1] is not None 
                       for item in selected_items)
        self.add_selected_btn.setEnabled(has_valid)
        
    def add_selected_to_map(self):
        """Add selected image-mask pairs to the map."""
        selected_items = self.file_list.selectedItems()
        added_count = 0
        
        for item in selected_items:
            image_path, mask_path = item.data(QtCore.Qt.UserRole)
            if mask_path:  # Only add if mask exists
                self.add_pair_to_map(image_path, mask_path)
                added_count += 1
                
        if added_count > 0:
            self.iface.messageBar().pushMessage(
                "Success", f"Added {added_count} image-mask pairs to the map",
                level=Qgis.Success, duration=3)
                
    def add_all_to_map(self):
        """Add all valid image-mask pairs to the map."""
        added_count = 0
        
        for image_path, mask_path in self.current_pairs:
            if mask_path:  # Only add if mask exists
                self.add_pair_to_map(image_path, mask_path)
                added_count += 1
                
        if added_count > 0:
            self.iface.messageBar().pushMessage(
                "Success", f"Added {added_count} image-mask pairs to the map",
                level=Qgis.Success, duration=3)
                
    def add_pair_to_map(self, image_path, mask_path):
        """Add a single image-mask pair to the map."""
        # Create group for the pair
        root = QgsProject.instance().layerTreeRoot()
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        group = root.addGroup(base_name)
        
        # Add image layer
        image_layer = QgsRasterLayer(image_path, f"{base_name} (image)")
        if image_layer.isValid():
            QgsProject.instance().addMapLayer(image_layer, False)
            group.addLayer(image_layer)
            
        # Add mask layer
        if mask_path:
            mask_layer = QgsRasterLayer(mask_path, f"{base_name} (mask)")
            if mask_layer.isValid():
                QgsProject.instance().addMapLayer(mask_layer, False)
                group.addLayer(mask_layer)
                # Set mask opacity to 50%
                mask_layer.setOpacity(0.5)
                
    def clear_layers(self):
        """Clear all layers from the project."""
        reply = QMessageBox.question(self, 'Clear Layers',
                                   'Are you sure you want to remove all layers from the project?',
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        if reply == QMessageBox.Yes:
            QgsProject.instance().clear()
            self.iface.messageBar().pushMessage(
                "Success", "All layers cleared",
                level=Qgis.Success, duration=2)