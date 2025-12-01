# -*- coding: utf-8 -*-

__author__ = 'UAV4GEO'
__date__ = '2024-10-21'
__copyright__ = '(C) 2024 by UAV4GEO'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect

from qgis.core import QgsProcessingAlgorithm, QgsApplication
from qgis.PyQt.QtWidgets import QAction, QApplication
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface
from .raster_merge_provider import RasterMergeProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class RasterMergePlugin(object):

    def __init__(self, iface):
        self.provider = None
        self.iface = iface

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = RasterMergeProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

        self.merge_orthos = QAction(QIcon(os.path.join(os.path.dirname(__file__), "icons", "qrastermerge.svg")), "Merge Orthophotos")
        self.merge_orthos.triggered.connect(self.merge_orthos_click)
        self.iface.addToolBarIcon(self.merge_orthos)

        self.iface.addPluginToRasterMenu("QRasterMerge", self.merge_orthos)

    def merge_orthos_click(self):
        iface.openProcessingAlgorithm('rastermerge:mergeorthophotos')

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
