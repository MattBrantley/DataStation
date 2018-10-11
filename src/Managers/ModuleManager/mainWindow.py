from PyQt5.Qt import *
from src.Managers.ModuleManager.DSWindow import DSWindow
import os, time

class mainWindow(QMainWindow):

    def __init__(self, ds):
        super().__init__(ds)
        self.ds = ds
        self.setWindowTitle('DataStation is Loading..')
        self.centerWindow()
        self.show()

    def centerWindow(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

##### Modules #####
    def transferModule(self, moduleHandler):
        self.addDockWidget(Qt.LeftDockWidgetArea, moduleHandler.modInstance)

    def closeEvent(self, event):
        self.hide()