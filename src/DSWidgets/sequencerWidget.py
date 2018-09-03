from PyQt5.Qt import *
import pyqtgraph as pg # This library gives a bunch of FutureWarnings that are unpleasant! Fix for this is in the main .py file header.
from pyqode.core import api, modes, panels
import os, json
from shutil import copyfileobj
import numpy as np
import random
from shutil import copyfile
from Constants import DSConstants as DSConstants

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
        plot = DSPlotItem(self, self.dockWidget, name, comp)
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

    def __init__(self, plotLayout, sequencerWidget, name, comp):
        self.component = comp
        self.sequencerWidget = sequencerWidget
        self.component.registerPlotItem(self)
        self.plotLayout = plotLayout
        self.plotItem = plotLayout.plotLayoutWidget.addPlot()
        self.name = name
        self.LODs = []
        self.data = []
        self.pen = []

        self.component.Events_Modified.connect(self.updatePlot)
    
    def updatePlot(self):
        data = self.component.parentPlotSequencer()
        self.xMin, self.xMax = self.component.instrumentManager.mW.sequencerDockWidget.getSequenceXRange()
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
            self.component.instrumentManager.mW.sequencerDockWidget.redrawSequence()

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
        self.plotItem.setDownsampling(ds=True, auto=True, mode='peak')
        #self.plotItem.setClipToView(True)
        axis = self.plotItem.getAxis('bottom')
        
    def formatData(self, data, xMin, xMax):
        #print('START')
        #print(data)
        if(data[:,0].min() > xMin):
            #minStump = [xMin, data[data[:,0].argmin(), 1]]
            minStump = [xMin, data[0, 1]]
            data = np.vstack((minStump, data))
        if(data[:,0].max() < xMax):
            #maxStump = [xMax, data[data[:,0].argmax(), 1]]
            maxStump = [xMax, data[-1, 1]]
            data = np.vstack((data, maxStump))
        #print('RESULT')
        #print(data)
        return data

    def report(self):
        pass

    def calcLODs(self):
        pass

class sequencerDockWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole
    plots = []
    plotPaddingPercent = 1

##### HELPER FUNCTIONS #####
    def isPlotListDirty(self):
        return True
        # This function is a placeholder for future optimizations - for stopping redraw on EVERY param change when
        # not necessary.

##### GUI FUNCTIONS #####
    def __init__(self, mW):
        super().__init__('Sequencer (None)')
        self.mW = mW
        self.instrumentManager = mW.instrumentManager
        self.hide()
        self.resize(1000, 800)
        self.fileSystem = DSEditorFSModel()
        self.fsRoot = os.path.abspath(os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), os.path.pardir), 'sequences'))
        self.fsIndex = self.fileSystem.setRootPath(self.fsRoot)  #This is a placeholder - will need updating.

        self.currentSequenceURL = None

        self.xMin = 0
        self.xMax = 1

        self.toolbar = QToolBar()
        
        self.mainContainer = QMainWindow()
        self.mainContainer.addToolBar(self.toolbar)
        self.sequencerContainer = QSplitter()

        self.sequenceNavigator = DSTreeView(self, self.fileSystem)
        self.initSequenceNavigator()
        self.initActions()
        self.initToolbar()

        self.sequenceView = DSGraphicsLayout(self)
        self.initSequenceView()
        
        self.sequencerContainer.addWidget(self.sequenceNavigator)
        self.sequencerContainer.addWidget(self.sequenceView.plotLayoutWidget)

        self.sequencerContainer.setStretchFactor(1, 3)
        self.setWidget(self.mainContainer)
        self.mainContainer.setCentralWidget(self.sequencerContainer)
        self.updateToolbarState()

        self.instrumentManager.Instrument_Modified.connect(self.redrawSequence)

        self.redrawSequence()

    def initSequenceView(self):
        pg.setConfigOptions(antialias=True)
        self.updatePlotList()

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
        if hasattr(self.instrumentManager.mW, 'hardwareWidget'):
            self.instrumentManager.mW.hardwareWidget.drawScene()

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

    def initToolbar(self):
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.saveAsAction)
        
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

    def getSaveData(self):
        saveDataPacket = dict()
        saveDataPacket['instrument'] = self.instrumentManager.currentInstrument.name

        saveData = list()
        count = 1
        for plot in self.plots:
            if(plot.component.sequencerEditWidget is not None):
                packetItem = dict()
                packetItem['name'] = plot.component.compSettings['name']
                packetItem['type'] = plot.component.componentType
                packetItem['compID'] = plot.component.componentIdentifier
                packetItem['uuid'] = plot.component.compSettings['uuid']
                packetItem['events'] = plot.component.sequencerEditWidget.getEventsSerializable()
                saveData.append(packetItem)
            count = count + 1

        saveDataPacket['saveData'] = saveData
        return saveDataPacket

    def save(self):
        if(self.currentSequenceURL is None):
            self.saveAs()
            return

        fileName = os.path.basename(self.currentSequenceURL)
        if(os.path.exists(os.path.join(self.fsRoot, self.instrumentManager.currentInstrument.name)) is False):
            os.mkdir(os.path.join(self.fsRoot, self.instrumentManager.currentInstrument.name))
        saveURL = os.path.join(os.path.join(self.fsRoot, self.instrumentManager.currentInstrument.name), fileName)

        #saveURL = self.currentSequenceURL
        saveData = self.getSaveData()
        self.mW.postLog('Saving Sequence (' + saveURL + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.exists(saveURL)):
            os.remove(saveURL)
        with open(saveURL, 'w') as file:
            json.dump(saveData, file, sort_keys=True, indent=4)
        self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def saveAs(self):
        fname, ok = QInputDialog.getText(self.mW, "Sequence Name", "Sequence Name")
        if(os.path.exists(os.path.join(self.fsRoot, self.instrumentManager.currentInstrument.name)) is False):
            os.mkdir(os.path.join(self.fsRoot, self.instrumentManager.currentInstrument.name))
        saveURL = os.path.join(os.path.join(self.fsRoot, self.instrumentManager.currentInstrument.name), fname + '.dssequence')
        if(ok):
            pass
            #self.instrumentManager.currentInstrument.name = fname
        else:
            return

        if(os.path.exists(saveURL)):
            reply = QMessageBox.question(self.mW, 'File Warning!', 'File exists - overwrite?', QMessageBox.Yes, QMessageBox.No)
            if(reply == QMessageBox.No):
                return

        saveData = self.getSaveData()
        self.mW.postLog('Saving Sequence (' + saveURL + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.exists(saveURL)):
            os.remove(saveURL)
        with open(saveURL, 'w') as file:
            json.dump(saveData, file, sort_keys=True, indent=4)
        self.currentSequenceURL = saveURL
        self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

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
        if(self.instrumentManager.currentInstrument is None):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("No instrument is loaded - cannot load sequence!")
            msg.setWindowTitle("Sequence/Instrument Compatibability Error")
            msg.setStandardButtons(QMessageBox.Ok)

            retval = msg.exec_()
            return

        self.mW.postLog('Loading Sequence (' + filePath + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.isfile(filePath) is True):
            with open(filePath, 'r') as file:
                try:
                    sequenceData = json.load(file)
                    if(self.processSequenceData(sequenceData) is False):
                        self.mW.postLog('Sequence at (' + filePath + ') not loaded - aborting! ', DSConstants.LOG_PRIORITY_HIGH)
                    else:
                        self.currentSequenceURL = filePath
                except ValueError as e:
                    self.mW.postLog('Corrupted sequence at (' + filePath + ') - aborting! ', DSConstants.LOG_PRIORITY_HIGH)
                    return
        if(self.currentSequenceURL is not None):
            self.setWindowTitle('Sequencer (' + os.path.basename(self.currentSequenceURL) + ')')
        else:
            self.setWindowTitle('Sequencer (None)')
        self.mW.workspaceManager.userProfile['sequenceURL'] = filePath
        self.mW.postLog('Finished Loading Sequence!', DSConstants.LOG_PRIORITY_HIGH)

    def processSequenceData(self, data):
        instrument = data['instrument']
        self.instrumentManager.currentInstrument.clearSequenceEvents()
        if(instrument != self.instrumentManager.currentInstrument.name):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("The sequence is for a different instrument (" + instrument + ") than what is currently loaded (" + self.instrumentManager.currentInstrument.name + "). It is unlikely this sequence will load.. Continue?")
            msg.setWindowTitle("Sequence/Instrument Compatibability Warning")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            retval = msg.exec_()
            if(retval == QMessageBox.No):
                return False

        dataSet = data['saveData']
        for datum in dataSet:
            comp = self.instrumentManager.currentInstrument.getComponentByUUID(datum['uuid'])
            if(comp is None):
                self.mW.postLog('Sequence data for comp with uuid (' + datum['uuid'] + ') cannot be assigned! Possibly from different instrument.', DSConstants.LOG_PRIORITY_HIGH)
            else:
                comp.loadSequenceData(datum['events'])
        
        self.redrawSequence()
        return True

    def updateToolbarState(self):
        self.saveAction.setEnabled(True)
        self.saveAsAction.setEnabled(True)

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
        self.parent.openSequence(item)

    def delete(self, item):
        os.remove(item)

    def duplicate(self, item):
        tempPath = os.path.splitext(item)[0] + '_copy' + os.path.splitext(item)[1]
        tempNum = 1
        while(os.path.isfile(tempPath)):
            tempNum = tempNum + 1
            tempPath = os.path.splitext(item)[0] + '_copy' + str(tempNum) + os.path.splitext(item)[1]
        
        copyfile(item, tempPath)