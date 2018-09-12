import matplotlib.pyplot as plt
import networkx as nx
import uuid, sys, os, pprint, inspect, time
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QRectF
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

#############################################################################################################

class networkObjectManager():
    def __init__(self, mW, widget):
        self.netObjList = list()
        self.mW = mW
        self.widget = widget

    def addNetObj(self, netObj):
        self.netObjList.append(netObj)
        return self.widget.addNetObject(netObj)

    def addNetSig(self, netObj, netSig):
        self.widget.addNetSig(netObj, netSig)

    def getObjsConnected(self, sigObject):
        resList = list()
        for netObj in self.netObjList:
            netConnList = list()
            for netConn in netObj.netConnList:
                if(netConn.pyqtSignal.__str__() == sigObject.pyqtSignal.__str__()):
                    netConnList.append(netConn)

            if(len(netConnList) != 0):
                resList.append(objSearchRes(netObj, netConnList))
        
        return resList

    def getSigsForObj(self, sigObj):
        resList = list()
        for emitObj in sigObj.parentObj.emitList:
            if(emitObj.pyqtSignal.__str__() == sigObj.pyqtSignal.__str__()):
                resList.append(emitObj.emitFunc)

    def getNodeList(self):
        outList = list()
        for netObj in self.netObjList:
            outList.append(netObj.netUuid)

        return outList

class objSearchRes():
    def __init__(self, netObj, netConns):
        self.netObj = netObj
        self.netConns = netConns

class netObject():
    def __init__(self, nmG, name=''):
        self.nmG = nmG
        self.netName = name
        self.netType = self.__class__.__name__
        self.netUuid = uuid.uuid4()
        self.netSigList = list()
        self.netConnList = list()
        self.emitList = list()

        self.netWidgetItem = self.nmG.addNetObj(self)

    def getNodeName(self):
        return self.netName + '[' + self.netType + ']'

    def nOConnect(self, obj, sigName, connFunc):
        sig = getattr(obj, sigName)
        self.addNetConn(sigName, sig, obj, connFunc)
        sig.connect(connFunc)

    def nOSig(self, sig, sigName):
        sO = signalObject(sig, sigName)
        sO.parentObj = self
        self.netSigList.append(sO)
        self.nmG.addNetSig(self, sO)

    def nOEmit(self, sig, **kwargs):
        emitFunc = inspect.stack()[1][3]
        eO = emitObject(sig, inspect.stack()[1][3])
        self.nmG.widget.onEmit(self.netName, eO)
        self.emitList.append(eO)
        
        sig(**kwargs)


    def addNetConn(self, sigName, sig, netObj, connFunc):
        cO = connObject(sigName, sig, netObj.netUuid, connFunc)
        self.netConnList.append(cO)

class emitObject():
    def __init__(self, pyqtSignal, emitFunc):
        self.pyqtSignal = pyqtSignal
        self.emitFunc = emitFunc

class signalObject():
    def __init__(self, pyqtSignal, sigName):
        self.pyqtSignal = pyqtSignal
        self.signalName = sigName
        self.parentObj = None #The calling class adds this in immediately after instantiation

class connObject():
    def __init__(self, sigName, sig, sigNetUuid, connFunc):
        self.signalName = sigName
        self.pyqtSignal = sig
        self.sigNetGuid = sigNetUuid
        self.connFunc = connFunc

#############################################################################################################

class netWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole
    def __init__(self, mW):
        super().__init__('Debugging')
        self.mW = mW
        self.nmG = networkObjectManager(mW, self)
        self.initLayout()
        self.hide()

    def initLayout(self):
        self.mainWidget = QTabWidget()
        self.setWidget(self.mainWidget)

        self.networkTab = networkWidget(self)
        self.sigDetailTab = signalDetails(self)

        self.mainWidget.addTab(self.networkTab, 'Network View')
        self.mainWidget.addTab(self.sigDetailTab, 'Signals')

    def addNetObject(self, netObject):
        return self.sigDetailTab.treeLeft.addNetObject(netObject)

    def addNetSig(self, netObj, netSig):
        self.sigDetailTab.treeLeft.addSigObject(netObj.netWidgetItem, netSig)

    def onEmit(self, name, emitObject):
        self.networkTab.onEmit(name, emitObject)

class signalDetails(QWidget):
    def __init__(self, dockWidget):
        super().__init__()
        self.dockWidget = dockWidget
        self.nmG = self.dockWidget.nmG
        self.treeLeft = treeLeft(self, self.nmG)
        self.treeRight = treeRight(self, self.nmG)
        self.layout = QHBoxLayout()
        self.splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.splitter)
        self.splitter.addWidget(self.treeLeft)
        self.splitter.addWidget(self.treeRight)
        self.setLayout(self.layout)

##### Signal Trees Widget #####

class dsSignalTree(QTreeWidget):
    def __init__(self, nmG):
        super().__init__()
        self.nmG = nmG

    def setHeader(self, headerText):
        headerItem = QTreeWidgetItem(headerText)
        self.setHeaderItem(headerItem)

    def addNetObject(self, netObject):
        item = QTreeWidgetItem([netObject.netName, netObject.netType])
        item.obj = netObject
        self.addTopLevelItem(item)
        return item

    def addSigObject(self, parItem, sigObject):
        item = QTreeWidgetItem(['', '', sigObject.signalName])
        item.obj = sigObject
        parItem.addChild(item)
        return item

    def addNetConn(self, parItem, connObject):
        item = QTreeWidgetItem(['', '', connObject.connFunc.__name__])
        #item.obj = sigObject
        parItem.addChild(item)
        return item

    def addEmit(self, func):
        item = QTreeWidgetITem('')

class treeLeft(dsSignalTree):
    def __init__(self, widget, nmG):
        super().__init__(nmG)
        self.widget = widget
        self.setHeader(['Name','Type','Signal'])

        self.itemChanged.connect(self.selectionChanged)

    def selectionChanged(self, item, col):
        if(len(self.selectedItems()) == 0):
            self.widget.treeRight.setHeader(['None View: '])
            return

        item = self.selectedItems()[0]
        parent = item.parent()
        if(parent is None): #Class selected
            self.widget.treeRight.drawClass(item.obj)
        else: #Signal selected
            self.widget.treeRight.drawSig(item.obj)

class treeRight(dsSignalTree):
    def __init__(self, widget, nmG):
        super().__init__(nmG)
        self.widget = widget
        self.setHeader(['Name','Type','Signal'])

    def drawClass(self, classObj):
        self.clear()
        self.setHeader(['Class View:','Type','Signal'])

    def drawSig(self, sigObj):
        self.clear()
        self.setHeader(['Signal View:','Type','Function'])
        results = self.nmG.getObjsConnected(sigObj)
        for res in results:
            item = self.addNetObject(res.netObj)
            for netConn in res.netConns:
                self.addNetConn(item, netConn)

        #print(sigObj.parentObj)

    def redraw(self):
        pass

##### Vizsualization Widget #####

class networkWidget(QWidget):
    def __init__(self, dockWidget):
        super().__init__()
        self.dockWidget = dockWidget

        self.netVisWidget = netVisualizationWidget(self)
        self.sigTable = signalHistoryTable(self)

        self.networkLayout = QHBoxLayout()
        self.netSplitter = QSplitter(Qt.Vertical)
        self.networkLayout.addWidget(self.netSplitter)
        self.setLayout(self.networkLayout)

        self.netSplitter.addWidget(self.netVisWidget)
        self.netSplitter.addWidget(self.sigTable)

    def onEmit(self, name, emitObject):
        string = emitObject.pyqtSignal.__str__()
        classType = name + '[' + string.split()[4] + ']'
        self.sigTable.addLine(string.split()[2], classType, emitObject.emitFunc)

    def redraw(self):
        pass

class netVisualizationWidget(QScrollArea):
    def __init__(self, dockWidget):
        super().__init__()
        self.dockWidget = dockWidget
        
        self.transform = QTransform()
        self.view = QGraphicsView()
        self.view.setTransform(self.transform)
        self.scene = netVisualizationScene(self, self.transform)
        self.view.setScene(self.scene)

        self.setWidgetResizable(True)
        self.setWidget(self.view)   
        self.resize(800, 500)

    def resize(self, x, y):
        rect = QRectF(0, 0, x, y)
        self.scene.setSceneRect(rect)

class netVisualizationScene(QGraphicsScene):
    def __init__(self, dockWidget, transform):
        super().__init__()
        self.dockWidget = dockWidget
        self.transform = transform

    def mousePressEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        if(event.buttons() == Qt.LeftButton):
            deltaPoint = event.lastScreenPos() - event.screenPos()
            self.transform.translate(deltaPoint.x(), deltaPoint.y())
            hbar = self.dockWidget.view.horizontalScrollBar()
            hbar.setValue(hbar.value() + deltaPoint.x())
            vbar = self.dockWidget.view.verticalScrollBar()
            vbar.setValue(vbar.value() + deltaPoint.y())

class signalHistoryTable(QTableWidget):
    def __init__(self, dockWidget):
        super().__init__()
        self.dockWidge = dockWidget
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['Time', 'Signal', 'Source', 'Function'])
        self.index = 0

    def addLine(self, source, signal, func):
        self.setRowCount(self.index+1)
        self.setItem(self.index, 0, QTableWidgetItem(time.strftime('%m/%d/%Y %H:%M:%S')))
        self.setItem(self.index, 1, QTableWidgetItem(source))
        self.setItem(self.index, 2, QTableWidgetItem(signal))
        self.setItem(self.index, 3, QTableWidgetItem(func))
        self.index += 1

#############################################################################################################
"""
from DSWidgets.networkViewWidget import netObject



    class editorWidget(netObject, QDockWidget):
        ITEM_GUID = Qt.UserRole

        def __init__(self, mW):
            netObject.__init__(self, mW.nmG, '')
            QDockWidget.__init__(self, "Code Editor")




            self.nOSig(self.Config_Modified, 'Config_Modified')




        Timely.nOConnect(Scholar, 'sig1', Timely.func1)



        self.nOEmit(self.Trigger_Modified, **kwargs)



class mainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.netWidget = netWidget(self)
        self.addDockWidget(Qt.TopDockWidgetArea, self.netWidget)
        self.nmG = self.netWidget.nmG
        self.show()
        self.testStuff()

    def testStuff(self):
        Marlin = testObject(self, 'Marlin')
        Argue = testObject(self, 'Argue')
        Money = testObject(self, 'Money')
        Guitar = testObject(self, 'Guitar')
        Scholar = testObject(self, 'Scholar')

        Timely = testObject2(self, 'Timely')

        Timely.nOConnect(Scholar, 'sig1', Timely.func1)
        Timely.nOConnect(Scholar, 'sig1', Timely.func2)

        Scholar.emitFunc1()
"""
#############################################################################################################

"""
class testObject(netObject, QObject):
    sig1 = pyqtSignal()
    
    def __init__(self, mW, name):
        netObject.__init__(self, mW.nmG, name)
        QObject.__init__(self)

        self.nOSig(self.sig1, 'sig1')

    def emitFunc1(self):
        self.nOEmit(self.sig1)

class testObject2(netObject, QObject):
    sig2 = pyqtSignal()
    sig3 = pyqtSignal()
    sig4 = pyqtSignal()
    
    def __init__(self, mW, name):
        netObject.__init__(self, mW.nmG, name)
        QObject.__init__(self)

        self.nOSig(self.sig2, 'sig2')
        self.nOSig(self.sig3, 'sig3')
        self.nOSig(self.sig4, 'sig4')

    def func1(self):
        print('func1!!')
    def func2(self):
        print('func1!!')
"""
#############################################################################################################
