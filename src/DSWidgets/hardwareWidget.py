from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, time
from Constants import DSConstants as DSConstants
from DSWidgets.filterStackWidget import filterStackWidget

class hardwareWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole
    socketList = list()
    plugList = list()

    def __init__(self, mW, instrumentManager, hardwareManager):
        super().__init__('Hardware')
        self.mW = mW
        self.instrumentManager = instrumentManager
        self.hardwareManager = hardwareManager

        self.hide()
        self.resize(800, 800)
        self.toolbar = QToolBar()

        self.mainContainer = QMainWindow()
        self.mainContainer.addToolBar(self.toolbar)

        self.driversWidget = QWidget()

        self.filtersWidget = QWidget()

        self.hardwareWidget = hardwareListWidget(self, self.hardwareManager)

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
        self.iScene = iScene(self, self.gridTransform)
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

        self.hardwareManager.Hardware_Modified.connect(self.drawScene)
        self.instrumentManager.Instrument_Unloaded.connect(self.drawScene)
        self.instrumentManager.Instrument_Loaded.connect(self.drawScene)
        self.instrumentManager.Instrument_Modified.connect(self.drawScene)

        self.drawScene()

    def repopulateSocketsAndPlugs(self):        
        typeText = self.gridCombo.currentText()
            
        self.plugList = self.hardwareManager.getSourceObjs(typeText)
        if(self.instrumentManager.currentInstrument is not None):
            self.socketList = self.instrumentManager.currentInstrument.getSocketsByType(typeText)
        else:
            self.socketList = list()

    def drawScene(self):
        self.repopulateSocketsAndPlugs()
        self.iScene.itemList.clear()
        self.iScene.redrawn()
        self.iScene.clear()
        rows = len(self.socketList)
        cols = len(self.plugList)
        totalWidth = cols * self.iScene.cellWidth
        totalHeight = rows * self.iScene.cellHeight
        gridRect = QRectF(0, 0, totalWidth + self.iScene.marginLeft + 10, totalHeight + self.iScene.marginTop + 10)
        self.gridWidget.setSceneRect(gridRect)

        labelFont = QFont()
        labelFont.setBold(True)
        labelFont.setPointSize(12)

        plugLabel = self.iScene.addText('PLUGS')
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
            text = self.iScene.addText(socket.name)
            text.setPos(self.iScene.marginLeft - text.boundingRect().width(), offsetY)
            
            offsetY = offsetY + self.iScene.cellWidth
            self.iScene.addLine(self.iScene.marginLeft, offsetY, self.iScene.marginLeft+totalWidth, offsetY)

        offsetX = self.iScene.marginLeft
        self.iScene.addLine(offsetX, self.iScene.marginTop, offsetX, self.iScene.marginTop+totalHeight)
        transformTopText = QTransform()
        transformTopText.rotate(270)
        for plug in self.plugList:
            text = self.iScene.addText(plug.name)
            text.setTransform(transformTopText)
            text.setPos(offsetX + text.boundingRect().height() - self.iScene.cellWidth, self.iScene.marginTop)

            offsetX = offsetX + self.iScene.cellHeight
            self.iScene.addLine(offsetX, self.iScene.marginTop, offsetX, self.iScene.marginTop+totalHeight)

        self.iScene.connectPlugsAndSockets()

class hardwareListWidget(QWidget):

    def __init__(self, hardwareWidget, hardwareManager):
        super().__init__()
        self.hardwareWidget = hardwareWidget
        self.hardwareManager = hardwareManager

        self.mainLayout = QVBoxLayout()
        self.hardwareList = hardwareListView(self, self.hardwareManager)
        self.setLayout(self.mainLayout)

        self.scroll = QScrollArea(self)
        self.mainLayout.addWidget(self.scroll)

        self.newButton = QPushButton("Add Hardware Object")
        self.newButton.pressed.connect(self.newButtonPressed)
        self.mainLayout.addWidget(self.newButton)

        self.mainLayout.setSpacing(2)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.hardwareList)   
        
    def newButtonPressed(self):
        menu = QMenu()

        hardwareMenuAction = hardwareSelectionWidget(self, menu)
        menu.addAction(hardwareMenuAction)
        action = menu.exec_(QCursor().pos())

    def addHardware(self, hardwareClass):
        tempHardware = type(hardwareClass)(self.hardwareManager)
        tempHardware.initHardwareWorker()
        widgetItem = hardwareListItem(self.hardwareList, self.hardwareManager, tempHardware)
        self.hardwareManager.addHardwareObj(tempHardware)
        
        self.hardwareList.addWidget(widgetItem)
        return tempHardware

class hardwareSelectionWidget(QWidgetAction):
    def __init__(self, parent, menu):
        super().__init__(None)
        self.parent = parent
        self.menu = menu
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
        self.parent.addHardware(curItem.filterClass)
        self.menu.close()

    def populateBox(self):
        for hardwareClass in self.parent.hardwareManager.driversAvailable:
            item = hardwareSelectionItem(hardwareClass.hardwareType, hardwareClass)
            self.pSpinBox.addItem(item)

class hardwareSelectionItem(QListWidgetItem):
    def __init__(self, name, filterClass):
        super().__init__(name)
        self.name = name
        self.filterClass = filterClass

class hardwareListView(QWidget):

    def __init__(self, parent, hardwareManager):
        super().__init__()
        self.parent = parent
        self.hardwareManager = hardwareManager
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

    def __init__(self, hardwareListView, hardwareManager, hardwareObj):
        super().__init__()
        self.hardwareListView = hardwareListView
        self.hardwareSelectionWidget = hardwareSelectionWidget
        self.hardwareManager = hardwareManager
        self.hardwareObj = hardwareObj
        self.msgWidget = driverMessageWidget()

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
        self.botPortionLayout.addWidget(self.sourceLabel)
        self.botPortionLayout.addWidget(self.hardwareObj.sourceListWidget)

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
        self.hardwareManager.removeHardwareObj(self.hardwareObj)
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

class driverMessageWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.maximumHeight = 150

class iScene(QGraphicsScene):
    marginLeft = 150
    marginTop = 150
    cellHeight = 20
    cellWidth = 20
    multiConnectPlugs = True
    multiConnectSockets = True
    itemList = list()
    highlightList = list()

    def __init__(self, widget, transform):
        super().__init__()
        self.widget = widget
        self.transform = transform

    def redrawn(self):
        self.highlightList.clear()

    def sceneWidth(self):
        return len(self.widget.plugList)*self.cellWidth + self.marginLeft

    def sceneHeight(self):
        return len(self.widget.socketList)*self.cellHeight + self.marginTop

    def connectPlugsAndSockets(self):
        #self.widget.mW.controlWidget.configChanged()
        self.clearItems()
        for socket in self.widget.socketList:
            source = socket.getAttachedSource()
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
        for plug in self.widget.plugList:
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
            self.widget.filterStackWidget.drawScene(self.widget.plugList[col-1], pos)

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
        rowObj = iSceneRowHighlight(self, row, color)
        self.addItem(rowObj)
        self.highlightList.append(rowObj)

    def drawColHighlight(self, col, color):
        colObj = iSceneColHighlight(self, col, color)
        self.addItem(colObj)
        self.highlightList.append(colObj)

    def isGridPointValid(self, row, col):
        if(self.widget.socketList is None):
            return False
        if(self.widget.plugList is None):
            return False

        if(row is None):
            return False
        if(col is None):
            return False

        if row > len(self.widget.socketList) or row < 1 or col > len(self.widget.plugList) or col < 1:
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

    def addItemToGrid(self, row, col, itemStatus):
        if(self.isGridPointValid(row, col) is False):
            return
        if(self.multiConnectPlugs is False):
            self.clearCol(col)
        if(self.multiConnectSockets is False):
            self.clearRow(row)
        item = iSceneItem(self, row, col, None)
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
    def __init__(self, scene, row, col, status):
        self.row = row
        self.col = col
        self.iScene = scene
        point = self.iScene.getPointAtGrid(row, col)
        super().__init__(point.x()+2, point.y()+2, iScene.cellWidth-4, iScene.cellHeight-4)
        self.setBrush(QColor(255, 0, 0))

class iSceneRowHighlight(QGraphicsRectItem):
    def __init__(self, scene, row, color):
        self.row = row
        self.color = color
        self.iScene = scene
        point = self.iScene.getPointAtGrid(row,0)
        super().__init__(0, point.y(), self.iScene.sceneWidth(), self.iScene.cellHeight)
        self.setBrush(color)
        pen = QPen(Qt.white)
        pen.setWidth(0)
        self.setPen(pen)
        self.setZValue(-50)

class iSceneColHighlight(QGraphicsRectItem):
    def __init__(self, scene, col, color):
        self.col = col
        self.color = color
        self.iScene = scene
        point = self.iScene.getPointAtGrid(0, col)
        super().__init__(point.x(), 0, self.iScene.cellWidth, self.iScene.sceneHeight())
        self.setBrush(color)
        pen = QPen(Qt.white)
        pen.setWidth(0)
        self.setPen(pen)
        self.setZValue(-51)
