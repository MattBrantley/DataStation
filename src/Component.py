from PyQt5.Qt import *
import os
from Constants import DSConstants as DSConstants

class Component():
    name = ''
    componentType = 'Default Component'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    layoutGraphicSrc = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'User Componeonts\img\default.png')
    mainWindow = None

    def __init__(self, instrumentManager, **kwargs):
        self.instrumentManager = instrumentManager
        self.name = kwargs.get('name', self.componentType)

    def setupWidgets(self):
        self.mainWindow = self.instrumentManager.mainWindow
        self.configWidget = ComponentConfigWidget(self)

    def onCreationParent(self):
        self.instrumentManager.mainWindow.postLog('Added New Component to Instrument: ' + self.componentType, DSConstants.LOG_PRIORITY_MED)
        self.onCreation()

    def onCreation(self):
        pass

    def hideConfigWindow(self):
        self.configWidget.hide()

    def onLeftClick(self, eventPos):
        self.configWidget.move(eventPos + QPoint(2, 2))
        if(self.configWidget.isHidden()):
            self.configWidget.show()
        else:
            self.configWidget.hide()

class ComponentConfigWidget(QDockWidget):
    doNotAutoPopulate = True

    def __init__(self, compParent):
        super().__init__('Config: ' + compParent.name, parent=compParent.instrumentManager.instrumentWidget)
        self.compParent = compParent
        self.setFeatures(QDockWidget.DockWidgetClosable)
        self.setFloating(True)
        self.hide()