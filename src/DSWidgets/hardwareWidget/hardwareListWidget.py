from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, time
from src.Constants import DSConstants as DSConstants
from src.DSWidgets.hardwareWidget import filterStackWidget, hardwareListWidget, gridViewWidget
from src.Managers.InstrumentManager.Sockets import AOSocket, AISocket, DOSocket, DISocket
from src.Managers.HardwareManager.Sources import AOSource, AISource, DOSource, DISource

class hardwareListWidget(QWidget):

    def __init__(self, mW):
        super().__init__()
        self.mW = mW
        self.hM = mW.hM
        self.iM = mW.iM
        self.wM = mW.wM

        self.mainLayout = QVBoxLayout()
        self.hardwareList = hardwareListView(self, self.mW)
        self.setLayout(self.mainLayout)

        self.scroll = QScrollArea(self)
        self.mainLayout.addWidget(self.scroll)

        self.newButton = QPushButton("Add Hardware Object")
        self.newButton.pressed.connect(self.newButtonPressed)
        self.mainLayout.addWidget(self.newButton)

        self.mainLayout.setSpacing(2)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.hardwareList)

        self.hM.Hardware_Added.connect(self.addHardware)
        
    def newButtonPressed(self):
        menu = QMenu()

        hardwareMenuAction = hardwareSelectionWidget(self, menu, self.mW)
        menu.addAction(hardwareMenuAction)
        action = menu.exec_(QCursor().pos())

    def addHardware(self, hardwareObj):
        widgetItem = hardwareListItem(self.hardwareList, self.mW, hardwareObj)
        
        self.hardwareList.addWidget(widgetItem)

class hardwareListView(QWidget):

    def __init__(self, parent, mW):
        super().__init__()
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.parent = parent
        self.hardwareItemList = list()
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.mainLayout.addStretch()

    def addWidget(self, widget):
        self.mainLayout.insertWidget(self.mainLayout.count()-1, widget)

    def removeWidget(self, widget):
        self.mainLayout.removeWidget(widget)

class hardwareListItem(QWidget):
    heightMinimized = 200
    heightMaximized = 400
    state = 'min'

    def __init__(self, hardwareListView, mW, hardwareObj):
        super().__init__()
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.hardwareListView = hardwareListView
        self.hardwareObj = hardwareObj
        self.msgWidget = driverMessageWidget(self.mW)

        self.configButton = QPushButton()
        self.configIcon = QIcon(os.path.join(self.mW.srcDir, 'icons5\settings.png'))
        self.configButton.setIcon(self.configIcon)
        self.configButton.setIconSize(QSize(16,16))
        self.configButton.pressed.connect(self.showConfigWidget)

        self.infoSection = QWidget()
        self.infoSectionLayout = QVBoxLayout()
        self.infoSectionLayout.addWidget(QLabel(hardwareObj.hardwareType))
        self.infoSectionLayout.addWidget(self.configButton)
        self.infoSectionLayout.addStretch()

        self.infoSection.setLayout(self.infoSectionLayout)

        self.layout = QVBoxLayout()
        self.topPortion = QWidget()
        self.topPortionLayout = QHBoxLayout()
        self.topPortion.setLayout(self.topPortionLayout)
        self.topPortionLayout.addWidget(self.infoSection)
        self.topPortionLayout.addWidget(self.msgWidget)
        self.topPortionLayout.addSpacerItem(QSpacerItem(30, 1))
        self.topPortion.setMaximumHeight(self.heightMinimized-10)
        self.topPortion.setMinimumHeight(self.heightMinimized-10)
        self.closeButtonRect = QRect(0, 0, 0, 0)

        self.botPortion = QWidget()
        self.botPortionLayout = QVBoxLayout()
        self.botPortion.setLayout(self.botPortionLayout)
        self.sourceLabel = QLabel("Sources:")
        self.sourceListWidget = sourceListWidget(self.hardwareObj, self.mW)
        self.botPortionLayout.addWidget(self.sourceLabel)
        self.botPortionLayout.addWidget(self.sourceListWidget)

        self.setLayout(self.layout)
        self.setHeight()
        self.setMaximumHeight(self.heightMinimized)
        self.setMinimumHeight(self.heightMinimized)

        self.minMaxPos = QPointF(self.width()-26, self.heightMinimized-20)
        self.minMaxSize = 12

        self.layout.addWidget(self.topPortion)

        self.messageUpdateTimer = QTimer()
        self.messageUpdateTimer.timeout.connect(self.updateMessages)
        self.messageUpdateTimer.start(20)

    def updateMessages(self):
        newMsgs = self.hardwareObj.getMessages()
        for msg in newMsgs:
            if(msg.action=='refresh'):
                self.msgWidget.clear()
            self.msgWidget.addItem(time.strftime('[%m/%d/%Y %H:%M:%S] ') + msg.msg)
            self.msgWidget.setCurrentRow(self.msgWidget.count()-1)

    def setHeight(self):
        if(self.state == 'min'):
            self.setMaximumHeight(self.heightMinimized)
            self.setMinimumHeight(self.heightMinimized)

        if(self.state == 'max'):
            self.setMaximumHeight(self.heightMaximized)
            self.setMinimumHeight(self.heightMaximized)

    def toggleMinMax(self):
        if(self.state == 'min'):
            self.state = 'max'
            self.layout.addWidget(self.botPortion)
        else:
            self.state = 'min'
            self.layout.removeWidget(self.botPortion)

        self.setHeight()

    def closeButton(self):
        self.hM.Remove_Hardware(self.hardwareObj)
        self.setParent(None)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.drawRoundedRect(0, 5, self.width()-5, self.height()-7, 3, 3)

        poly = QPolygonF()
        self.minMaxPos = QPointF(self.width()-26, self.heightMinimized-20)

        if(self.state == 'max'):
            poly.append(self.minMaxPos + QPointF(self.minMaxSize/2, 0))
            poly.append(self.minMaxPos + QPointF(0, self.minMaxSize))
            poly.append(self.minMaxPos + QPointF(self.minMaxSize, self.minMaxSize))
            poly.append(self.minMaxPos + QPointF(self.minMaxSize/2, 0))
        if(self.state == 'min'):
            poly.append(self.minMaxPos + QPointF(0, 0))
            poly.append(self.minMaxPos + QPointF(self.minMaxSize/2, self.minMaxSize))
            poly.append(self.minMaxPos + QPointF(self.minMaxSize, 0))
            poly.append(self.minMaxPos + QPointF(0, 0))

        painter.drawPolygon(poly)

        closeButtonSize = 12
        self.closeButtonRect = QRect(self.width()-closeButtonSize-16, closeButtonSize+6, closeButtonSize, closeButtonSize)
        painter.drawRect(self.closeButtonRect)
        painter.drawLine(self.closeButtonRect.topLeft()+QPoint(2, 2), self.closeButtonRect.bottomRight()-QPoint(1, 1))
        painter.drawLine(self.closeButtonRect.topRight()-QPoint(1, -2), self.closeButtonRect.bottomLeft()+QPoint(2, -1))

        super().paintEvent(e)

    def showConfigWidget(self):
        cursor = QCursor()
        self.hardwareObj.showConfigWidget(cursor.pos())

    def mousePressEvent(self, e):
        #check if min/max pressed
        minMaxRect = QRectF(self.minMaxPos.x(), self.minMaxPos.y(), self.minMaxSize, self.minMaxSize)
        if(minMaxRect.contains(e.pos())):
            self.toggleMinMax()
            return
        
        if(self.closeButtonRect.contains(e.pos())):
            self.closeButton()
            return

class hardwareSelectionWidget(QWidgetAction):
    def __init__(self, parent, menu, mW):
        super().__init__(None)
        self.parent = parent
        self.menu = menu
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.pWidget = QWidget()
        self.pLayout = QVBoxLayout()
        self.pSpinBox = QListWidget()
        self.pSpinBox.itemClicked.connect(self.itemClicked)
        self.pLayout.addWidget(self.pSpinBox)
        self.pWidget.setLayout(self.pLayout)

        self.setDefaultWidget(self.pWidget)

        self.populateBox()

    def itemClicked(self):
        curItem = self.pSpinBox.currentItem()
        self.parent.hM.Add_Hardware(curItem.hardwareModel)
        self.menu.close()

    def populateBox(self):
        for hardwareModel in self.parent.hM.Get_Hardware_Models_Available():
            self.pSpinBox.addItem(hardwareSelectionItem(hardwareModel.hardwareType, hardwareModel))

class hardwareSelectionItem(QListWidgetItem):
    def __init__(self, name, hardwareModel):
        super().__init__(name)
        self.name = name
        self.hardwareModel = hardwareModel

class sourceListWidget(QListWidget):
    def __init__(self, hardwareObj, mW):
        super().__init__()
        self.hardwareObj = hardwareObj
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM

        self.hM.Source_Added.connect(self.addSource)

    def addSource(self, hardwareObj, source):
        if(hardwareObj is self.hardwareObj):
            self.addItem(sourceListItem(source, self.mW))

    def clearSources(self):
        self.clear()

class sourceListItem(QListWidgetItem):
    def __init__(self, source, mW):
        super().__init__()
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.source = source
        self.setText(self.source.Get_Name())
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

class driverMessageWidget(QListWidget):
    def __init__(self, mW):
        super().__init__()
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.maximumHeight = 150
