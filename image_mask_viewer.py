from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject, QgsRasterLayer, Qgis
import os.path
from .image_mask_dock import ImageMaskDock


class ImageMaskViewer:

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        self.actions = []
        self.menu = '&Image Mask Viewer'
        self.toolbar = self.iface.addToolBar('ImageMaskViewer')
        self.toolbar.setObjectName('ImageMaskViewer')
        
        self.dock = None
        self.first_start = True

    def add_action(self, icon_path, text, callback, enabled_flag=True, 
                   add_to_menu=True, add_to_toolbar=True, status_tip=None, 
                   whats_this=None, parent=None):
        
        icon = QIcon(icon_path) if icon_path else QIcon()
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(
            icon_path,
            text='Image Mask Reviewer',
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu('&Image Mask Viewer', action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar
        
        if self.dock:
            self.iface.removeDockWidget(self.dock)

    def run(self):
        if self.first_start:
            self.first_start = False
            self.dock = ImageMaskDock(self.iface)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
            self.dock.show()  # Always show on first creation
        else:
            # Toggle visibility for subsequent clicks
            if self.dock.isVisible():
                self.dock.hide()
            else:
                self.dock.show()