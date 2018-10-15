from PyQt5.Qt import *
from shutil import copyfile
import os

class sequenceTreeView(QTreeView):
    def __init__(self, module):
        super().__init__()
        self.module = module
        self.ds = module.ds
        self.iM = module.ds.iM
        self.hM = module.ds.hM
        self.wM = module.ds.wM
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
        if(self.module.targetInstrument is not None):
            self.module.targetInstrument.Load_Sequence(item)

    def delete(self, item):
        os.remove(item)

    def duplicate(self, item):
        tempPath = os.path.splitext(item)[0] + '_copy' + os.path.splitext(item)[1]
        tempNum = 1
        while(os.path.isfile(tempPath)):
            tempNum = tempNum + 1
            tempPath = os.path.splitext(item)[0] + '_copy' + str(tempNum) + os.path.splitext(item)[1]
        
        copyfile(item, tempPath)

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