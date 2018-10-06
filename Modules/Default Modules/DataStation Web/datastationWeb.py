from PyQt5.Qt import *
#from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebEngineWidgets import QWebEngineView
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class datastationWeb(DSModule):
    Module_Name = 'DataStation Web'
    Module_Flags = [mfs.SHOW_ON_CREATION, mfs.FLOAT_ON_CREATION]

    def __init__(self, mW):
        super().__init__(mW)
        #self.setFeatures(self.features() & ~QDockWidget.DockWidgetClosable & ~QDockWidget.DockWidgetMovable & ~QDockWidget.DockWidgetFloatable & ~QDockWidget.DockWidgetVerticalTitleBar)
        self.browser = QWebEngineView()
        self.browser.load(QUrl("http://news.google.com"))

        self.setWidget(self.browser)
