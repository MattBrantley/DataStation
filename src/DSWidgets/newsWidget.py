from PyQt5.Qt import *
#from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebEngineWidgets import QWebEngineView

class newsWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole

    def __init__(self, mainWindow):
        super().__init__('News')
        #self.setFeatures(self.features() & ~QDockWidget.DockWidgetClosable & ~QDockWidget.DockWidgetMovable & ~QDockWidget.DockWidgetFloatable & ~QDockWidget.DockWidgetVerticalTitleBar)
        self.browser = QWebEngineView()
        self.browser.load(QUrl("http://news.google.com"))

        self.setWidget(self.browser)
