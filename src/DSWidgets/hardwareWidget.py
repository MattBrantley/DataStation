from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, time
from Constants import DSConstants as DSConstants
from DSWidgets.filterStackWidget import filterStackWidget
from Managers.InstrumentManager.Sockets import AOSocket, AISocket, DOSocket, DISocket
from Managers.HardwareManager.Sources import AOSource, AISource, DOSource, DISource

class hardwareWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole
    socketList = list()
    sourceList = list()

    def __init__(self, mW):
        super().__init__('Hardware')
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM

        self.hide()
        self.resize(800, 800)
        self.toolbar = QToolBar()

        self.mainContainer = QMainWindow()
        self.mainContainer.addToolBar(self.toolbar)

        self.driversWidget = QWidget()

        self.filtersWidget = QWidget()

        self.hardwareWidget = hardwareListWidget(self, self.mW)

        self.filterStackWidget = filterStackWidget(self, self.mW)
        self.filterStackWidget.setObjectName('filterStackWidget')
        self.mW.addDockWidget(Qt.BottomDockWidgetArea, self.filterStackWidget)
        self.filterStackWidget.hide()
        self.filterStackWidget.setFloating(True)

        self.gridContainer = QWidget()
        self.gridContainerLayout = QVBoxLayout()
        self.gridContainer.setLayout(self.gridContainerLayout)

        self.gridCombo = QComboBox()
        self.gridCombo.addItem('Sockets: Analog Output')
        self.gridCombo.addItem('Sockets: Analog Input')
        self.gridCombo.addItem('Sockets: Digital Output')
        self.gridCombo.addItem('Sockets: Digital Input')
        self.gridCombo.currentTextChanged.connect(self.drawScene)

        self.gridContainerLayout.addWidget(self.gridCombo)

        self.gridWidget = QGraphicsView()
        self.gridTransform = QTransform()
        self.gridWidget.setTransform(self.gridTransform)
        self.iScene = iScene(self, self.gridTransform, self.mW)
        gridRect = QRectF(0, 0, 1600, 1600)
        self.tabWidget = QTabWidget()
        self.gridWidget.setSceneRect(gridRect)
        self.gridWidget.setScene(self.iScene)

        self.gridContainerLayout.addWidget(self.gridWidget)

        self.tabWidget.addTab(self.hardwareWidget, "Attached Hardware")
        self.tabWidget.addTab(self.gridContainer, "Connection Grid")
        self.tabWidget.addTab(self.filtersWidget, "Filters")
        self.tabWidget.addTab(self.driversWidget, "Hardware Drivers")
        self.mainContainer.setCentralWidget(self.tabWidget)
        self.setWidget(self.mainContainer)

        self.iM.Instrument_Unloaded.connect(self.drawScene)
        self.iM.Instrument_Loaded.connect(self.drawScene)

        self.drawScene()

    def repopulateSocketsAndPlugs(self):        
        typeText = self.gridCombo.currentText()

        if(self.iM.currentInstrument is not None):
            if(typeText == 'Sockets: Analog Output'):
                self.socketList = self.iM.Get_Instrument().Get_Sockets_By_Type(AOSocket)
                self.sourceList = self.hM.Get_All_Sources_By_Type(AOSource)
            if(typeText == 'Sockets: Analog Input'):
                self.socketList = self.iM.Get_Instrument().Get_Sockets_By_Type(AISocket)
                self.sourceList = self.hM.Get_All_Sources_By_Type(AISource)
            if(typeText == 'Sockets: Digital Output'):
                self.socketList = self.iM.Get_Instrument().Get_Sockets_By_Type(DOSocket)
                self.sourceList = self.hM.Get_All_Sources_By_Type(DOSource)
            if(typeText == 'Sockets: Digital Input'):
                self.socketList = self.iM.Get_Instrument().Get_Sockets_By_Type(DISocket)
                self.sourceList = self.hM.Get_All_Sources_By_Type(DISource)
        else:
            self.socketList = list()
            self.sourceList = list()

    def drawScene(self):
        self.repopulateSocketsAndPlugs()
        self.iScene.itemList.clear()
        self.iScene.redrawn()
        self.iScene.clear()
        rows = len(self.socketList)
        cols = len(self.sourceList)
        totalWidth = cols * self.iScene.cellWidth
        totalHeight = rows * self.iScene.cellHeight
        gridRect = QRectF(0, 0, totalWidth + self.iScene.marginLeft + 10, totalHeight + self.iScene.marginTop + 10)
        self.gridWidget.setSceneRect(gridRect)

        labelFont = QFont()
        labelFont.setBold(True)
        labelFont.setPointSize(12)

        plugLabel = self.iScene.addText('SOURCES')
        plugLabel.setFont(labelFont)
        plugLabel.setPos(self.iScene.marginLeft + totalWidth/2 - plugLabel.boundingRect().width()/2, 0)

        transformSocketLabel = QTransform()
        transformSocketLabel.rotate(270)

        socketLabel = self.iScene.addText('SOCKETS')
        socketLabel.setFont(labelFont)
        socketLabel.setTransform(transformSocketLabel)
        socketLabel.setPos(0, self.iScene.marginTop + totalHeight/2 + socketLabel.boundingRect().width()/2)

        offsetY = self.iScene.marginTop
        self.iScene.addLine(self.iScene.marginLeft, offsetY, self.iScene.marginLeft+totalWidth, offsetY)
        for socket in self.socketList:
            text = self.iScene.addText(socket.socketSettings['name'])
            text.setPos(self.iScene.marginLeft - text.boundingRect().width(), offsetY)
            
            offsetY = offsetY + self.iScene.cellWidth
            self.iScene.addLine(self.iScene.marginLeft, offsetY, self.iScene.marginLeft+totalWidth, offsetY)

        offsetX = self.iScene.marginLeft
        self.iScene.addLine(offsetX, self.iScene.marginTop, offsetX, self.iScene.marginTop+totalHeight)
        transformTopText = QTransform()
        transformTopText.rotate(270)
        for plug in self.sourceList:
            text = self.iScene.addText(plug.sourceSettings['name'])
            text.setTransform(transformTopText)
            text.setPos(offsetX + text.boundingRect().height() - self.iScene.cellWidth, self.iScene.marginTop)

            offsetX = offsetX + self.iScene.cellHeight
            self.iScene.addLine(offsetX, self.iScene.marginTop, offsetX, self.iScene.marginTop+totalHeight)

        self.iScene.connectPlugsAndSockets()

##### Hardware List Widget #####

class hardwareListWidget(QWidget):

    def __init__(self, hardwareWidget, mW):
        super().__init__()
        self.hardwareWidget = hardwareWidget
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
        self.configIcon = QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons5\settings.png'))
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
        menu = QMenu()

        hardwareConfig = QWidgetAction(self)
        hardwareConfig.setDefaultWidget(self.hardwareObj.hardwareObjectConfigWidgetParent())
        menu.addAction(hardwareConfig)
        cursor = QCursor()

        action = menu.exec_(cursor.pos())

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

##### Source List View Widget #####

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
        self.setText(self.source.Get_Source_Name())
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

##### Connection Grid Widget #####

class iScene(QGraphicsScene):
    marginLeft = 150
    marginTop = 150
    cellHeight = 20
    cellWidth = 20
    multiConnectPlugs = True
    multiConnectSockets = True
    itemList = list()
    highlightList = list()

    def __init__(self, widget, transform, mW):
        super().__init__()
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.widget = widget
        self.transform = transform

    def redrawn(self):
        self.highlightList.clear()

    def sceneWidth(self):
        return len(self.widget.sourceList)*self.cellWidth + self.marginLeft

    def sceneHeight(self):
        return len(self.widget.socketList)*self.cellHeight + self.marginTop

    def connectPlugsAndSockets(self):
        #self.widget.mW.controlWidget.configChanged()
        self.clearItems()
        for socket in self.widget.socketList:
            if(socket.cP.isTriggerComponent is True):
                for source in self.widget.sourceList:
                    if(source.trigger == False):
                        self.addItemToGrid(self.getSocketRow(socket), self.getPlugCol(source), None, color='grey')

            source = socket.getSource()
            if(source is not None):
                row = self.getSocketRow(socket)
                col = self.getPlugCol(source)
                if(row is not None and col is not None):
                    self.addItemToGrid(row, col, None)

    def getSocketRow(self, socketIn):
        index = 1
        for socket in self.widget.socketList:
            if(socket == socketIn):
                return index
            index = index + 1

        return None

    def getPlugCol(self, plugIn):
        index = 1
        for plug in self.widget.sourceList:
            if(plug == plugIn):
                return index
            index = index + 1

        return None

    def mousePressEvent(self, event):
        event.ignore()
        pos = event.scenePos()
        row, col = self.getGridAtPoint(pos)
        status = self.statusAtGrid(row, col)
        self.interactGridItem(row, col, pos)
        #if(self.itemAtGrid(row, col) is None):
            #self.addItemToGrid(row, col, None)
        #else:
        #    self.interactGridItem(row, col)

    def viewFilterStack(self, row, col, pos):
        if(self.isGridPointValid(row, col) is True):
            self.widget.filterStackWidget.drawScene(self.widget.sourceList[col-1], pos)

    def mouseMoveEvent(self, event):
        if(event.buttons() == Qt.LeftButton):
            deltaPoint = event.lastScreenPos() - event.screenPos()
            self.transform.translate(deltaPoint.x(), deltaPoint.y())
            hbar = self.widget.gridWidget.horizontalScrollBar()
            hbar.setValue(hbar.value() + deltaPoint.x())
            vbar = self.widget.gridWidget.verticalScrollBar()
            vbar.setValue(vbar.value() + deltaPoint.y())

        row, col = self.getGridAtPoint(event.scenePos())
        self.drawHighlights(row, col)

    def drawHighlights(self, row, col):
        for obj in self.highlightList:
            self.removeItem(obj)
        self.highlightList.clear()

        if(self.isGridPointValid(row, col) is True):
            self.drawRowHighlight(row, QColor(255, 255, 117))
            self.drawColHighlight(col, QColor(255, 255, 117))

    def drawRowHighlight(self, row, color):
        rowObj = iSceneRowHighlight(self, row, color, self.mW)
        self.addItem(rowObj)
        self.highlightList.append(rowObj)

    def drawColHighlight(self, col, color):
        colObj = iSceneColHighlight(self, col, color, self.mW)
        self.addItem(colObj)
        self.highlightList.append(colObj)

    def isGridPointValid(self, row, col):
        if(self.widget.socketList is None):
            return False
        if(self.widget.sourceList is None):
            return False

        if(row is None):
            return False
        if(col is None):
            return False

        if row > len(self.widget.socketList) or row < 1 or col > len(self.widget.sourceList) or col < 1:
            return False
        else:
            return True

    def interactGridItem(self, row, col, pos):
        self.viewFilterStack(row, col, pos)
        #self.removeItemAtGrid(row, col)

    def removeItemAtGrid(self, row, col):
        itemHit = None
        for item in self.itemList:
            if(item.row == row and item.col == col):
                itemHit = item

        if(itemHit is not None):
            self.removeItem(itemHit)
            self.itemList.remove(itemHit)

    def clearItems(self):
        for item in self.itemList:
            self.removeItem(item)

        self.itemList.clear()

    def itemAtGrid(self, row, col):
        for item in self.itemList:
            if(item.row == row and item.col == col):
                return item

        return None

    def addItemToGrid(self, row, col, itemStatus, color='red'):
        if(self.isGridPointValid(row, col) is False):
            return
        if(self.multiConnectPlugs is False):
            self.clearCol(col)
        if(self.multiConnectSockets is False):
            self.clearRow(row)
        item = iSceneItem(self, row, col, None, color, self.mW)
        self.addItem(item)
        self.itemList.append(item)

    def clearRow(self, row):
        itemsHit = list()
        for item in self.itemList:
            if(item.row == row):
                itemsHit.append(item)

        for item in itemsHit:
            self.removeItem(item)
            self.itemList.remove(item)

    def clearCol(self, col):
        itemsHit = list()
        for item in self.itemList:
            if(item.col == col):
                itemsHit.append(item)

        for item in itemsHit:
            self.removeItem(item)
            self.itemList.remove(item)

    def statusAtGrid(self, row, col):
        return None

    def getGridAtPoint(self, point):
        row = point.y()-self.marginTop
        row = math.ceil(row / self.cellHeight)
        
        col = point.x()-self.marginLeft
        col = math.ceil(col / self.cellWidth)

        return row, col

    def getPointAtGrid(self, row, col):
        tempY = (row-1)*self.cellHeight + self.marginTop
        tempX = (col-1)*self.cellWidth + self.marginLeft
        return QPointF(tempX, tempY)

class iSceneItem(QGraphicsRectItem):
    def __init__(self, scene, row, col, status, color, mW):
        self.row = row
        self.col = col
        self.iScene = scene
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        point = self.iScene.getPointAtGrid(row, col)
        super().__init__(point.x()+2, point.y()+2, iScene.cellWidth-4, iScene.cellHeight-4)
        if(color == 'red'):
            self.setBrush(QColor(255, 0, 0))
        else:
            self.setBrush(QColor(100, 100, 100))

class iSceneRowHighlight(QGraphicsRectItem):
    def __init__(self, scene, row, color, mW):
        self.row = row
        self.color = color
        self.iScene = scene
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        point = self.iScene.getPointAtGrid(row,0)
        super().__init__(0, point.y(), self.iScene.sceneWidth(), self.iScene.cellHeight)
        self.setBrush(color)
        pen = QPen(Qt.white)
        pen.setWidth(0)
        self.setPen(pen)
        self.setZValue(-50)

class iSceneColHighlight(QGraphicsRectItem):
    def __init__(self, scene, col, color, mW):
        self.col = col
        self.color = color
        self.iScene = scene
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        point = self.iScene.getPointAtGrid(0, col)
        super().__init__(point.x(), 0, self.iScene.cellWidth, self.iScene.sceneHeight())
        self.setBrush(color)
        pen = QPen(Qt.white)
        pen.setWidth(0)
        self.setPen(pen)
        self.setZValue(-51)
