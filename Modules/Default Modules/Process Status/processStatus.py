from PyQt5.Qt import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class processStatus(DSModule):
    Module_Name = 'Process Status'
    Module_Flags = []

    def __init__(self, ds):
        super().__init__(ds)
        
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)

        self.processList = QListWidget(self)
        self.processList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.processList.customContextMenuRequested.connect(self.openMenu)

        self.setWidget(self.processList)

    def addProcessToWidget(self, job):
        newJobWidget = job.createJobWidget(self.processList)
        self.processList.addItem(newJobWidget.getJobWidgetItem())
        self.processList.setItemWidget(newJobWidget.getJobWidgetItem(), newJobWidget)

    def initDefaultContextMenu(self):
        selectedItem = self.processList.currentItem()
        selectedRow = self.processList.currentRow()
        itemWorker = selectedItem.data(Qt.UserRole)

        warningAction = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'icons4\multiply-1')), 'Kill Job', self.workspace.ds)
        warningAction.setStatusTip('Kill the selected job. (Note: No data will be returned)')
        warningAction.triggered.connect(lambda: self.abortJob(itemWorker))
        warningAction.setEnabled(True)

        self.contextMenu = QMenu()
        self.contextMenu.addAction(warningAction)

    def openMenu(self, position):
        if(self.processList.selectedItems()):
            self.initDefaultContextMenu()
            self.contextMenu.exec_(self.processList.viewport().mapToGlobal(position))