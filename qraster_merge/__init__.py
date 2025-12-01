# -*- coding: utf-8 -*-

__author__ = 'UAV4GEO'
__date__ = '2024-10-21'
__copyright__ = '(C) 2024 by UAV4GEO'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load RasterMerge class from file RasterMerge.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .raster_merge import RasterMergePlugin
    return RasterMergePlugin(iface)
