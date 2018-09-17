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
    plots = []
    plotPaddingPercent = 1

    def __init__(self, mW):
        super().__init__('Sequencer (None)')
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.hide()
        self.resize(1000, 800)
        self.fileSystem = DSEditorFSModel()
        self.fsRoot = self.mW.iM.sequencesDir
        self.fsRoot = os.path.join(self.mW.rootDir, 'sequences')
        self.fsIndex = self.fileSystem.setRootPath(self.fsRoot)  #This is a placeholder - will need updating.

        self.xMin = 0
        self.xMax = 1

        self.sequenceNavigator = DSTreeView(self, self.fileSystem, self.fsIndex)
        self.sequenceView = DSGraphicsLayout(self.mW, self)
        self.initActionsAndToolbar()
        self.initLayout()

        pg.setConfigOptions(antialias=True)

        self.updateToolbarState()

        self.iM.Sequence_Loaded.connect(self.sequenceLoaded)
        self.iM.Sequence_Unloaded.connect(self.sequenceUnloaded)
        self.iM.Component_Added.connect(self.addPlot)

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
        self.sequencerContainer.addWidget(self.sequenceView.plotLayoutWidget)

        self.sequencerContainer.setStretchFactor(1, 3)
        self.setWidget(self.mainContainer)
        self.mainContainer.setCentralWidget(self.sequencerContainer)

    def sequenceLoaded(self): #Update when Sequence has been fixed in iM
        self.setWindowTitle('Sequencer (' + os.path.basename(self.iM.currentSequenceURL) + ')')

    def sequenceUnloaded(self):
        self.setWindowTitle('Sequencer (None)')
        self.redrawSequence()

    def addPlot(self, instrument, component):
        if(component.Get_Custom_Field('sequencerSettings') is None):
            component.Set_Custom_Field('sequencerSettings', {'show': True})

        settings = component.Get_Custom_Field('sequencerSettings')
        if(settings['show'] is True):
            plotHolder = self.sequenceView.addPlot(component.Get_Standard_Field('name'), component)
            self.plots.append(plotHolder)


        self.redrawSequence()

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
            print('counter')
            plotCounter = plotCounter - 1
            if(plotCounter == 0):
                plotTemp.plot(True, self.xMin, self.xMax)
            else:
                plotTemp.plot(False, self.xMin, self.xMax)

    def treeToggled(self, checked):
        if(checked):
            self.sequenceNavigator.show()
        else:
            self.sequenceNavigator.hide()

    def doubleClicked(self, index):
        item = self.fileSystem.fileInfo(index)
        filePath = item.filePath()
        fileExt = os.path.splitext(item.fileName())[1]
        if(fileExt == '.sqpy'):
            self.openSequence(filePath)

    def updateToolbarState(self):
        self.saveAction.setEnabled(True)
        self.saveAsAction.setEnabled(True)

class DSGraphicsLayout():
    sequenceBGColor = QColor(255, 255, 255) #Intended to be user-editable at a future date.
    sequencePLT1Color = QColor(0, 0, 0) #Intended to be user-editable at a future date. This is the programming plot
    sequencePLT2Color = QColor(255, 0, 0) #Intended to be user-editable at a future date. This is the readback plot

    def __init__(self, mW, dockWidget):
        self.dockWidget = dockWidget
        self.plots = list()
        self.referencePlot = None
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.plotLayoutWidget = DSGraphicsLayoutWidget(self)
        self.plotLayoutWidget.setBackground(self.sequenceBGColor)

    def addPlot(self, name, comp):
        self.plotLayoutWidget.nextRow()
        plot = DSPlotItem(self.mW, self, self.dockWidget, name, comp)
        self.plots.append(plot)

        if(len(self.plots) == 1):
            self.referencePlot = plot
        else:
            plot.plotItem.setXLink(self.referencePlot.plotItem)

        return plot

    def clearPlots(self):
        self.plots.clear()
        self.plotLayoutWidget.clear()

class DSGraphicsLayoutWidget(pg.GraphicsLayoutWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def findPlotByMousePos(self, pos):
        plotsInRange = []
        for plot in self.parent.plots:
            # Okay - so there is a glitch in pyqtgraph that adjustes the offset for other widgets in the scene by offsetting the bounding QRect
            # into the plot area (it seems to do this TWICE). Because the sequencer browser is causing this - we are adjusting the QRect collision
            # area to account for this. It's not pretty but it works.
            sequenceNavigatorWidth = self.parent.dockWidget.sequenceNavigator.width()
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
        if (len(selectedPlots) > 0):
            selectedPlots[0].component.onSequencerDoubleClick(event.globalPos())

    def mousePressEvent(self, event):
        
        if(event.buttons() == Qt.RightButton):
            event.accept()
            selectedPlots = self.findPlotByMousePos(event.globalPos())
            if (len(selectedPlots) > 0):
                selectedPlots[0].component.onSequencerDoubleClick(event.globalPos())
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

    def __init__(self, mW, plotLayout, sequencerWidget, name, comp):
        super().__init__()

        self.mW = mW
        self.component = comp
        self.sequencerWidget = sequencerWidget
        self.component.registerPlotItem(self)
        self.plotLayout = plotLayout
        self.plotItem = plotLayout.plotLayoutWidget.addPlot()
        self.name = name
        self.LODs = []
        self.data = []
        self.pen = []
    
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
                self.data = data
                xMin = 0
                xMax = 1
                
            data = self.formatData(data, self.xMin, self.xMax)
            self.data = data

            yDelta = self.data[:,1].max() - self.data[:,1].min()
            yPadding = yDelta*self.plotPaddingPercent/100

            self.plotItem.clear()
            self.plotItem.plot(x=self.data[:,0], y=self.data[:,1], pen = self.plotLayout.sequencePLT1Color)

            self.plotItem.autoRange()
            self.component.iM.mW.sequencerDockWidget.redrawSequence()

    def plot(self, showXAxis, xMinIn, xMaxIn):
        data = self.component.parentPlotSequencer()
        if(data is None):
            data = np.array([[0,0], [1,0]])

        if(data is not None):
            data2 = self.formatData(data, xMinIn, xMaxIn)
            self.data = data2

            yDelta = self.data[:,1].max() - self.data[:,1].min()
            if(yDelta < 1):
                yDelta = 1
            yPadding = yDelta*self.plotPaddingPercent/100

            yMin = self.data[:,1].min()
            if(yMin > 0):
                yMin = 0 - yPadding
            else:
                yMin = yMin - yPadding

            yMax = self.data[:, 1].max()
            if(yMax < 1):
                yMax = 1 + yPadding
            else:
                yMax = yMax + yPadding

            self.plotItem.clear()
            self.plotItem.plot(x=self.data[:,0], y=self.data[:,1], pen = self.plotLayout.sequencePLT1Color)
            self.plotItem.setLimits(xMin=xMinIn, xMax=xMaxIn, yMin=yMin, yMax=yMax)

        self.plotItem.setMouseEnabled(x=True, y=False)
        self.plotItem.setLabels(bottom='Time (s)', left='voltage')
        if(showXAxis):
            self.plotItem.showAxis('bottom', True)
            self.plotItem.showLabel('bottom', True)
        else:
            self.plotItem.showAxis('bottom', False)
            self.plotItem.showLabel('bottom', False)
        self.plotItem.setLabel('left', self.name)
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
    def __init__(self, parent, model, fsIndex):
        super().__init__()
        self.parent = parent
        self.model = model
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.rightClick)

        self.setModel(model)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setRootIndex(fsIndex)
        self.doubleClicked.connect(self.doubleClicked)
        self.hideColumn(1)
        self.hideColumn(2)
        self.hideColumn(3)

    def rightClick(self, point):
        idx = self.mapToGlobal(point)

        item = self.selectionModel().selectedIndexes()
        if(os.path.isdir(self.model.filePath(item[0]))):        #Don't show menu on folders
            return

        openAction = QAction('Open', self)
        openAction.triggered.connect(lambda: self.open(self.model.filePath(item[0])))

        deleteAction = QAction('Delete', self)
        deleteAction.triggered.connect(lambda: self.delete(self.model.filePath(item[0])))

        duplicateAction = QAction('Duplicate', self)
        duplicateAction.triggered.connect(lambda: self.duplicate(self.model.filePath(item[0])))

        menu = QMenu(self)
        menu.addAction(openAction)
        menu.addAction(deleteAction)
        menu.addAction(duplicateAction)
        menu.exec(idx)

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
