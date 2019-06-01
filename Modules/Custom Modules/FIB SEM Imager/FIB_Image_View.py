from PyQt5.Qt import *
from PyQt5.QtCore import *
import pyqtgraph as pg
from pyqtgraph.graphicsItems.GradientEditorItem import Gradients
import numpy as np
import os

class FIB_Image_View(pg.ImageView):
    def __init__(self, module, parent=None):
        super().__init__(parent)

        self.module = module
        self.ds = module.ds
        self.iM = module.ds.iM

        spectrumColormap =  pg.ColorMap(*zip(*Gradients["thermal"]["ticks"]))
        self.setColorMap(spectrumColormap)
        # self.setColorMap(pg.colormap.)
        self.show()
        #self.view = self.addViewBox()

    def measurementPacketRecieved(self, instrument, component, socket, packet):
        if component is self.module.configData['DetectorComponent']:
            for measurement in packet.Get_Measurements():
                data = measurement.yData().view()
                data = np.reshape(data, (int(self.module.progData['YResolution']), int(data.shape[0]/self.module.progData['YResolution'])))
                self.setImage(data)
