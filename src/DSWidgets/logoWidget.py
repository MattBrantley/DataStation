from PyQt5.Qt import *
import os

class logoDockWidget(QDockWidget):
    doNotAutoPopulate = True
    ITEM_GUID = Qt.UserRole

    def __init__(self, mW):
        super().__init__('DataStation')
        self.mW = mW

        #self.hide()
        self.logo_pixmap = QPixmap(os.path.join(self.mW.srcDir, r'DSIcons\DataStation_Full.png'))
        self.logoWidget = QLabel(self)
        self.logoWidget.setPixmap(self.logo_pixmap)
        self.resize(self.logo_pixmap.width(), self.logo_pixmap.height())
        self.setWidget(self.logoWidget)