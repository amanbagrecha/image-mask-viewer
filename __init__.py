# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ImageMaskViewer
                                 A QGIS plugin
 Load and view paired images with their masks
                             -------------------
        begin                : 2024-01-01
        copyright            : (C) 2024 by Your Name
        email                : your.email@example.com
 ***************************************************************************/

 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ImageMaskViewer class from file ImageMaskViewer.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .image_mask_viewer import ImageMaskViewer
    return ImageMaskViewer(iface)