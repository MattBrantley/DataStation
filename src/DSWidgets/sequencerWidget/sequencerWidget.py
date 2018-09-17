from PyQt5.Qt import *
import pyqtgraph as pg # This library gives a bunch of FutureWarnings that are unpleasant! Fix for this is in the main .py file header.
from pyqode.core import api, modes, panels
import os, json
from shutil import copyfileobj
import numpy as np
import random
from shutil import copyfile
from src.Constants import DSConstants as DSConstants
from src.DSWidgets.sequencerWidget.eventListWidget import eventListWidget

class sequencerDockWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole

    def __init__(self, mW):
        super().__init__('Sequencer (None)')
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.plotPaddingPercent = 1
        self.plotList = list()
        self.hide()
        self.resize(1000, 800)

        self.xMin = 0
        self.xMax = 1

        self.sequenceNavigator = DSTreeView(self.mW, self)
        self.sequenceView = DSGraphicsLayoutWidget(self.mW, self)
        self.initActionsAndToolbar()
        self.initLayout()

        self.updateToolbarState()

        self.iM.Sequence_Loaded.connect(self.sequenceLoaded)
        self.iM.Sequence_Unloaded.connect(self.sequenceUnloaded)

    def initActionsAndToolbar(self):
        self.newAction = QAction('New', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('New')
        self.newAction.triggered.connect(self.iM.newSequence)

        self.saveAction = QAction('Save', self)
        self.saveAction.setStatusTip('Save')
        self.saveAction.triggered.connect(self.iM.saveSequence)

        self.saveAsAction = QAction('Save As', self)
        self.saveAsAction.setStatusTip('Save As')
        self.saveAsAction.triggered.connect(self.iM.saveSequenceAs)

        self.toggleTree = QToolButton(self)
        self.toggleTree.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons3\css.png')))
        self.toggleTree.setCheckable(True)
        self.toggleTree.setStatusTip('Show/Hide The Sequence Browser')
        self.toggleTree.toggled.connect(self.treeToggled)
        self.toggleTree.toggle()
        
        self.toolbar = QToolBar()
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.saveAsAction)
        
        self.toolbar.addSeparator()

        self.toolbar.addWidget(self.toggleTree)

    def initLayout(self):
        
        self.mainContainer = QMainWindow()
        self.mainContainer.addToolBar(self.toolbar)
        self.sequencerContainer = QSplitter()
        
        self.sequencerContainer.addWidget(self.sequenceNavigator)
        self.sequencerContainer.addWidget(self.sequenceView)

        self.sequencerContainer.setStretchFactor(1, 3)
        self.setWidget(self.mainContainer)
        self.mainContainer.setCentralWidget(self.sequencerContainer)

    def sequenceLoaded(self): #Update when Sequence has been fixed in iM
        self.setWindowTitle('Sequencer (' + os.path.basename(self.iM.currentSequenceURL) + ')')

    def sequenceUnloaded(self):
        self.setWindowTitle('Sequencer (None)')

    def treeToggled(self, checked):
        if(checked):
            self.sequenceNavigator.show()
        else:
            self.sequenceNavigator.hide()

    def updateToolbarState(self):
        self.saveAction.setEnabled(True)
        self.saveAsAction.setEnabled(True)

class DSGraphicsLayoutWidget(pg.GraphicsLayoutWidget):

    def __init__(self, mW, dockWidget):
        super().__init__()
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.hM

        pg.setConfigOptions(antialias=True)
        self.dockWidget = dockWidget
        self.referencePlot = None
        self.plotList = list()
        self.setBackground(QColor(255, 255, 255))

        self.iM.Component_Added.connect(self.addNewPlot) #addPlot is reserved by pyqtgraph!
        self.iM.Component_Removed.connect(self.removePlot)

    def addNewPlot(self, instrument, component):
        if(component.Get_Custom_Field('sequencerSettings') is None):
            component.Set_Custom_Field('sequencerSettings', {'show': True})

        settings = component.Get_Custom_Field('sequencerSettings')
        if(settings['show'] is True):
            self.nextRow()
            plot = DSPlotItem(self.mW, self, component)
            self.plotList.append(plot)

            if(len(self.plotList) == 1):
                self.referencePlot = plot
            else:
                plot.plotItem.setXLink(self.referencePlot.plotItem)
            self.plotList.append(plot)

    def removePlot(self, instrument, component):
        for plot in self.plotList:
            if(plot.component is component):
                print('found the one to remove')
        print('could not find the one to remove')

    def findPlotByMousePos(self, pos):
        plotsInRange = list()
        for plot in self.plotList:
            # Okay - so there is a glitch in pyqtgraph that adjustes the offset for other widgets in the scene by offsetting the bounding QRect
            # into the plot area (it seems to do this TWICE). Because the sequencer browser is causing this - we are adjusting the QRect collision
            # area to account for this. It's not pretty but it works.
            sequenceNavigatorWidth = self.dockWidget.sequenceNavigator.width()
            adjViewGeometry = plot.plotItem.getViewBox().screenGeometry().adjusted(-sequenceNavigatorWidth, 0, sequenceNavigatorWidth, 0)
            if(adjViewGeometry.contains(pos)):
                plotsInRange.append(plot)
        return plotsInRange

    def mouseDoubleClickEvent(self, event):
        if(event.buttons() == Qt.LeftButton):
            super().mouseDoubleClickEvent(event)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
        selectedPlots = self.findPlotByMousePos(event.globalPos())
        if selectedPlots:
            selectedPlots[0].toggleEditWidget(event.globalPos())

    def mousePressEvent(self, event):
        
        if(event.buttons() == Qt.RightButton):
            event.accept()
            selectedPlots = self.findPlotByMousePos(event.globalPos())
            if (len(selectedPlots) > 0):
                selectedPlots[0].toggleEditWidget(event.globalPos())
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if(event.button() == 2):
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if(event.buttons() & Qt.RightButton):
            event.accept()
        else:
            super().mouseMoveEvent(event)

class DSPlotItem(QObject):
    plotPaddingPercent = 1

    def __init__(self, mW, plotLayout, comp):
        super().__init__()

        self.mW = mW
        self.component = comp
        self.plotLayout = plotLayout
        self.plotItem = plotLayout.addPlot()

        self.sequencerEditWidget = eventListWidget(mW, plotLayout.dockWidget, comp)
    
    def toggleEditWidget(self, eventPos):
        self.sequencerEditWidget.move(eventPos + QPoint(2, 2))
        if(self.sequencerEditWidget.isHidden()):
            self.sequencerEditWidget.updateTitle()
            self.sequencerEditWidget.show()
        else:
            self.sequencerEditWidget.hide()

    def updatePlot(self):
        data = self.component.parentPlotSequencer()
        self.xMin, self.xMax = self.component.iM.mW.sequencerDockWidget.getSequenceXRange()
        if(data is not None):
            self.plotItem.clear()
            if(data.ndim < 2):
                startHub = np.array([-900000, data[1]])
                endHub = np.array([900000, data[1]])
                data = np.vstack((startHub, data))
                data = np.vstack((data, endHub))
                xMin = 0
                xMax = 1
                
            data = self.formatData(data, self.xMin, self.xMax)

            yDelta = data[:,1].max() - data[:,1].min()
            yPadding = yDelta*self.plotPaddingPercent/100

            self.plotItem.clear()
            self.plotItem.plot(x=data[:,0], y=data[:,1], pen = QColor(0, 0, 0))

            self.plotItem.autoRange()
            self.component.iM.mW.sequencerDockWidget.redrawSequence()

    def plot(self, showXAxis, xMinIn, xMaxIn):
        data = self.component.parentPlotSequencer()
        if(data is None):
            data = np.array([[0,0], [1,0]])

        if(data is not None):
            data2 = self.formatData(data, xMinIn, xMaxIn)
            data = data2

            yDelta = data[:,1].max() - data[:,1].min()
            if(yDelta < 1):
                yDelta = 1
            yPadding = yDelta*self.plotPaddingPercent/100

            yMin = data[:,1].min()
            if(yMin > 0):
                yMin = 0 - yPadding
            else:
                yMin = yMin - yPadding

            yMax = data[:, 1].max()
            if(yMax < 1):
                yMax = 1 + yPadding
            else:
                yMax = yMax + yPadding

            self.plotItem.clear()
            self.plotItem.plot(x=data[:,0], y=data[:,1], pen = self.plotLayout.sequencePLT1Color)
            self.plotItem.setLimits(xMin=xMinIn, xMax=xMaxIn, yMin=yMin, yMax=yMax)

        self.plotItem.setMouseEnabled(x=True, y=False)
        self.plotItem.setLabels(bottom='Time (s)', left='voltage')
        if(showXAxis):
            self.plotItem.showAxis('bottom', True)
            self.plotItem.showLabel('bottom', True)
        else:
            self.plotItem.showAxis('bottom', False)
            self.plotItem.showLabel('bottom', False)
        self.plotItem.setLabel('left', self.comp.Get_Standard_Field('name'))
        #self.plotItem.setDownsampling(ds=True, auto=True, mode='peak') #mode='peak' produces strange results with large gaps in data
        #self.plotItem.setClipToView(True)
        axis = self.plotItem.getAxis('bottom')
        
    def formatData(self, data, xMin, xMax):
        #print('START')
        #print(data)
        if(data[:,0].min() > xMin):
            dataStart = data[:,0].min()
            gapX = np.arange(xMin, dataStart, 0.001)
            gapY = np.add(np.zeros(len(gapX)), data[0, 1])
            minStump = np.vstack((gapX, gapY)).transpose()
            #minStump = [xMin, data[0, 1]]
            data = np.vstack((minStump, data))
        if(data[:,0].max() < xMax):
            dataEnd = data[:,0].max()
            gapX = np.arange(dataEnd, xMax, 0.001)
            gapY = np.add(np.zeros(len(gapX)), data[-1, 1])
            maxStump = np.vstack((gapX, gapY)).transpose()
            #maxStump = [xMax, data[-1, 1]]
            data = np.vstack((data, maxStump))
        #print('RESULT')
        #print(data)
        return data

    def xRangeUpdate(self, xMinTest, xMaxTest):
        if(xMinTest < self.xMin):
            xMinOut = xMinTest
            self.xMin = xMinOut
        else:
            xMinOut = self.xMin

        if(xMaxTest > self.xMax):
            xMaxOut = xMaxTest
            self.xMax = xMaxOut
        else:
            xMaxOut = self.xMax

        return self.padSequenceXRange(xMinOut, xMaxOut)

    def getSequenceXRange(self):
        globalxMax = 0
        globalxMin = 1
        for plotTemp in self.plots:
            data = plotTemp.component.parentPlotSequencer()
            if(data is not None):
                xMax = data[:, 0].max()
                if(xMax > globalxMax):
                    globalxMax = xMax
                xMin = data[:, 0].min()
                if(xMin < globalxMin):
                    globalxMin = xMin

        return globalxMin, globalxMax

    def padSequenceXRange(self, xMin, xMax):
        distance = xMax-xMin
        xMinOut = xMin - (self.plotPaddingPercent*distance/100)
        xMaxOut = xMax + (self.plotPaddingPercent*distance/100)
        return xMinOut, xMaxOut

    def redrawSequence(self):
        self.xMin, self.xMax = self.getSequenceXRange()
        xMinPad, xMaxPad = self.padSequenceXRange(self.xMin, self.xMax) 
        plotCounter = len(self.plots)
        for plotTemp in self.plots:
            plotCounter = plotCounter - 1
            if(plotCounter == 0):
                plotTemp.plot(True, self.xMin, self.xMax)
            else:
                plotTemp.plot(False, self.xMin, self.xMax)

############################################################################################
##################################### TREE VIEW WIDGET #####################################

class DSNewFileDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.scriptType = QComboBox()
        self.scriptType.setWindowTitle('New Sequence..')
        self.scriptType.addItem('Display')
        self.scriptType.addItem('Export')
        self.scriptType.addItem('Generator')
        self.scriptType.addItem('Import')
        self.scriptType.addItem('Interact')
        self.scriptType.addItem('Operation')

        self.layout.addWidget(self.scriptType)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    @staticmethod
    def newFile():
        dialog = DSNewFileDialog()
        result = dialog.exec_()
        return (result == QDialog.Accepted)

class DSEditorFSModel(QFileSystemModel):
    def __init__(self):
        super().__init__()
        self.setReadOnly(False)

    def headerData(self, section, orientation, role):
        if section == 0 and role == Qt.DisplayRole:
            return "Sequences"
        else:
            return super(QFileSystemModel, self).headerData(section, orientation, role)

class DSTreeView(QTreeView):
    def __init__(self, dockWidget, mW):
        super().__init__()
        self.dockWidget = dockWidget
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.rightClick)

        self.fileSystem = DSEditorFSModel()
        self.fsRoot = self.iM.sequencesDir
        self.fsIndex = self.fileSystem.setRootPath(self.fsRoot)  #This is a placeholder - will need updating.

        self.setModel(self.fileSystem)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setRootIndex(self.fsIndex)
        self.doubleClicked.connect(self.doubleClickedAction)
        self.hideColumn(1)
        self.hideColumn(2)
        self.hideColumn(3)

    def rightClick(self, point):
        idx = self.mapToGlobal(point)

        item = self.selectionModel().selectedIndexes()
        if(os.path.isdir(self.fileSystem.filePath(item[0]))):        #Don't show menu on folders
            return

        openAction = QAction('Open', self)
        openAction.triggered.connect(lambda: self.open(self.fileSystem.filePath(item[0])))

        deleteAction = QAction('Delete', self)
        deleteAction.triggered.connect(lambda: self.delete(self.fileSystem.filePath(item[0])))

        duplicateAction = QAction('Duplicate', self)
        duplicateAction.triggered.connect(lambda: self.duplicate(self.fileSystem.filePath(item[0])))

        menu = QMenu(self)
        menu.addAction(openAction)
        menu.addAction(deleteAction)
        menu.addAction(duplicateAction)
        menu.exec(idx)

    def doubleClickedAction(self, index):
        item = self.fileSystem.fileInfo(index)
        filePath = item.filePath()
        fileExt = os.path.splitext(item.fileName())[1]
        if(fileExt == '.sqpy'):
            self.openSequence(filePath)

    def open(self, item):
        self.iM.Load_Sequence(item)

    def delete(self, item):
        os.remove(item)

    def duplicate(self, item):
        tempPath = os.path.splitext(item)[0] + '_copy' + os.path.splitext(item)[1]
        tempNum = 1
        while(os.path.isfile(tempPath)):
            tempNum = tempNum + 1
            tempPath = os.path.splitext(item)[0] + '_copy' + str(tempNum) + os.path.splitext(item)[1]
        
        copyfile(item, tempPath)
