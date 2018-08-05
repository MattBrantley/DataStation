from PyQt5.Qt import *
import pyqtgraph as pg # This library gives a bunch of FutureWarnings that are unpleasant! Fix for this is in the main .py file header.
import os
from shutil import copyfileobj
import numpy as np
import random
from .iView import iView

class instrumentWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole

    def __init__(self, mainWindow, instrManager):
        super().__init__('Instrument View')
        self.instrumentManager = instrManager
        self.mainWindow = mainWindow
        self.hide()
        self.resize(1000, 800)
        self.fileSystem = DSEditorFSModel()
        self.fsIndex = self.fileSystem.setRootPath(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))  #This is a placeholder - will need updating.

        self.toolbar = QToolBar()
        
        self.mainContainer = QMainWindow()
        self.mainContainer.addToolBar(self.toolbar)
        self.instrumentContainer = QSplitter()
        self.toolWidgets = QTabWidget()
        
        self.instrumentNavigator = DSTreeView(self, self.fileSystem)
        self.componentList = componentsList(self)

        self.instrumentView = iView(self)

        self.initInstrumentNavigator()
        self.initActions()
        self.initToolbar()

        self.toolWidgets.addTab(self.instrumentNavigator, "Instruments")
        self.toolWidgets.addTab(self.componentList, "Component Pallet")
        self.instrumentContainer.addWidget(self.toolWidgets)
        self.instrumentContainer.addWidget(self.instrumentView)

        self.instrumentContainer.setStretchFactor(1, 3)
        self.setWidget(self.mainContainer)
        self.mainContainer.setCentralWidget(self.instrumentContainer)
        self.updateToolbarState()
        
    def initToolbar(self):
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.saveAsAction)
        
        self.toolbar.addSeparator()

        self.toolbar.addWidget(self.toolToggle)
        self.toolbar.addWidget(self.lockToggle)
        
    def initInstrumentNavigator(self):
        self.instrumentNavigator.setModel(self.fileSystem)
        self.instrumentNavigator.setDragEnabled(True)
        self.instrumentNavigator.setAcceptDrops(True)
        self.instrumentNavigator.setDefaultDropAction(Qt.MoveAction)
        self.instrumentNavigator.setRootIndex(self.fsIndex)
        self.instrumentNavigator.doubleClicked.connect(self.doubleClicked)
        self.instrumentNavigator.hideColumn(1)
        self.instrumentNavigator.hideColumn(2)
        self.instrumentNavigator.hideColumn(3)

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

        self.toolToggle = QToolButton(self)
        self.toolToggle.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons3\cogwheels.png')))
        self.toolToggle.setCheckable(True)
        self.toolToggle.setStatusTip('Show/Hide Tools')
        self.toolToggle.toggled.connect(self.toolsToggled)
        self.toolToggle.toggle()

        self.lockToggle = QToolButton(self)
        self.lockToggle.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons2\padlock.png')))
        self.lockToggle.setCheckable(True)
        self.lockToggle.setStatusTip('Show/Hide Tools')
        self.lockToggle.toggled.connect(self.lockToggled)
        self.lockToggle.toggle()

    def toolsToggled(self, checked):
        if(checked):
            self.toolWidgets.show()
        else:
            self.toolWidgets.hide()

    def lockToggled(self, checked):
        if(checked):
            pass
            #self.instrumentView.setDragEnabled(False)
            #self.instrumentView.setAcceptDrops(False)
        else:
            pass
            #self.instrumentView.setDragEnabled(True)
            #self.instrumentView.setAcceptDrops(True)

    def doubleClicked(self, index):
        item = self.fileSystem.fileInfo(index)
        filePath = item.filePath()
        fileExt = os.path.splitext(item.fileName())[1]
        if(fileExt == '.sqpy'):
            self.openInstrument(filePath)

    def openInstrument(self, filePath):
        print("opening path")

    def updateToolbarState(self):
        self.saveAction.setEnabled(True)
        self.saveAsAction.setEnabled(True)

class componentsList(QListWidget):
    def __init__(self, mainWindow, parent=None):
        super(componentsList, self).__init__(parent)

        self.mainWindow = mainWindow
        self.setDragEnabled(True)
        self.setViewMode(QListView.ListMode)
        self.setIconSize(QSize(60, 60))
        self.setSpacing(10)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(True)
        self.populateList()

    def mouseMoveEvent(self, e):
        mimeData = QMimeData()
        mimeData.setText("compDrag")
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)
        stream.writeQString(self.itemAt(e.pos()).text())
        data2 = QByteArray()
        stream2 = QDataStream(data2, QIODevice.WriteOnly)
        stream2.writeInt(self.selectedIndexes()[0].row())
        mimeData.setData("application/compName", data)
        mimeData.setData("application/compIndex", data2)
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        dropAction = drag.exec_()

    def populateList(self):
        compList = self.mainWindow.instrumentManager.getAvailableComponents()
        for val in compList:
            tempIcon = QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'User Components\img\\' + val.iconGraphicSrc))
            self.addItem(componentItem(tempIcon, val.componentType))

class componentItem(QListWidgetItem):
    def __init__(self, icon, text, parent=None):
        super(componentItem, self).__init__(parent)
        self.setText(text)
        self.setToolTip("Example Tooltip")
        self.setIcon(icon)
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

class compInstrItem(QListWidgetItem):
    def __init__(self, icon, text, parent=None):
        super(compInstrItem, self).__init__(parent)
        self.setText(text)
        self.setToolTip("This Item Is In")
        self.setIcon(icon)
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

class DSNewFileDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.scriptType = QComboBox()
        self.scriptType.setWindowTitle('New Instrument..')
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
            return "Instruments"
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