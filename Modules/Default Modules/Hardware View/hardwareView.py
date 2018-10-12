from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, time
from src.Constants import DSConstants as DSConstants
from hardwareListWidget import hardwareListWidget
from gridViewWidget import gridViewWidget
from src.Managers.InstrumentManager.Sockets import AOSocket, AISocket, DOSocket, DISocket
from src.Managers.HardwareManager.Sources import AOSource, AISource, DOSource, DISource
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class hardwareView(DSModule):
    Module_Name = 'Hardware View'
    Module_Flags = []

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM

    def configureWidget(self, window):

        #self.hide()
        self.window = window
        self.resize(800, 800)
        self.toolbar = QToolBar()

        self.mainContainer = QMainWindow()
        self.mainContainer.addToolBar(self.toolbar)

        self.hardwareWidget = hardwareListWidget(self, self.ds)
        self.connectorGridWidget = gridViewWidget(self, self.ds)
        self.filtersWidget = QWidget()
        self.driversWidget = QWidget()

        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(self.hardwareWidget, "Attached Hardware")
        self.tabWidget.addTab(self.connectorGridWidget, "Connection Grid")
        #self.tabWidget.addTab(self.filtersWidget, "Filters")
        #self.tabWidget.addTab(self.driversWidget, "Hardware Drivers")
        self.mainContainer.setCentralWidget(self.tabWidget)
        self.setWidget(self.mainContainer)
