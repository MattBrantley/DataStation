from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, copy
from src.Constants import DSConstants as DSConstants
from filterStackWidget import filterStackWidget
from src.Managers.InstrumentManager.Sockets import AOSocket, AISocket, DOSocket, DISocket
from src.Managers.HardwareManager.Sources import AOSource, AISource, DOSource, DISource

class gridViewWidget(QWidget):
    doNotAutoPopulate = True

    def __init__(self, dockWidget, ds):
        super().__init__()
        self.dockWidget = dockWidget
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM

        self.socketList = list()
        self.sourceList = list()

        self.filterStackWidget = filterStackWidget(dockWidget, self.ds)
        self.filterStackWidget.setObjectName('filterStackWidget')
        self.dockWidget.Get_Window().addDockWidget(Qt.BottomDockWidgetArea, self.filterStackWidget)
        self.filterStackWidget.hide()
        self.filterStackWidget.setFloating(True)

        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.gridCombo = QComboBox()
        self.gridCombo.addItem('Sockets: Analog Output')
        self.gridCombo.addItem('Sockets: Analog Input')
        self.gridCombo.addItem('Sockets: Digital Output')
        self.gridCombo.addItem('Sockets: Digital Input')
        self.gridCombo.currentTextChanged.connect(self.drawScene)
        self.mainLayout.addWidget(self.gridCombo)

        self.gridWidget = QGraphicsView()
        self.gridTransform = QTransform()
        self.gridWidget.setTransform(self.gridTransform)
        self.iScene = iScene(self, self.gridTransform, self.ds)
        gridRect = QRectF(0, 0, 1600, 1600)
        self.gridWidget.setSceneRect(gridRect)
        self.gridWidget.setScene(self.iScene)

        self.mainLayout.addWidget(self.gridWidget)
        
        self.iM.Socket_Attached.connect(self.drawScene)
        self.iM.Socket_Detatched.connect(self.drawScene)
        self.iM.Socket_Added.connect(self.drawScene)
        self.hM.Source_Added.connect(self.drawScene)

        self.drawScene()

    def repopulateSocketsAndPlugs(self):
        self.socketList = list()
        self.sourceList = list()
        for instrument in self.iM.Get_Instruments():
            if(self.gridCombo.currentText() == 'Sockets: Analog Output'):
                self.socketList += instrument.Get_Sockets(socketType=AOSocket)
                self.sourceList = self.hM.Get_Sources(sourceType=AOSource)
            if(self.gridCombo.currentText() == 'Sockets: Analog Input'):
                self.socketList += instrument.Get_Sockets(socketType=AISocket)
                self.sourceList = self.hM.Get_Sources(sourceType=AISource)
            if(self.gridCombo.currentText() == 'Sockets: Digital Output'):
                self.socketList += instrument.Get_Sockets(socketType=DOSocket)
                self.sourceList = self.hM.Get_Sources(sourceType=DOSource)
            if(self.gridCombo.currentText() == 'Sockets: Digital Input'):
                self.socketList += instrument.Get_Sockets(socketType=DISocket)
                self.sourceList = self.hM.Get_Sources(sourceType=DISource)

    def drawScene(self):
        self.repopulateSocketsAndPlugs()
        self.iScene.itemList.clear()
        self.iScene.redrawn()
        self.iScene.clear()
        rows = len(self.sourceList)
        cols = len(self.socketList)
        totalWidth = cols * self.iScene.cellWidth
        totalHeight = rows * self.iScene.cellHeight
        gridRect = QRectF(0, 0, totalWidth + self.iScene.marginLeft + 10, totalHeight + self.iScene.marginTop + 10)
        self.gridWidget.setSceneRect(gridRect)

        labelFont = QFont()
        labelFont.setBold(True)
        labelFont.setPointSize(12)

        socketlabel = self.iScene.addText('SOCKETS')
        socketlabel.setFont(labelFont)
        socketlabel.setPos(self.iScene.marginLeft + totalWidth/2 - socketlabel.boundingRect().width()/2, 0)

        transformSourcelabel = QTransform()
        transformSourcelabel.rotate(270)

        sourcelabel = self.iScene.addText('SOURCES')
        sourcelabel.setFont(labelFont)
        sourcelabel.setTransform(transformSourcelabel)
        sourcelabel.setPos(0, self.iScene.marginTop + totalHeight/2 + sourcelabel.boundingRect().width()/2)

        offsetY = self.iScene.marginTop
        self.iScene.addLine(self.iScene.marginLeft, offsetY, self.iScene.marginLeft+totalWidth, offsetY)

        for source in self.sourceList:
            text = self.iScene.addText(source.Get_Name())
            text.setPos(self.iScene.marginLeft - text.boundingRect().width(), offsetY)
            
            offsetY = offsetY + self.iScene.cellWidth
            self.iScene.addLine(self.iScene.marginLeft, offsetY, self.iScene.marginLeft+totalWidth, offsetY)

        offsetX = self.iScene.marginLeft
        self.iScene.addLine(offsetX, self.iScene.marginTop, offsetX, self.iScene.marginTop+totalHeight)
        transformTopText = QTransform()
        transformTopText.rotate(270)

        for socket in self.socketList:
            text = self.iScene.addText(socket.Get_Name())
            text.setTransform(transformTopText)
            text.setPos(offsetX + text.boundingRect().height() - self.iScene.cellWidth, self.iScene.marginTop)

            offsetX = offsetX + self.iScene.cellHeight
            self.iScene.addLine(offsetX, self.iScene.marginTop, offsetX, self.iScene.marginTop+totalHeight)

        self.iScene.connectPlugsAndSockets()

class iScene(QGraphicsScene):
    marginLeft = 150
    marginTop = 150
    cellHeight = 20
    cellWidth = 20
    multiConnectPlugs = True
    multiConnectSockets = True
    itemList = list()
    highlightList = list()

    def __init__(self, widget, transform, ds):
        super().__init__()
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM
        self.widget = widget
        self.transform = transform

    def redrawn(self):
        self.highlightList.clear()

    def sceneWidth(self):
        return len(self.widget.socketList)*self.cellWidth + self.marginLeft

    def sceneHeight(self):
        return len(self.widget.sourceList)*self.cellHeight + self.marginTop

    def connectPlugsAndSockets(self):
        #self.widget.ds.controlWidget.configChanged()
        self.clearItems()
        for socket in self.widget.socketList:
            #if(socket.cP.isTriggerComponent is True):
            #    for source in self.widget.sourceList:
            #        if(source.trigger == False):
            #            self.addItemToGrid(self.getSocketRow(socket), self.getPlugCol(source), None, color='grey')

            source = socket.getSource()
            if(source is not None):
                row = self.getSourceRow(source)
                col = self.getSocketColumn(socket)
                if(row is not None and col is not None):
                    self.addItemToGrid(col, row, None)

    def getSourceRow(self, sourceIn):
        index = 1
        for source in self.widget.sourceList:
            if(source == sourceIn):
                return index
            index = index + 1

        return None

    def getSocketColumn(self, socketIn):
        index = 1
        for socket in self.widget.socketList:
            if(socket == socketIn):
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
        if(self.isGridPointValid(col, row) is True):
            self.widget.filterStackWidget.setSource(self.widget.sourceList[col-1])
            self.widget.filterStackWidget.drawScene()
            self.widget.filterStackWidget.show()

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
        rowObj = iSceneRowHighlight(self, row, color, self.ds)
        self.addItem(rowObj)
        self.highlightList.append(rowObj)

    def drawColHighlight(self, col, color):
        colObj = iSceneColHighlight(self, col, color, self.ds)
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

        if row > len(self.widget.sourceList) or row < 1 or col > len(self.widget.socketList) or col < 1:
            return False
        else:
            return True

    def interactGridItem(self, row, col, pos):
        self.viewFilterStack(col, row, pos)
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
        if(self.isGridPointValid(col, row) is False):
            return
        if(self.multiConnectPlugs is False):
            self.clearCol(col)
        if(self.multiConnectSockets is False):
            self.clearRow(row)
        item = iSceneItem(self, col, row, None, color, self.ds)
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
    def __init__(self, scene, row, col, status, color, ds):
        self.row = row
        self.col = col
        self.iScene = scene
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM
        point = self.iScene.getPointAtGrid(row, col)
        super().__init__(point.x()+2, point.y()+2, iScene.cellWidth-4, iScene.cellHeight-4)
        if(color == 'red'):
            self.setBrush(QColor(255, 0, 0))
        else:
            self.setBrush(QColor(100, 100, 100))

class iSceneRowHighlight(QGraphicsRectItem):
    def __init__(self, scene, row, color, ds):
        self.row = row
        self.color = color
        self.iScene = scene
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM
        point = self.iScene.getPointAtGrid(row,0)
        super().__init__(0, point.y(), self.iScene.sceneWidth(), self.iScene.cellHeight)
        self.setBrush(color)
        pen = QPen(Qt.white)
        pen.setWidth(0)
        self.setPen(pen)
        self.setZValue(-50)

class iSceneColHighlight(QGraphicsRectItem):
    def __init__(self, scene, col, color, ds):
        self.col = col
        self.color = color
        self.iScene = scene
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM
        point = self.iScene.getPointAtGrid(0, col)
        super().__init__(point.x(), 0, self.iScene.cellWidth, self.iScene.sceneHeight())
        self.setBrush(color)
        pen = QPen(Qt.white)
        pen.setWidth(0)
        self.setPen(pen)
        self.setZValue(-51)
