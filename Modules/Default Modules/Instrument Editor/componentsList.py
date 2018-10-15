from PyQt5.Qt import *
from PyQt5.QtCore import *
import os

class componentsList(QListWidget):
    def __init__(self, module):
        super().__init__(None)
        self.module = module
        self.ds = module.ds
        self.iM = module.ds.iM
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
        if(self.itemAt(e.pos()) is not None):
            stream.writeQString(self.itemAt(e.pos()).text())
        else:
            return
        data2 = QByteArray()
        stream2 = QDataStream(data2, QIODevice.WriteOnly)
        stream2.writeInt(self.selectedIndexes()[0].row())
        mimeData.setData("application/compName", data)
        mimeData.setData("application/compIndex", data2)
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        dropAction = drag.exec_()

    def populateList(self):
        for val in self.iM.Get_Component_Models_Available():
            tempIcon = QIcon(os.path.join(self.ds.rootDir, 'Components\img\\' + val.iconGraphicSrc))
            self.addItem(componentItem(tempIcon, val.componentType))

class componentItem(QListWidgetItem):
    def __init__(self, icon, text):
        super().__init__(None)
        self.setText(text)
        self.setIcon(icon)
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
