from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
from shutil import copyfile

class treeView(QTreeView):
    def __init__(self, module):
        super().__init__()
        self.module = module
        self.ds = module.ds
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.rightClick)
        
        self.fileSystem = DSEditorFSModel()
        self.rootPath = os.path.join(self.ds.rootDir, 'Instruments')
        self.fsIndex = self.fileSystem.setRootPath(self.rootPath)

        self.setModel(self.fileSystem)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setRootIndex(self.fsIndex)
        self.doubleClicked.connect(self.doubleClicked)
        self.hideColumn(1)
        self.hideColumn(2)
        self.hideColumn(3)

    def mousePressEvent(self, event):
        self.clearSelection()
        event.accept()
        QTreeView.mousePressEvent(self, event)

    def rightClick(self, point):
        idx = self.mapToGlobal(point)

        item = self.selectionModel().selectedIndexes()
        if(len(item) > 0):
            if(os.path.isdir(self.fileSystem.filePath(item[0]))):        #Show different menu on folders
                newInstrumentAction = QAction('New Instrument', self)
                newInstrumentAction.triggered.connect(lambda: self.newInstrumentAction(self.fileSystem.filePath(item[0])))

                newFolderAction = QAction('New Folder', self)
                newFolderAction.triggered.connect(lambda: self.newFolderAction(self.fileSystem.filePath(item[0])))
                
                menu = QMenu(self)
                menu.addAction(newInstrumentAction)
                menu.addAction(newFolderAction)
                menu.exec(idx)
            else:                                                   #Show this menu for non-folder items
                openInstrumentAction = QAction('Open', self)
                openInstrumentAction.triggered.connect(lambda: self.openInstrumentAction(self.fileSystem.filePath(item[0])))

                newInstrumentAction = QAction('New Instrument', self)
                newInstrumentAction.triggered.connect(lambda: self.newInstrumentAction(self.fileSystem.filePath(item[0])))

                newFolderAction = QAction('New Folder', self)
                newFolderAction.triggered.connect(lambda: self.newFolderAction(self.fileSystem.filePath(item[0])))
                
                deleteAction = QAction('Delete', self)
                deleteAction.triggered.connect(lambda: self.delete(self.fileSystem.filePath(item[0])))

                duplicateAction = QAction('Duplicate', self)
                duplicateAction.triggered.connect(lambda: self.duplicate(self.fileSystem.filePath(item[0])))

                menu = QMenu(self)
                menu.addAction(openInstrumentAction)
                menu.addSeparator()
                menu.addAction(newInstrumentAction)
                menu.addAction(newFolderAction)
                menu.addAction(deleteAction)
                #menu.addAction(duplicateAction)
                menu.exec(idx)
        else:                                                       #Show this menu for non-items
            newInstrumentAction = QAction('New Instrument', self)
            newInstrumentAction.triggered.connect(lambda: self.newInstrumentAction(self.module.rootPath))

            newFolderAction = QAction('New Folder', self)
            newFolderAction.triggered.connect(lambda: self.newFolderAction(self.module.rootPath))
            
            menu = QMenu(self)
            menu.addAction(newInstrumentAction)
            menu.addAction(newFolderAction)
            menu.exec(idx)

    def openInstrumentAction(self, item):
        self.module.openInstrument(item)

    def newInstrumentAction(self, item):
        print(item)

    def newFolderAction(self, item):
        print(item)

    def delete(self, item):
        os.remove(item)

    def duplicate(self, item):
        tempPath = os.path.splitext(item)[0] + '_copy' + os.path.splitext(item)[1]
        tempNum = 1
        while(os.path.isfile(tempPath)):
            tempNum = tempNum + 1
            tempPath = os.path.splitext(item)[0] + '_copy' + str(tempNum) + os.path.splitext(item)[1]

        copyfile(item, tempPath)

class DSEditorFSModel(QFileSystemModel):
    def __init__(self):
        super().__init__()
        self.setReadOnly(False)
        self.setNameFilters({'*.dsinstrument'})

    def headerData(self, section, orientation, role):
        if section == 0 and role == Qt.DisplayRole:
            return "Instruments"
        else:
            return super(QFileSystemModel, self).headerData(section, orientation, role)
