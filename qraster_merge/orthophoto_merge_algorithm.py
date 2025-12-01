# -*- coding: utf-8 -*-

__author__ = 'UAV4GEO'
__date__ = '2024-10-21'
__copyright__ = '(C) 2024 by UAV4GEO'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterNumber,
                       QgsProcessingAlgorithm,
                       QgsProcessingFeedback,
                       QgsRasterLayer,
                       QgsProcessingUtils,
                       QgsProject)
import os
import tempfile
from .log import WARNING, INFO, CRITICAL, set_log_feedback

class OrthophotoMergeAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT_LAYERS = 'INPUT_LAYERS'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr('Input layers'),
                layerType=QgsProcessing.TypeRaster,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                'BLEND_DISTANCE',
                self.tr('Blend Distance (pixels)'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=30,
                minValue=1
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                'EQUALIZE_HISTOGRAMS',
                self.tr('Equalize Color Histograms'),
                options=['RGB', 'LCH', 'Do not equalize (keep original pixels)'],
                defaultValue=0,
                allowMultiple=False
            )
        )

        

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('Merged layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        from .orthophoto import merge, compute_mask_raster, feather_raster
        from .cutline import compute_cutline
        from .io import related_file_path
        from .rio_hist.match import hist_match_worker

        INPUT_LAYERS = parameters.get('INPUT_LAYERS', [])
        if len(INPUT_LAYERS) <= 1:
            CRITICAL("You need at least two raster layers")
            return

        output_path = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        if feedback is None:
            feedback = QgsProcessingFeedback()
        
        set_log_feedback(feedback)

        layers = []
        for layer_id in INPUT_LAYERS:
            layer = QgsProcessingUtils.mapLayerFromString(layer_id, context)
            if isinstance(layer, QgsRasterLayer):
                layers.append(layer)

        if len(layers) <= 1:
            CRITICAL("You need at least two valid raster layers")
            return {}

        blend_distance = self.parameterAsInt(parameters, 'BLEND_DISTANCE', context)
        equalize_histograms = self.parameterAsEnum(parameters, 'EQUALIZE_HISTOGRAMS', context)
        
        temp_dir = QgsProcessingUtils.tempFolder()
        INFO(f"Using temporary directory: {temp_dir}")

        equalize = ['RGB', 'LCH', 'None'][equalize_histograms]
        sources = []

        if equalize != 'None':
            INFO("Equalizing histograms")

            reference = layers[0].source()
            sources.append(reference)

            for i in range(1, len(layers)):
                to_equalize = layers[i].source()

                equalized_file = related_file_path(to_equalize, postfix=".eq", temp_dir=temp_dir)

                INFO(f"Equalizing {to_equalize}")
                hist_match_worker(to_equalize, reference, equalized_file, 
                    1.0, {}, "1,2,3", equalize)
                
                if os.path.isfile(equalized_file):
                    sources.append(equalized_file)
                else:
                    WARNING(f"Cannot equalize {to_equalize}, skipping...")
                    sources.append(to_equalize)
        else:
            INFO("No histogram equalization")
            sources = [l.source() for l in layers]

        orthos_and_cuts = []

        for ortho_file in sources:
            if feedback.isCanceled():
                feedback.pushInfo("Processing cancelled by user.")
                return {}

            cutline_file = related_file_path(ortho_file, postfix=".cutline", replace_ext=".gpkg", temp_dir=temp_dir)
            INFO(f"Computing cutline: {ortho_file}")

            if not os.path.isfile(cutline_file):
                compute_cutline(ortho_file, cutline_file, scale=0.25)
            else:
                INFO(f"Using already computed cutline: {cutline_file}")

            
            if feedback.isCanceled():
                feedback.pushInfo("Processing cancelled by user.")
                return {}

            if not os.path.isfile(cutline_file):
                CRITICAL("Cannot compute cutline. Cannot proceed with merging")
                return {}
            
            orthocut_file = related_file_path(ortho_file, postfix=".cut", temp_dir=temp_dir)
            orthofeather_file = related_file_path(ortho_file, postfix=".feathered", temp_dir=temp_dir)

            if not os.path.isfile(orthocut_file):
                compute_mask_raster(ortho_file, cutline_file, 
                                                orthocut_file,
                                                blend_distance=blend_distance, only_max_coords_feature=True)
            else:
                INFO(f"Using already computed raster cut: {orthocut_file}")
            
            if feedback.isCanceled():
                feedback.pushInfo("Processing cancelled by user.")
                return {}

            if not os.path.isfile(orthofeather_file):
                feather_raster(ortho_file, 
                    orthofeather_file,
                    blend_distance=blend_distance
                )
            else:
                INFO(f"Using already computed feathered raster: {orthofeather_file}")
            
            orthos_and_cuts.append((orthofeather_file, orthocut_file))

        base_dir = os.path.dirname(output_path)
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)

        return {"OUTPUT": merge(orthos_and_cuts, output_path, feedback=feedback)}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Seamless Merge'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return OrthophotoMergeAlgorithm()
