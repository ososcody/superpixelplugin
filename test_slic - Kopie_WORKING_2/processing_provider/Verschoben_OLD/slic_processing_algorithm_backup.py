# Skript build arount the boiler plate code from:
# https://gis.stackexchange.com/questions/282773/writing-a-python-processing-script-with-qgis-3-0?rq=1
# See API: https://qgis.org/pyqgis/3.16/core/QgsProcessingAlgorithm.html
# And: https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/processing.html

import numpy as np  # eventuell rasterio nehmen?
import gdal
from osgeo import gdal
from osgeo.gdalconst import GDT_Float32
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterRasterDestination


from skimage import exposure
from skimage.segmentation import slic  # import slic
#from skimage.segmentation import quickshift
#from skimage.segmentation import watershed
#from skimage.segmentation import felzenszwalb
#from skimage.color import label2rgb  # Import the label2rgb function from the color module

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination)


class SuperpixelProcessingPluginSLIC(QgsProcessingAlgorithm):  # TODO: RENAME
    INPUT_RASTER_A = 'INPUT_RASTER_A'
    # INPUT_RASTER_B = 'INPUT_RASTER_B'

    # INPUT_DOUBLE = 'INPUT_DOUBLE'
    NSEGMENTS = 'NSEGMENTS'
    COMPACTNESS = 'COMPACTNESS'
    SIGMA = 'SIGMA'
    STARTLABEL = 'STARTLABEL'

    OUTPUT_RASTER_A = 'OUTPUT_RASTER_A'

    # OUTPUT_RASTER_B = 'OUTPUT_RASTER_B'

    def __init__(self): # TODO Hmmm...
        super().__init__()

    def name(self):
        return "SLIC"

    def tr(self, text):
        return QCoreApplication.translate("Superpixel Processing Plugin - SLIC Algorithm", text)

    def displayName(self):
        return self.tr("Superpixelplugin - SLIC Algorithm")

    def group(self):
        return self.tr("Superpixelplugin")#Superpixelalgorithms")

    def groupId(self):
        return "superpixelplugin" # algorithms"

    def shortHelpString(self):
        return self.tr("The SLIC Superpixel Algorithm, originally "
                       "proposed by ACHANTA et al. 2010, see: Achanta, R. et al. (2010). SLIC Superpixels "
                       "(EPFL Technical Report, https://infoscience.epfl.ch/record/149300) in the implementation of "
                       "Scikit-image, see: van der Walt, S., Schönberger, J.L., Nunez-Iglesias, J., & Boulogne, F., et al. (2014). "
                       "Scikit-image: Image Processing in Python. PeerJ, 2, e453. DOI 10.7717/peerj.453")
    def helpUrl(self):
        return "https://qgis.org"

    def createInstance(self):
        return SuperpixelProcessingPluginSLIC()

    def initAlgorithm(self, config=None, **kwargs):
        # See: https://docs.qgis.org/3.16/en/docs/user_manual/processing/scripts.html

        """
        # See: https://gis.stackexchange.com/questions/377793/how-to-group-parameters-in-pyqgis-processing-plugin
        param = QgsProcessingParameterString(
            self.NAME_OF_THE_PARAMETER,
            tr('Your label'),
            optional=False,
            defaultValue='If any default)

        # The line below will take default flags already there and adds the Advanced one
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        :param **kwargs:
        """

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_RASTER_A,
                #self.tr("Input Raster A")))  #, None, False))
                self.tr("Input Raster A"), None, False))

        # self.addParameter(QgsProcessingParameterRasterLayer(
        #    self.INPUT_RASTER_B,
        #    self.tr("Input Raster B"), None, False))



        #self.addParameter(
        #    QgsProcessingParameterFeatureSource(
        #        self.INPUT_RASTER_A,
        #        self.tr('Input layer'),
        #        [QgsProcessing.TypeRaster]#VectorAnyGeometry]
        #    )
        #)



        # self.addParameter(QgsProcessingParameterNumber(
        #    self.INPUT_DOUBLE,
        #    self.tr("Input Double"),
        #    QgsProcessingParameterNumber.Double,
        #    QVariant(1.0)))

        self.addParameter(QgsProcessingParameterNumber(
            self.NSEGMENTS,
            self.tr("Number of Segments"),
            QgsProcessingParameterNumber.Integer,
            QVariant(250)))

        self.addParameter(QgsProcessingParameterNumber(
            self.COMPACTNESS,
            self.tr("Compactness"),
            QgsProcessingParameterNumber.Integer,
            QVariant(10)))

        self.addParameter(QgsProcessingParameterNumber(
            self.SIGMA,
            self.tr("Sigma"),
            QgsProcessingParameterNumber.Double,
            QVariant(1.0)))

        self.addParameter(QgsProcessingParameterNumber(
            self.STARTLABEL,
            self.tr("Start Label"),
            #QgsProcessingParameterNumber.Integer,
            #QVariant(1.0)
            defaultValue=1.0,
            minValue=1, # 1 ist Double, 0 ist Integer
            maxValue=1000000000,
            type=1
            ))

        self.addParameter(QgsProcessingParameterRasterDestination(  # RASTER OUTPUT
            self.OUTPUT_RASTER_A,
            self.tr("Output Raster Segments"),
            None, False))

        # self.addParameter(QgsProcessingParameterRasterDestination(
        #    self.OUTPUT_RASTER_B,
        #    self.tr("Output Raster B"),
        #    None, False))

    def processAlgorithm(self, parameters, context, feedback, **kwargs):
        #raster_a = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER_A, context)
        #raster_a = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER_A, context)
        # raster_b = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER_B, context)

        #  Experiment, ob AsSource oder AsRasterLayer...
        # TODO raster_a = self.parameterAsSource(parameters, self.INPUT_RASTER_A, context)
        self.raster_a = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER_A, context)
        # !!!! JETZT HIER GANZ WICHTIG DIESER SCHRITT::
        # Code snippet verändert nach: https://gis.stackexchange.com/questions/357074/save-numpy-array-as-raster-in-a-processing-toolbox-qgis3
        # set provider to raster input as a dataProvider
        #provider = self.raster_a.dataProvider()
        # get the filepath of the input raster as a string
        #self.filepath_raster_a = str(provider.dataSourceUri())
        self.filepath_raster_a = str(self.raster_a.dataProvider().dataSourceUri())
        # ~~~~~

        # See filetypes: https://qgis.org/pyqgis/3.16/core/QgsProcessingAlgorithm.html
        # double_val = self.parameterAsDouble(parameters, self.INPUT_DOUBLE,context)
        self.nSegments_slic = self.parameterAsInt(parameters, self.NSEGMENTS, context)
        self.compactness_slic = self.parameterAsInt(parameters, self.COMPACTNESS, context)
        self.sigma_slic = self.parameterAsDouble(parameters, self.SIGMA, context)
        self.startLabel_slic = self.parameterAsInt(parameters, self.STARTLABEL, context)

        output_path_raster_a = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER_A, context)
        # output_path_raster_b = self.parameterAsOutputLayer(parameters, self.OUTPUT_RASTER_B, context)

        # DO SOME CALCULATION

        # Nachfolgender code ist angepasst aus dem tutorial von:
        # https://opensourceoptions.com/blog/python-geographic-object-based-image-analysis-geobia/
        driverTiff = gdal.GetDriverByName('GTiff')  # GDAL assign GTiff file driver (besser rasterio nehmen?)
        # global raster_dataset # set as a global variable

        raster_dataset = gdal.Open(
            #self.inRaster.dataProvider().dataSourceUri())  # use GDAL to open file from inRaster path
            #self.INPUT_RASTER_A.source())#.dataProvider().dataSourceUri())
            # TODO::::
            self.filepath_raster_a)

        self.nbands = raster_dataset.RasterCount  # get number of raster bands
        band_data = []  # create a list for the raster bands
        for i in range(1, self.nbands + 1):  # starting with band as 1
            band = raster_dataset.GetRasterBand(i).ReadAsArray()  # reads each band as ---> np array <---
            band_data.append(band)  # append the band as a np array to the band_data list
        band_data = np.dstack(band_data)  # put all in a single variable as a ---> stack of the bands <---

        # self.progressBar.setValue(10)

        # Check if multiband data:
        # TODO HIER WENN MEHR BÄNDER; DANN
        # (height, width, channels) = img.shape[:3]
        if band_data.shape[-1] > 1: # if more than 1 channel is present in image, than compute gradient image, else pass
            self.multichannel = True
        else:
            self.multichannel = False

        # normalize the raster band values
        # scale image values from 0.0 - 1.0
        self.img_normalized = exposure.rescale_intensity(band_data)

        # self.progressBar.setValue(20)

        # ---> jetzt kommt SLIC <---
        # self.img_normalized ist jetzt normalized (values from 0.0 - 1.0)

        # TODO: update variables???
        # self.setVariables()
        # ~~~~~ NEW ~~~~~~

        # self.progressBar.setValue(30)

        self.segments_slic = slic(image=self.img_normalized,
                                  n_segments=self.nSegments_slic,
                                  compactness=self.compactness_slic,
                                  sigma=self.sigma_slic,
                                  start_label=self.startLabel_slic,
                                  multichannel=self.multichannel)  # =True  # TODO: eventuell noch checkbox einbauen?
        # )  # max_iter = 10 standard # argument multichannel = true standard!!!

        # self.progressBar.setValue(80)

        # ---> save segments to raster <----
        # segments_fn = self.outRaster  # to get the name from the input field or picker#

        segments_ds = driverTiff.Create(output_path_raster_a, # TODO  self.OUTPUT_RASTER_A,  # self.outRaster,  # segments_fn,
                                        raster_dataset.RasterXSize,
                                        raster_dataset.RasterYSize,
                                        1,
                                        gdal.GDT_Float32)
        segments_ds.SetGeoTransform(raster_dataset.GetGeoTransform())  # transform
        segments_ds.SetProjection(raster_dataset.GetProjectionRef())  # assign the CRS
        segments_ds.GetRasterBand(1).WriteArray(self.segments_slic)  # hier wird segments geschrieben
        segments_ds = None

        """
        results = {}
        results[self.OUTPUT_RASTER_A] = output_path_raster_a
        # results[self.OUTPUT_RASTER_B] = output_path_raster_b
        return results
        """
        return {self.OUTPUT_RASTER_A: output_path_raster_a}
