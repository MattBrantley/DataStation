from PyQt5.Qt import *
import os

class moduleManagerWindow(QMainWindow):
    ITEM_GUID = Qt.UserRole

    def __init__(self, ds):
        super().__init__(None)
        self.setWindowTitle('Module Manager')
        self.ds = ds
        self.mM = ds.mM
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.mainWidget = QTabWidget()
        self.setCentralWidget(self.mainWidget)

        self.modulesTab = modulesTab(self.ds)
        self.mainWidget.addTab(self.modulesTab, 'Modules')

        self.windowsTab = windowsTab(self.ds)
        self.mainWidget.addTab(self.windowsTab, 'Windows')

        self.stylesTab = stylesTab(self.ds)
        self.mainWidget.addTab(self.stylesTab, 'Styles')

        self.ds.DataStation_Closing.connect(self.closing)

    def closing(self):
        self.close()
        
class stylesTab(QWidget):
    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        self.mM = ds.mM
        self.initWindow()

    def initWindow(self):
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.listBox = QListWidget()
        self.listBox.itemClicked.connect(self.listBoxChanged)
        self.populateStyles()
        self.mainLayout.addWidget(self.listBox)

        self.applyButton = QPushButton('Apply Style')
        self.applyButton.pressed.connect(self.applyPressed)
        self.applyButton.setEnabled(False)
        self.mainLayout.addWidget(self.applyButton)

    def listBoxChanged(self):
        if self.listBox.currentIndex != -1:
            self.applyButton.setEnabled(True)

    def populateStyles(self):
        self.listBox.clear()
        listItem = QListWidgetItem('Default')
        self.listBox.addItem(listItem)
        listItem.ssPath = None

        stylesPath = os.path.join(self.ds.rootDir, 'Stylesheets')

        for root, dirs, files in os.walk(stylesPath):
            for file in files:
                url = os.path.join(root, file)
                name, ext = os.path.splitext(file)
                if ext == '.stylesheet':
                    listItem = QListWidgetItem(name, parent=self.listBox)
                    #listItem = self.listBox.addItem(listItem)
                    listItem.ssPath = url

    def applyPressed(self):
        ssPath = self.listBox.selectedItems()[0].ssPath
        self.mM.Set_StyleSheet(ssPath)


class windowsTab(QWidget):
    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        self.mM = ds.mM
        self.initWindow()

    def initWindow(self):
        self.mainLayout = QHBoxLayout()
        self.setLayout(self.mainLayout)

        self.initLeftSide()
        self.mainLayout.addWidget(self.leftSide)

    def initLeftSide(self):
        self.leftSide = QWidget()
        self.leftSideLayout = QVBoxLayout()
        self.leftSide.setLayout(self.leftSideLayout)
    
        self.newWindowButton = QPushButton('New Window')
        self.newWindowButton.pressed.connect(self.newWindowPressed)
        self.leftSideLayout.addWidget(self.newWindowButton)

    def newWindowPressed(self):
        self.mM.Add_New_Window()

class modulesTab(QWidget):
    def __init__(self, ds):
        super().__init__()
        self.showFolders = False
        self.ds = ds
        self.mM = ds.mM
        self.initWindow()
        self.populateWindow()

    ##### Initialize Window Layout #####
    def initWindow(self):
        #### Main Widget & Layout
        self.mainLayout = QHBoxLayout()
        self.setLayout(self.mainLayout)

        self.initLeftSide()
        self.mainLayout.addWidget(self.leftSide)
        self.initRightSide()
        self.mainLayout.addWidget(self.rightSide)

    def initLeftSide(self):
        self.leftSide = QWidget()
        self.leftSideLayout = QVBoxLayout()
        self.leftSide.setLayout(self.leftSideLayout)

        self.moduleIcon = QIcon(os.path.join(self.ds.srcDir, 'icons/pie-chart.png'))

        self.moduleTree = moduleTree(self.ds)

        #self.moduleTree.contextMenuEvent.connect(self.moduleContextMenu)

        self.leftSideLayout.addWidget(self.moduleTree)

        self.checkboxWidget = QWidget()
        self.checkboxLayout = QHBoxLayout()
        self.checkboxWidget.setLayout(self.checkboxLayout)

        self.checkBox = QCheckBox()
        self.checkBox.clicked.connect(self.showFoldersChanged)
        self.checkboxLayout.addWidget(QLabel('Show Folders: '))
        self.checkboxLayout.addStretch()
        self.checkboxLayout.addWidget(self.checkBox)

        self.leftSideLayout.addWidget(self.checkboxWidget)

    def initRightSide(self):
        self.rightSide = QWidget()
        self.rightSideLayout = QVBoxLayout()
        self.rightSide.setLayout(self.rightSideLayout)

    ##### Populate Window Contents #####
    def populateWindow(self):
        self.populateModuleTree()

    def showFoldersChanged(self, val):
        if val is True:
            self.showFolders = True
        else:
            self.showFolders = False

        self.populateModuleTree()

    def populateModuleTree(self):
        self.moduleTree.clear()
        rootNode = self.moduleTree.invisibleRootItem()

        for module in self.mM.Get_Available_Modules():
            dirs = module.subDirectories
            if dirs is False or self.showFolders is False:
                moduleItem = moduleTreeItem(rootNode, [module.name, 'Module'], module)
                moduleItem.setIcon(0, self.moduleIcon)
            else:
                curNode = rootNode
                for dirsItem in dirs:
                    curNode = self.findOrCreateChildNode(dirsItem, curNode)
                moduleItem = moduleTreeItem(curNode, [module.name, 'Module'], module)
                moduleItem.setIcon(0, self.moduleIcon)
                    
    def findOrCreateChildNode(self, nodeName, parentNode):
        for i in range(parentNode.childCount()):
            if(parentNode.child(i).text(0) == nodeName and parentNode.child(i).text(1) != 'Module'):
                return parentNode.child(i)
        
        # If we can't find this node, create it!
        return QTreeWidgetItem(parentNode, [nodeName, ''])

class moduleTree(QTreeWidget):
    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        self.mM = ds.mM

        self.setColumnCount(0)
        self.setSortingEnabled(True)
        self.setHeaderLabels(['Modules'])
        self.header().hideSection(1)

    def mousePressEvent(self, mouseEvent):
        super().mousePressEvent(mouseEvent)
        itemPressed = self.itemAt(mouseEvent.pos())
        if itemPressed is not None:
            if itemPressed.text(1) == 'Module':
                if(mouseEvent.buttons() == Qt.RightButton):
                    self.showModuleContextMenu(itemPressed, mouseEvent.pos())

    def showModuleContextMenu(self, item, pos):
        menu = QMenu(self)
        addMenu = QMenu('Add Instance', self)
        menu.addMenu(addMenu)

        windowActionList = list()
        for window in self.mM.Get_Windows():
            windowActionList.append(addMenu.addAction(window.windowTitle()))
        action = menu.exec_(self.mapToGlobal(pos))
        if action in windowActionList:
            idx = windowActionList.index(action)
            window = self.mM.Get_Windows()[idx]
            module = item.module
            self.mM.Add_Module_Instance(module, window)
        #if action == addAction:
        #    print('Adding')

class moduleTreeItem(QTreeWidgetItem):
    def __init__(self, node, texts, module):
        super().__init__(node, texts)
        self.module = module