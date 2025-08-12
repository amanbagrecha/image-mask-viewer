# Image Mask Viewer

<div align="center">

![Image Mask Viewer](icon.png)

A QGIS plugin for loading and reviewing paired images with their corresponding masks

[![QGIS Version](https://img.shields.io/badge/QGIS-3.0+-brightgreen.svg)](https://qgis.org)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/amanbagrecha/image-mask-viewer)
[![License](https://img.shields.io/badge/license-GPL--3.0-orange.svg)](LICENSE)

</div>

## Description

Image Mask Viewer provides a streamlined interface for loading and reviewing paired images with their corresponding masks. It's particularly useful for remote sensing applications, image segmentation review, and validation workflows where you need to systematically examine image-mask pairs.

The plugin automatically matches images with their masks based on configurable naming conventions and provides an intuitive review interface with navigation controls and decision tracking.

## Features

- 📁 **Directory-based Loading**: Select separate directories for images, regular masks, and vegetation masks
- 🔗 **Smart Pairing**: Automatic matching of images with masks based on customizable suffix patterns
- 👁️ **Visual Review Interface**: Side-by-side viewing of images with overlay masks
- ✅ **Decision Tracking**: Mark pairs as correct, incorrect, or reset review status
- 🎯 **Dual Mask Support**: Handle both regular masks and vegetation masks simultaneously
- 📊 **Progress Tracking**: Visual progress bar and comprehensive statistics
- 💾 **Review Logging**: Automatic logging of all review decisions with timestamps
- 🔄 **Filter Options**: Toggle between showing all pairs or only unreviewed ones
- 🎨 **Smart Symbology**: Automatic styling for optimal mask visualization
- 📐 **Band Configuration**: Automatic 4-3-2 band ordering for multi-spectral imagery

## Installation

### From QGIS Plugin Repository

1. Open QGIS
2. Go to `Plugins` → `Manage and Install Plugins...`
3. Search for "Image Mask Viewer"
4. Click `Install Plugin`

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/amanbagrecha/image-mask-viewer/releases)
2. Extract the ZIP file to your QGIS plugins directory:
   - **Windows**: `C:\Users\{username}\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS
4. Enable the plugin in `Plugins` → `Manage and Install Plugins...` → `Installed`

### Development Installation

```bash
# Clone the repository
git clone https://github.com/amanbagrecha/image-mask-viewer.git

# Create symbolic link to QGIS plugins directory (Linux/macOS)
ln -s /path/to/image-mask-viewer ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/image_mask_viewer

# Or copy to plugins directory (Windows)
xcopy /E /I image-mask-viewer "C:\Users\{username}\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\image_mask_viewer"
```

## Usage

### Quick Start

1. **Activate the Plugin**: Click the Image Mask Viewer icon in the toolbar or go to `Plugins` → `Image Mask Viewer`
2. **Setup Directories**: Configure your directory paths in the dock panel:
   - **Images**: Directory containing your source images
   - **Masks**: Directory containing regular mask files
   - **Mask Veg**: Directory containing vegetation mask files
   - **Output**: Directory where review logs will be saved
3. **Configure Suffixes**: Set the naming patterns for your masks (default: `_rf_classified` and `_vegmask_ndvi`)
4. **Load Triplets**: Click "Load Triplets" to scan and pair your files
5. **Start Reviewing**: Use the navigation and review buttons to examine each pair

### Directory Structure Example

```
project/
├── images/
│   ├── scene_001.tif
│   ├── scene_002.tif
│   └── scene_003.tif
├── masks/
│   ├── scene_001_rf_classified.tif
│   ├── scene_002_rf_classified.tif
│   └── scene_003_rf_classified.tif
├── masks_veg/
│   ├── scene_001_vegmask_ndvi.tif
│   ├── scene_002_vegmask_ndvi.tif
│   └── scene_003_vegmask_ndvi.tif
└── output/
    └── review_log.csv
```

### Review Interface

#### Navigation Controls
- **Previous/Next**: Navigate through your image pairs
- **Progress Bar**: Shows current position and total count
- **Filter Toggle**: Switch between showing all pairs or only unreviewed ones

#### Review Decisions
- **✓ Correct**: Mark the current mask as accurate
- **✗ Incorrect**: Mark the current mask as inaccurate  
- **↶ Reset**: Clear the review status and mark as not reviewed

#### Mask Type Selection
- **Mask**: Save decision for the regular classification mask
- **Mask Veg**: Save decision for the vegetation mask (default)

### Output Files

The plugin generates a `review_log.csv` file in your output directory with the following columns:
- `timestamp`: When the review decision was made
- `image_file`: Name of the source image
- `mask_file`: Name of the regular mask file
- `mask_veg_file`: Name of the vegetation mask file
- `mask_type`: Which mask type was reviewed (`mask` or `mask_veg`)
- `status`: Review decision (`correct`, `incorrect`, or `not_reviewed`)
- `notes`: Additional notes (reserved for future use)

### Keyboard Shortcuts

- **Space**: Mark as Correct
- **X**: Mark as Incorrect
- **R**: Reset review status
- **Left Arrow**: Previous pair
- **Right Arrow**: Next pair

## Requirements

- QGIS 3.0 or higher
- Python 3.6+
- pandas library (usually included with QGIS)

### Supported File Formats

**Images**: TIFF, JPEG, PNG, BMP  
**Masks**: TIFF, PNG (recommended: single-band integer rasters)

## Configuration

### Custom Naming Patterns

You can customize the suffix patterns to match your file naming convention:

```
Base filename: scene_001.tif
Mask suffix: _rf_classified → scene_001_rf_classified.tif
Veg suffix: _vegmask_ndvi → scene_001_vegmask_ndvi.tif
```

The plugin will automatically try multiple extensions (.tif, .png) when searching for mask files.

### Layer Styling

- **Images**: Automatically configured for 4-3-2 band display (false color infrared) for multi-band imagery
- **Masks**: Value 1 displayed as white, value 0 as transparent with 60% opacity
- **Layer Management**: Only current triplet layers are shown; previous layers are automatically removed

## Troubleshooting

### Common Issues

**Plugin not appearing in menu**
- Ensure the plugin is enabled in Plugin Manager
- Check QGIS Python console for error messages

**Files not being paired**
- Verify directory paths are correct
- Check that mask files follow the expected naming convention
- Ensure file extensions match between images and masks

**Slow loading**
- Large raster files may take time to load and display
- Consider using pyramids/overviews for better performance

**CSV not saving**
- Verify write permissions to the output directory
- Check that the output directory exists

### Getting Help

- Check the [Issues](https://github.com/amanbagrecha/image-mask-viewer/issues) page for known problems
- Create a new issue with details about your problem
- Include QGIS version, plugin version, and error messages

## Development

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Building from Source

```bash
# Clone the repository
git clone https://github.com/amanbagrecha/image-mask-viewer.git
cd image-mask-viewer

# Install to QGIS plugins directory
make deploy

# Restart QGIS to see changes
```

### Testing

The plugin includes a comprehensive test suite. Run tests with:

```bash
# Unit tests
python -m pytest tests/

# Integration tests
make test
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this plugin in your research, please cite:

```bibtex
@software{image_mask_viewer,
  title={Image Mask Viewer: A QGIS Plugin for Image-Mask Pair Review},
  author={Aman Bagrecha},
  year={2025},
  url={https://github.com/amanbagrecha/image-mask-viewer}
}
```

## Acknowledgments

- Built with the [QGIS Plugin Builder](https://g-sherman.github.io/Qgis-Plugin-Builder/)
- Icons from [Icons8](https://icons8.com)
- Thanks to the QGIS development team and community

## Changelog

### Version 1.0.0 (2024-01-01)
- Initial release
- Basic image-mask loading functionality
- Directory selection interface
- Automatic pairing based on suffix patterns
- Review decision tracking with CSV export
- Dual mask type support (regular and vegetation masks)
- Progress tracking and filtering options

---

<div align="center">

**[⬆ Back to Top](#image-mask-viewer)**

Made with ❤️ for the QGIS community

</div>