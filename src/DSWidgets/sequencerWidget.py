from PyQt5.Qt import *
import pyqtgraph as pg # This library gives a bunch of FutureWarnings that are unpleasant! Fix for this is in the main .py file header.
from pyqode.core import api, modes, panels
import os
from shutil import copyfileobj
import numpy as np
import random

class DSGraphicsLayout():
    sequenceBGColor = QColor(255, 255, 255) #Intended to be user-editable at a future date.
    sequencePLT1Color = QColor(0, 0, 0) #Intended to be user-editable at a future date. This is the programming plot
    sequencePLT2Color = QColor(255, 0, 0) #Intended to be user-editable at a future date. This is the readback plot
    plots = list()
    referencePlot = None

    def __init__(self, dockWidget):
        self.dockWidget = dockWidget
        self.plotLayoutWidget = DSGraphicsLayoutWidget(self)
        self.plotLayoutWidget.setBackground(self.sequenceBGColor)

    def addPlot(self, name, comp):
        self.plotLayoutWidget.nextRow()
        plot = DSPlotItem(self, name, comp)
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

class DSPlotItem():
    plotPaddingPercent = 1

    def __init__(self, plotLayout, name, comp):
        self.component = comp
        self.plotLayout = plotLayout
        self.plotItem = plotLayout.plotLayoutWidget.addPlot()
        self.name = name
        self.LODs = []
        self.data = []
        self.pen = []
    
    def plot(self, showXAxis, xMinIn, xMaxIn):
        data = self.component.plotSequencer()
        data2 = self.formatData(data, xMinIn, xMaxIn)
        self.data = data2

        yDelta = self.data[:,1].max() - self.data[:,1].min()
        yPadding = yDelta*self.plotPaddingPercent/100

        self.plotItem.plot(x=self.data[:,0], y=self.data[:,1], pen = self.plotLayout.sequencePLT1Color)
        self.plotItem.setLimits(xMin=xMinIn, xMax=xMaxIn, yMin=self.data[:,1].min()-yPadding, yMax=self.data[:,1].max()+yPadding)
        self.plotItem.setMouseEnabled(x=True, y=False)
        self.plotItem.setLabels(bottom='Time (s)', left='voltage')
        if(showXAxis):
            self.plotItem.showAxis('bottom', True)
            self.plotItem.showLabel('bottom', True)
        else:
            self.plotItem.showAxis('bottom', False)
            self.plotItem.showLabel('bottom', False)
        self.plotItem.setLabel('left', self.name)
        self.plotItem.setDownsampling(ds=True, auto=True, mode='peak')
        #self.plotItem.setClipToView(True)
        axis = self.plotItem.getAxis('bottom')
        
    def formatData(self, data, xMin, xMax):
        if(data[:,0].min() > xMin):
            minStump = [xMin, data[data[:,0].argmin(), 1]]
            data = np.vstack((minStump, data))
        if(data[:,0].max() < xMax):
            maxStump = [xMax, data[data[:,0].argmax(), 1]]
            data = np.vstack((data, maxStump))

        return data

    def report(self):
        pass

    def calcLODs(self):
        pass

class sequencerDockWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole
    plots = []
    plotPaddingPercent = 1

    def __init__(self, mainWindow):
        super().__init__('Sequencer')
        self.mainWindow = mainWindow
        self.instrumentManager = mainWindow.workspace.DSInstrumentManager
        self.hide()
        self.resize(1000, 800)
        self.fileSystem = DSEditorFSModel()
        self.fsIndex = self.fileSystem.setRootPath(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))  #This is a placeholder - will need updating.

        self.toolbar = QToolBar()
        
        self.mainContainer = QMainWindow()
        self.mainContainer.addToolBar(self.toolbar)
        self.sequencerContainer = QSplitter()

        self.sequenceNavigator = DSTreeView(self, self.fileSystem)
        self.initSequenceNavigator()
        self.initActions()
        self.initToolbar()

        self.sequenceView = DSGraphicsLayout(self)
        #self.sequenceView = pg.GraphicsLayoutWidget()
        self.initSequenceView()
        
        self.sequencerContainer.addWidget(self.sequenceNavigator)
        self.sequencerContainer.addWidget(self.sequenceView.plotLayoutWidget)

        self.sequencerContainer.setStretchFactor(1, 3)
        self.setWidget(self.mainContainer)
        self.mainContainer.setCentralWidget(self.sequencerContainer)
        self.updateToolbarState()

        self.redrawSequence()

    def prepareLODs(self, data):
        pass

    def initSequenceView(self):
        pg.setConfigOptions(antialias=True)
        self.updatePlotList()

    def isPlotListDirty(self):
        return True
        # This function is a placeholder for future optimizations - for stopping redraw on EVERY param change when
        # not necessary.

    def updatePlotList(self):
        if(self.isPlotListDirty()):
            self.sequenceView.clearPlots()
            if(self.instrumentManager.currentInstrument is not None):
                for component in self.instrumentManager.currentInstrument.components:
                    if(component.compSettings['showSequencer'] is True):
                        plotHolder = self.sequenceView.addPlot(component.compSettings['name'], component)
                        if(component.valid is True):
                            pass
                            #plotHolder.plotItem.getViewBox().setBackgroundColor(None)
                        else:
                            plotHolder.plotItem.getViewBox().setBackgroundColor(QColor(255,0,0,alpha=100))
                        self.plots.append(plotHolder)

            self.redrawSequence()

    def getSequenceXRange(self):
        globalxMax = 0
        globalxMin = 1
        for plotTemp in self.plots:
            data = plotTemp.component.plotSequencer()
            xMax = data[:, 0].max()
            if(xMax > globalxMax):
                globalxMax = xMax
            xMin = data[:, 0].min()
            if(xMin < globalxMin):
                globalxMin = xMin

        return globalxMin, globalxMax

    def redrawSequence(self):
        xMin, xMax = self.getSequenceXRange()
        distance = xMax-xMin
        xMin = xMin - (self.plotPaddingPercent*distance/100)
        xMax = xMax + (self.plotPaddingPercent*distance/100)

        plotCounter = len(self.plots)
        for plotTemp in self.plots:
            plotCounter = plotCounter - 1
            if(plotCounter == 0):
                plotTemp.plot(True, xMin, xMax)
            else:
                plotTemp.plot(False, xMin, xMax)

    def initToolbar(self):
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.saveAsAction)
        self.toolbar.addAction(self.saveAllAction)
        
        self.toolbar.addSeparator()

        self.toolbar.addWidget(self.toggleTree)

    def initSequenceNavigator(self):
        self.sequenceNavigator.setModel(self.fileSystem)
        self.sequenceNavigator.setDragEnabled(True)
        self.sequenceNavigator.setAcceptDrops(True)
        self.sequenceNavigator.setDefaultDropAction(Qt.MoveAction)
        self.sequenceNavigator.setRootIndex(self.fsIndex)
        self.sequenceNavigator.doubleClicked.connect(self.doubleClicked)
        self.sequenceNavigator.hideColumn(1)
        self.sequenceNavigator.hideColumn(2)
        self.sequenceNavigator.hideColumn(3)

    def save(self):
        print("save")
        #curWidget = self.codeEditorTabs.currentWidget()
        #curWidget.file.save()

    def saveAs(self):
        print("save as")
        '''
        curWidget = self.codeEditorTabs.currentWidget()
        if(curWidget):
            text, ok = QInputDialog.getText(self, 'Save As..', 'Filename:', QLineEdit.Normal, curWidget.fileName)
            if(ok):
                if(os.path.isfile(os.path.dirname(curWidget.filePath) + '/' + text)):
                    ans = QMessageBox.question(self, 'Save File..', 'A file with this name already exists. Do you want to overwrite it?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if(ans == QMessageBox.Yes):
                        curWidget.file.save(os.path.dirname(curWidget.filePath) + '/' + text)
                else:
                    curWidget.file.save(os.path.dirname(curWidget.filePath) + '/' + text)
        '''

    def saveAll(self):
        print("save all")
        #for n in range(0, self.codeEditorTabs.count()):
        #    self.codeEditorTabs.widget(n).file.save()

    def new(self):
        result = DSNewFileDialog.newFile()
        print(result)

    def initActions(self):
        self.newAction = QAction('New', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('New')
        self.newAction.triggered.connect(self.new)

        self.saveAction = QAction('Save', self)
        self.saveAction.setStatusTip('Save')
        self.saveAction.triggered.connect(self.save)

        self.saveAsAction = QAction('Save As', self)
        self.saveAsAction.setStatusTip('Save As')
        self.saveAsAction.triggered.connect(self.saveAs)

        self.saveAllAction = QAction('&Save All', self)
        self.saveAllAction.setShortcut('Ctrl+S')
        self.saveAllAction.setStatusTip('Save All')
        self.saveAllAction.triggered.connect(self.saveAll)

        self.toggleTree = QToolButton(self)
        self.toggleTree.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons3\css.png')))
        self.toggleTree.setCheckable(True)
        self.toggleTree.setStatusTip('Show/Hide The Sequence Browser')
        self.toggleTree.toggled.connect(self.treeToggled)
        self.toggleTree.toggle()

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

    def openSequence(self, filePath):
        print("opening path")

    def updateToolbarState(self):
        self.saveAction.setEnabled(True)
        self.saveAsAction.setEnabled(True)
        self.saveAllAction.setEnabled(True)

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
    def __init__(self, parent, model):
        super().__init__()
        self.parent = parent
        self.model = model
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.rightClick)

    def rightClick(self, point):
        idx = self.mapToGlobal(point)

        item = self.selectionModel().selectedIndexes()
        if(os.path.isdir(self.model.filePath(item[0]))):        #Don't show menu on folders
            return

        deleteAction = QAction('Delete', self)
        deleteAction.triggered.connect(lambda: self.delete(self.model.filePath(item[0])))

        duplicateAction = QAction('Duplicate', self)
        duplicateAction.triggered.connect(lambda: self.duplicate(self.model.filePath(item[0])))

        menu = QMenu(self)
        menu.addAction(deleteAction)
        menu.addAction(duplicateAction)
        menu.exec(idx)

    def delete(self, item):
        os.remove(item)

    def duplicate(self, item):
        tempPath = os.path.splitext(item)[0] + '_copy' + os.path.splitext(item)[1]
        tempNum = 1
        while(os.path.isfile(tempPath)):
            tempNum = tempNum + 1
            tempPath = os.path.splitext(item)[0] + '_copy' + str(tempNum) + os.path.splitext(item)[1]

        copyfile(item, tempPath)