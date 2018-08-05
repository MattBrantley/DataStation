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

    def __init__(self):
        self.plotLayoutWidget = pg.GraphicsLayoutWidget()
        self.plotLayoutWidget.setBackground(self.sequenceBGColor)

    def addPlot(self, name):
        self.plotLayoutWidget.nextRow()
        plot = DSPlotItem(self, name)
        self.plots.append(plot)

        if(len(self.plots) == 1):
            self.referencePlot = plot
        else:
            plot.plotItem.setXLink(self.referencePlot.plotItem)

        return plot

class DSPlotItem():

    def __init__(self, plotLayout, name):
        self.plotLayout = plotLayout
        self.plotItem = plotLayout.plotLayoutWidget.addPlot()
        self.name = name
        self.LODs = []
        self.data = []
        self.pen = []
        self.xMax = 0
        self.xMin = 0
        self.numPoints = 0
        self.LODing = True
    
    def plot(self, data):
        self.xMax = data.size #np.max(data)
        self.xMin = 0 #np.min(data)
        self.numPoints = data.size
        self.data = data

        self.plotItem.plot(y=data, pen = self.plotLayout.sequencePLT1Color)
        self.plotItem.setLimits(xMin=0, xMax=data.size)
        self.plotItem.setMouseEnabled(x=True, y=False)
        self.plotItem.showAxis('bottom', False)
        self.plotItem.setLabel('left', self.name)
        self.plotItem.setDownsampling(ds=True, auto=True, mode='peak')
        self.plotItem.setClipToView(True)
        axis = self.plotItem.getAxis('bottom')
        #self.plotItem.sigXRangeChanged.connect(lambda: self.checkLOD(axis.range))
        
    def checkLOD(self, range):
        xRange = self.xMax-self.xMin
        xRangeView = range[1]-range[0]
        xRangeRatio = xRangeView/xRange
        xPoints = self.numPoints*xRangeRatio
        print([xRangeRatio, '||', xPoints, '||'])

    def report(self):
        #self.plotItem.setLabel('left', random.choice("abcde"))

        print("SHIT")

    def calcLODs(self):
        pass


class sequencerDockWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole

    def __init__(self, mainWindow):
        super().__init__('Sequencer')
        self.mainWindow = mainWindow
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

        self.sequenceView = DSGraphicsLayout()
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

        size = 1000000
        p1 = self.sequenceView.addPlot("Name 1")
        p1.plot(np.random.normal(size=size))

        p2 = self.sequenceView.addPlot("Name 2")
        p2.plot(np.random.normal(size=size))

        p3 = self.sequenceView.addPlot("Name 3")
        p3.plot(np.random.normal(size=size))

        p4 = self.sequenceView.addPlot("Name 4")
        p4.plot(np.random.normal(size=size))

    def redrawSequence(self):
        npoints = 100000

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