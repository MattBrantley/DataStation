from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, time
from src.Constants import DSConstants as DSConstants
from src.DSWidgets.hardwareWidget.hardwareListWidget import hardwareListWidget
from src.DSWidgets.hardwareWidget.gridViewWidget import gridViewWidget
from src.Managers.InstrumentManager.Sockets import AOSocket, AISocket, DOSocket, DISocket
from src.Managers.HardwareManager.Sources import AOSource, AISource, DOSource, DISource

class hardwareWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole

    def __init__(self, mW):
        super().__init__('Hardware')
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM

        self.hide()
        self.resize(800, 800)
        self.toolbar = QToolBar()

        self.mainContainer = QMainWindow()
        self.mainContainer.addToolBar(self.toolbar)

        self.hardwareWidget = hardwareListWidget(self.mW)
        self.connectorGridWidget = gridViewWidget(self.mW)
        self.filtersWidget = QWidget()
        self.driversWidget = QWidget()

        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(self.hardwareWidget, "Attached Hardware")
        self.tabWidget.addTab(self.connectorGridWidget, "Connection Grid")
        self.tabWidget.addTab(self.filtersWidget, "Filters")
        self.tabWidget.addTab(self.driversWidget, "Hardware Drivers")
        self.mainContainer.setCentralWidget(self.tabWidget)
        self.setWidget(self.mainContainer)
