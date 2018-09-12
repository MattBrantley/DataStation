from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from xml.dom.minidom import *
from xml.etree.ElementTree import *
from Managers.WorkspaceManager.UserScript import *

class workspaceTreeDockWidget(QDockWidget):

    def __init__(self, mW):
        super().__init__('No Workspace Loaded')
        self.mW = mW
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)

        self.workspaceTreeWidget = WorkspaceTreeWidget(mW)
        self.setWidget(self.workspaceTreeWidget)

class WorkspaceTreeWidget(QTreeWidget):
    ITEM_GUID = Qt.UserRole
    ITEM_TYPE = Qt.UserRole+1
    ITEM_NAME = Qt.UserRole+2
    ITEM_UNITS = Qt.UserRole+3

    def __init__(self, mW):
        super().__init__()
        self.mW = mW
        self.wM = mW.wM
        self.setDragEnabled(True)
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)
        self.initMenu()
        self.initToolbar()

        self.itemSelectionChanged.connect(self.selectionChangedFunc)

    def initActions(self):

        self.exitAction = QAction(QIcon(os.path.join(self.mW.srcDir, r'icons2\minimize.png')), 'Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit Application')
        self.exitAction.triggered.connect(self.close)

        self.newAction = QAction(QIcon(os.path.join(self.mW.srcDir, r'icons2\controller.png')), 'New Workspace', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('Create a New Workspace')
        self.newAction.triggered.connect(self.wM.newWorkspace)

        self.saveAction = QAction(QIcon(os.path.join(self.srcDir, r'icons2\save.png')), 'Save Workspace As..', self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.setStatusTip('Save Workspace As..')
        self.saveAction.triggered.connect(self.wM.saveWSToNewSql)

        self.openAction = QAction(QIcon(os.path.join(self.mW.srcDir, r'icons2\\folder.png')), 'Open Workspace', self)
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.setStatusTip('Open Workspace')
        self.openAction.triggered.connect(self.wM.loadWSFromSql)

        self.settingsAction = QAction(QIcon(os.path.join(self.mW.srcDir, r'icons2\settings.png')), 'Settings', self)
        self.settingsAction.setShortcut('Ctrl+S')
        self.settingsAction.setStatusTip('Adjust Settings')

        self.importAction = QAction(QIcon(os.path.join(self.mW.srcDir, r'icons2\pendrive.png')), 'Import', self)
        self.importAction.setStatusTip('Import Data')
        self.importAction.triggered.connect(self.wM.importData)

        self.viewWindowsAction = QAction('Import', self)
        self.viewWindowsAction.triggered.connect(self.populateViewWindowMenu)

    def initMenu(self):
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('&File')
        self.fileMenu.addAction(self.newAction)
        self.fileMenu.addAction(self.saveAction)
        self.fileMenu.addAction(self.openAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.settingsAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.importAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAction)

        self.viewWindowsMenu = QMenu('Windows')
        self.viewWindowsMenu.aboutToShow.connect(self.populateViewWindowMenu)

        self.viewMenu = self.menubar.addMenu('&View')
        self.viewMenu.addMenu(self.viewWindowsMenu)

        self.importMenu = self.menubar.addMenu('&Import')
        self.wM.userScriptController.populateImportMenu(self.importMenu, self)

    def initToolbar(self):
        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.setObjectName('toolbar')
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.openAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.settingsAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.importAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.exitAction)

    def selectionChangedFunc(self):
        if(len(self.selectedItems()) > 0):
            if(self.selectedItems()[0].data(0, self.ITEM_TYPE) == 'Data'):
                self.mW.inspectorDockWidget.drawInspectorWidget(self.selectedItems()[0])

    def dragEnterEvent(self, event):
        if(event.mimeData().hasUrls()):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if(event.mimeData().hasUrls()):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if(url.isValid):
                self.wM.importDataByURL(url.toLocalFile())

    def getItemLevel(self, item):
        level = 0
        while(item.parent()):
            level += 1
            item = item.parent()
        return level

    def toXML(self):
        iterator = QTreeWidgetItemIterator(self)
        workingInd = []
        wsXML = Element('Workspace')
        wsXML.append(Comment('Workspace Variables and Operators are Contained Here'))
        while iterator.value():
            item = iterator.value()
            level = self.getItemLevel(item)
            if (len(workingInd) <= level):
                workingInd.append(0)
            if (level > 0):
                workingInd[level] = SubElement(workingInd[level - 1], item.data(0, self.ITEM_TYPE))
            else:
                workingInd[level] = SubElement(wsXML, item.data(0, self.ITEM_TYPE))
            workingInd[level].set('Name', item.data(0, self.ITEM_NAME))
            workingInd[level].set('GUID', item.data(0, self.ITEM_GUID))
            workingInd[level].set('Type', item.data(0, self.ITEM_TYPE))
            workingInd[level].set('Units', item.data(0, self.ITEM_UNITS))
            workingInd[level].text = "\n"
            workingInd[level].tail = "\n"
            iterator += 1
        return wsXML

    def fromXML(self, wsXMLString):
        self.clear()
        wsXML = XML(wsXMLString)
        self.treeItemFromXMLItem(wsXML, self.invisibleRootItem())

    def treeItemFromXMLItem(self, xmlItem, treeItem):
        for child in xmlItem:
            Metadata = child.attrib
            nTreeItem = self.addItem(treeItem, Metadata)
            self.treeItemFromXMLItem(child, nTreeItem)

    def submitOperation(self, script, selectedItem):
        dataOp = {'GUID': '', 'Type': 'Operation', 'Name': 'Operation: ' + script.name, 'Units': ''}
        return self.addItem(selectedItem, dataOp)

    def addItem(self, parent, data):
        item = QTreeWidgetItem(parent)
        nName = data['Name']
        item.setText(0, nName)
        item.setData(0, self.ITEM_NAME, data['Name'])
        item.setData(0, self.ITEM_GUID, data['GUID'])
        item.setData(0, self.ITEM_TYPE, data['Type'])
        item.setData(0, self.ITEM_UNITS, data['Units'])
        if(data['Type'] == 'Data'):
            item.setIcon(0, QIcon('icons4\database-1.png'))
        if(data['Type'] == 'Operation'):
            item.setIcon(0, QIcon('icons4\settings-6.png'))
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
        if(data['Type'] == 'Axis'):
            item.setHidden(True)

        return item

    def deleteItem(self, selectedItem):
        if(self.indexOfTopLevelItem(selectedItem) == -1): #Item is a child
            p = selectedItem.parent()
            p.removeChild(selectedItem)
        else:   #Item is top level (these are handled differently)
            self.takeTopLevelItem(self.indexOfTopLevelItem(selectedItem))
        self.workspace.deleteDSFromSql(selectedItem)

    def renameItem(self, selectedItem):
        text, ok = QInputDialog.getText(self.mW, 'Rename Item', 'Enter New Name', text=selectedItem.text(0))
        if(ok):
            selectedItem.setText(0, self.workspace.cleanStringName(text))
            selectedItem.setData(0, self.ITEM_NAME, text)
            self.wM.renameDSInSql(selectedItem)
            self.wM.saveWSToSql()

    def treeWidgetItemByGUID(self, GUID):
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            if(item.data(0, self.ITEM_GUID) == GUID):
                return item.data(0, self.ITEM_NAME)
            iterator += 1
        return 'ERROR!'

    def getAxisGUIDsByDataGUID(self, GUID):
        iterator = QTreeWidgetItemIterator(self)

        while iterator.value():
            item = iterator.value()
            if(item.data(0, self.ITEM_GUID) == GUID):
                axisGUIDList = []
                for idx in range(item.childCount()):
                    child = item.child(idx)
                    if(child.data(0, self.ITEM_TYPE) == 'Axis'):
                        axisGUIDList.append(child.data(0, self.ITEM_GUID))
                return axisGUIDList
            iterator += 1

        return []

    def initContextActions(self, selectedItem):
        self.renameAction = QAction(QIcon('icons\\analytics-1.png'), 'Rename Item', self.mW)
        self.renameAction.setStatusTip('Rename this Item')
        self.renameAction.triggered.connect(lambda: self.renameItem(selectedItem))

        self.deleteAction = QAction(QIcon('icons\\transfer-1.png'),'Delete Item', self.mW)
        self.deleteAction.setStatusTip('Delete this Item from Memory')
        self.deleteAction.triggered.connect(lambda: self.deleteItem(selectedItem))

        self.linePlotAction = QAction(QIcon('icons\\analytics-4.png'),'Line Plot', self.mW)
        self.linePlotAction.setStatusTip('Generate a line plot of this DataSet')
        self.linePlotAction.triggered.connect(lambda: self.wM.linePlotItem(selectedItem))

        self.surfacePlotAction = QAction(QIcon('icons\\analytics-4.png'),'Surface Plot', self.mW)
        self.surfacePlotAction.setStatusTip('Generate a surface plot of this DataSet')
        self.surfacePlotAction.triggered.connect(lambda: self.wM.surfacePlotItem(selectedItem))

    def initContextMenu(self):
        selectedItem = self.currentItem()
        itemType = selectedItem.data(0, self.ITEM_TYPE)
        self.initContextActions(selectedItem)
        self.contextMenu = QMenu()

        #Universal Workspace Context Menu Actions
        if(self.wM.userScripts.processManager.processWidget.processList.count() is not 0):
            self.renameAction.setEnabled(False)
            self.deleteAction.setEnabled(False)
        self.contextMenu.addAction(self.renameAction)
        self.contextMenu.addAction(self.deleteAction)
        self.contextMenu.addSeparator()

        #Type Specific Context Menu Actions
        if(itemType == 'Data'):
            self.contextMenu.addAction(self.linePlotAction)
            self.contextMenu.addAction(self.surfacePlotAction)
            self.contextMenu.addSeparator()
            self.wM.userScripts.populateActionMenu(self.contextMenu.addMenu('Operations'), UserOperation, self.mW, selectedItem)

    def initDefaultContextMenu(self):
        warningAction = QAction('Nothing selected!', self.mW)
        warningAction.setStatusTip('Nothing has been selected!')
        warningAction.setEnabled(False)

        self.contextMenu = QMenu()
        self.contextMenu.addAction(warningAction)

    def openMenu(self, position):
        if (self.selectedItems()):
            self.initContextMenu()
            self.contextMenu.exec_(self.viewport().mapToGlobal(position))
        else:
            self.initDefaultContextMenu()
            self.contextMenu.exec_(self.viewport().mapToGlobal(position))