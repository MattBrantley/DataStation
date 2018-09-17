from PyQt5.Qt import *
from pyqode.core import api, modes, panels
import os
from shutil import copyfile

class editorWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole

    def __init__(self, mW):
        super().__init__("Code Editor")
        self.mW = mW
        self.hide()
        self.resize(1000, 800)

        self.initActions()

        self.mainContainer = QMainWindow()
        self.toolbar = QToolBar()
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.saveAsAction)
        self.toolbar.addAction(self.saveAllAction)
        self.mainContainer.addToolBar(self.toolbar)

        self.codeEditorContainer = QSplitter()
        self.codeEditorTabs = QTabWidget()
        self.codeEditorTabs.setMovable(True)
        self.codeEditorTabs.setTabsClosable(True)
        self.codeEditorTabs.tabCloseRequested.connect(self.closeTab)
        self.fileSystem = DSEditorFSModel()
        self.fsIndex = self.fileSystem.setRootPath(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))  #This is a placeholder - will need updating.

        self.codeEditorNavigator = DSTreeView(self, self.fileSystem)
        self.codeEditorNavigator.setModel(self.fileSystem)
        self.codeEditorNavigator.setDragEnabled(True)
        self.codeEditorNavigator.setAcceptDrops(True)
        self.codeEditorNavigator.setDefaultDropAction(Qt.MoveAction)
        self.codeEditorNavigator.setRootIndex(self.fsIndex)
        self.codeEditorNavigator.doubleClicked.connect(self.doubleClicked)
        self.codeEditorNavigator.hideColumn(1)
        self.codeEditorNavigator.hideColumn(2)
        self.codeEditorNavigator.hideColumn(3)

        self.codeEditorContainer.addWidget(self.codeEditorNavigator)
        self.codeEditorContainer.addWidget(self.codeEditorTabs)
        self.codeEditorContainer.setStretchFactor(1, 3)
        self.setWidget(self.mainContainer)
        self.mainContainer.setCentralWidget(self.codeEditorContainer)
        self.updateToolbarState()

    def save(self):
        curWidget = self.codeEditorTabs.currentWidget()
        curWidget.file.save()

    def saveAs(self):
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

    def saveAll(self):
        for n in range(0, self.codeEditorTabs.count()):
            self.codeEditorTabs.widget(n).file.save()

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

    def updateToolbarState(self):
        if(self.codeEditorTabs.count() == 0):
            self.saveAction.setEnabled(False)
            self.saveAsAction.setEnabled(False)
            self.saveAllAction.setEnabled(False)
        else:
            self.saveAction.setEnabled(True)
            self.saveAsAction.setEnabled(True)
            self.saveAllAction.setEnabled(True)

    def closeTab(self, index):
        self.codeEditorTabs.removeTab(index)
        self.updateToolbarState()

    def doubleClicked(self, index):
        item = self.fileSystem.fileInfo(index)
        filePath = item.filePath()
        fileExt = os.path.splitext(item.fileName())[1]
        if(fileExt == '.py'):
            self.newTab(filePath)

    def newTab(self, path):
        res = self.isFileOpened(path)
        if(res == -1):
            editor = DSEditor(path)
            self.codeEditorTabs.addTab(editor, editor.fileName)
            editor.dirty_changed.connect(self.fileIsDirty)
            self.codeEditorTabs.setCurrentIndex(self.codeEditorTabs.count()-1)
        else:
            self.codeEditorTabs.setCurrentIndex(res)
            print('File already opened in Code Editor!')

        self.updateToolbarState()

    def isFileOpened(self, path):
        for n in range(0, self.codeEditorTabs.count()):
            if(self.codeEditorTabs.widget(n).filePath == path):
                return n
        return -1

    def fileIsDirty(self):
        sender = self.sender()
        ind = self.isFileOpened(sender.filePath)
        if(sender.dirty):
            self.codeEditorTabs.setTabText(ind, '*'+sender.fileName)
        else:
            self.codeEditorTabs.setTabText(ind, sender.fileName)

class DSNewFileDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.scriptType = QComboBox()
        self.scriptType.setWindowTitle('New User Script..')
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
            return "User Scripts"
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

class DSEditor(api.CodeEdit):
    filePath = ''
    fileName = ''
    head = ''

    def __init__(self, path):
        super().__init__()
        self.defFont = QFont()
        self.defFont.setFamily('Courier')
        self.defFont.setFixedPitch(True)
        self.defFont.setPointSize(10)

        self.modes.append(modes.PygmentsSyntaxHighlighter(self.document()))
        self.modes.append(modes.CaretLineHighlighterMode())
        self.modes.append(modes.IndenterMode())
        self.modes.append(modes.AutoIndentMode())
        self.modes.append(modes.SmartBackSpaceMode())
        self.modes.append(modes.ZoomMode())
        self.panels.append(panels.SearchAndReplacePanel(), api.Panel.Position.BOTTOM)
        self.panels.append(panels.LineNumberPanel(), api.Panel.Position.LEFT)
        self.file.open(path)
        self.setFont(self.defFont)
        self.head, self.fileName = os.path.split(path)
        self.filePath = path
