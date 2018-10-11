from PyQt5.Qt import *
import os
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class datastationLogo(DSModule):
    Module_Name = 'DataStation Logo'
    Module_Flags = [mfs.SHOW_ON_CREATION, mfs.FLOAT_ON_CREATION]

    def __init__(self, ds):
        super().__init__(ds)
        self.ds = ds

        #self.hide()
        self.logo_pixmap = QPixmap(os.path.join(self.ds.srcDir, r'DSIcons\DataStation_Full.png'))
        self.logoWidget = QLabel(self)
        self.logoWidget.setPixmap(self.logo_pixmap)
        self.resize(self.logo_pixmap.width(), self.logo_pixmap.height())
        self.setWidget(self.logoWidget)