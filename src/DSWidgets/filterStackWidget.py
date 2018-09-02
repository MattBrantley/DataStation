from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, copy
from Constants import DSConstants as DSConstants
from Filter import Filter
from Sources import Source
from Sockets import Socket

class filterStackWidget(QDockWidget):
    doNotAutoPopulate = True

    def __init__(self, parent, mW):
        super().__init__('Filter Stack Editor', parent=parent)
        self.hardwareManager = parent.hardwareManager
        self.instrumentManager = parent.instrumentManager 
        self.parent = parent
        self.mW = mW
        self.hide()
        self.setAllowedAreas(Qt.NoDockWidgetArea)
        #self.setFeatures(QDockWidget.DockWidgetClosable)

        self.filterViewTransform = QTransform()
        self.filterViewScene = filterScene(self, self.filterViewTransform)
        self.filterView = filterView(self, self.filterViewScene, self.filterViewTransform)
        self.filterView.setTransform(self.filterViewTransform)

        self.setWidget(self.filterView)

    def drawScene(self, rootSource, pos):
        self.filterView.drawScene(rootSource)
        self.setWindowTitle('Filter Stack: '+ rootSource.name)
        #self.move(QPoint(pos.x() + 2, pos.y() + 2))
        self.show()

class filterView(QGraphicsView):
    filterObjList = list()
    filterColumnList = list()
    arrowList = list()
    rootSource = None
    rowBuffer = 4
    colBuffer = QPointF(0, 20)
    colGap = QPointF(10, 0)

    def __init__(self, parent, scene, transform):
        super().__init__()
        self.parent = parent
        self.mainScene = scene
        self.hardwareManager = parent.hardwareManager
        self.setScene(scene)
        self.mainTransform = transform
        self.setTransform(transform)
        self.setSceneRect(self.calcViewQRectF())
        self.drawOffset = QPoint(10, 10)
        self.columnDrawOffset = QPoint(0, 0)
        self.rowDrawOffset = QPoint(0, 0)

    def calcViewQRectF(self):
        rect = QRectF(0, 0, 400, 400)
        for object in self.filterObjList:
            bottomRightCorner = QPointF(object.pos.x() + object.rect.width(), object.pos.y() + object.rect.height())
            if(bottomRightCorner.x() > rect.width()):
                rect.setWidth(bottomRightCorner.x())
            if(bottomRightCorner.y() > rect.height()):
                rect.setHeight(bottomRightCorner.y())
        return rect

    def drawScene(self, rootSource):
        self.mainScene.clear()
        self.filterObjList.clear()
        self.drawOffset = QPoint(10, 10)
        self.rowDrawOffset = QPoint(0, 0)
        self.columnDrawOffset = QPoint(0, 0)
        self.rootSource = rootSource
        self.rootObject = filterWidgetObject(rootSource, self, self.mainScene, QColor(239, 154, 154), topRound=True)
        self.filterObjList.append(self.rootObject)

        self.drawOffset = self.drawOffset + QPoint(0, self.rowBuffer)
        self.drawOffset = self.drawOffset + QPoint(0, self.rootObject.rect.height())
        self.rootColumn = filterViewColumn(self.rootObject, self)
        self.rowDrawOffset = QPointF(0, self.rootObject.rect.height())
        self.filterColumnList.append(self.rootColumn)
        if(self.rootSource.paths[0] is not None):
            self.rootSource.paths[0].walkPathsForDraw(self.rootColumn, self, False)

        self.rootColumn.drawAtDepth()
        self.setSceneRect(self.calcViewQRectF())
        self.scene().update(self.calcViewQRectF())

    def addFilterObject(self, filterObj, branchRoot, curColumn):
        if(issubclass(type(filterObj), Filter)):
            filterObject = filterWidgetObject(filterObj, self, self.mainScene, QColor(165, 214, 167), topRound=False)
        if(issubclass(type(filterObj), Socket)):
            filterObject = filterWidgetObject(filterObj, self, self.mainScene, QColor(129, 212, 250), botRound=True)
        self.filterObjList.append(filterObject)

        if(branchRoot is True):
            newCol = filterViewColumn(filterObject, self)
            self.filterColumnList.append(newCol)
            curColumn.addChildCol(newCol)
            self.columnDrawOffset = self.columnDrawOffset + QPointF(filterObject.rect.width(), 0) + self.colGap
            self.rowDrawOffset = QPointF(0, 0)
            filterObject.setPosOffset(self.rowDrawOffset + self.columnDrawOffset)
            self.rowDrawOffset = QPointF(0, filterObject.rect.height())
            return newCol, filterObject
        else:
            curColumn.addObj(filterObject)
            filterObject.setPosOffset(self.rowDrawOffset + self.columnDrawOffset)
            self.rowDrawOffset = self.rowDrawOffset + QPointF(0, filterObject.rect.height())
            return curColumn, filterObject

    def drawColumn(self, filterObjList, rootObject):
        if(rootObject.sourceObject.filterInputSource is not None and rootObject.sourceObject.filterInputPathNo is not None):
            pathArrow = rootObject.sourceObject.filterInputSource.filterObject.pointOfPathArrow(rootObject.sourceObject.filterInputPathNo) 
            adjPathArrow = pathArrow + QPointF(rootObject.sourceObject.filterInputSource.filterObject.arrowSize, rootObject.sourceObject.filterInputSource.filterObject.arrowSize/2)
            offset = self.colBuffer + QPointF(0, pathArrow.y())

            arrow = arrowObject(None, adjPathArrow, rootObject.pos + offset + QPointF(rootObject.rect.width()/2, 0))
            self.scene().addItem(arrow)
            self.arrowList.append(arrow)
        else:
            offset = QPointF(0,0) + self.colBuffer

        for filterObj in filterObjList:
            filterObj.drawObject(offset)
        
class filterViewColumn():
    def __init__(self, rootObject, view):
        self.childCols = list()
        self.rootObject = rootObject
        self.view = view
        self.objectList = list()
        self.addObj(self.rootObject)
        self.drawPoint = QPoint(0, 0)

    def addObj(self, obj):
        self.objectList.append(obj)

    def addChildCol(self, col):
        self.childCols.append(col)

    def drawAtDepth(self):
        self.view.drawColumn(self.objectList, self.rootObject)
        for child in self.childCols:
            child.drawAtDepth()

class filterScene(QGraphicsScene):

    def __init__(self, widget, transform):
        super().__init__()
        self.widget = widget
        self.transform = transform

    def mouseMoveEvent(self, event):
        if(event.buttons() == Qt.LeftButton):
            deltaPoint = event.lastScreenPos() - event.screenPos()
            self.transform.translate(deltaPoint.x(), deltaPoint.y())
            hbar = self.widget.filterView.horizontalScrollBar()
            hbar.setValue(hbar.value() + deltaPoint.x())
            vbar = self.widget.filterView.verticalScrollBar()
            vbar.setValue(vbar.value() + deltaPoint.y())

class filterWidgetObject():

    def __init__(self, sourceObject, view, scene, color, topRound=False, botRound=False, topRadius=5, botRadius=5):
        self.sourceObject = sourceObject
        self.view = view
        self.scene = scene
        self.arrowGap = 20
        self.rect = QRectF()
        self.backgroundBrush = QBrush(color)
        self.topRound = topRound
        self.botRound = botRound
        self.topRadius = topRadius
        self.botRadius = botRadius
        self.arrowSize = 16
        self.pos = QPointF(0, 0)
        self.rect = QRectF(0, 0, 250, 80 + self.arrowGap*(len(self.sourceObject.paths)-1))
        self.arrowList = list()

        self.type = "Unknown"
        if(issubclass(type(self.sourceObject), Filter)):
            self.type = "Filter"
            self.descString = 'Filter: ' + self.sourceObject.filterType
        if(issubclass(type(self.sourceObject), Source)):
            self.type = "Source"
            self.descString = str(type(self.sourceObject).__name__) + ': ' + self.sourceObject.name
        if(issubclass(type(self.sourceObject), Socket)):
            self.type = "Socket"
            self.descString = "Socket: " + self.sourceObject.name

    def pointOfPathArrow(self, pathNum):
        for arrow in self.arrowList:
            if(arrow.pathNo == pathNum):
                return QPointF(arrow.pos.x(), arrow.pos.y())
        else:
            return QPointF(0, 0)

    def setPosOffset(self, pos):
        self.pos = pos

    def drawObject(self, colOffset):
        self.pos = self.pos + colOffset
        self.rect.translate(self.pos)
        self.boxOutline = roundedRectObject(self, self.rect, 20, self.topRound, self.botRound, self.backgroundBrush)

        self.descStringObject = QGraphicsSimpleTextItem(self.descString)
        self.descStringObject.setPos(self.pos + QPoint(10, 10))
        self.scene.addItem(self.descStringObject)

        if(self.type != "Source"):
            buttonSize = 12
            self.xButton = closeObject(self, buttonSize, self.pos + QPoint(self.rect.width()-buttonSize-10, 10))
            self.xButton.setZValue(10)
            self.scene.addItem(self.xButton)

        rightArrowPos = QPointF(self.rect.width()-self.arrowSize, self.rect.height()-self.arrowSize-15)
        pathNo = 1
        for path in self.sourceObject.paths:
            if(pathNo == 1):
                botArrowPos = QPointF(self.rect.width()/2 - self.arrowSize/2, self.rect.height() - self.arrowSize)
                arrow = triangleObject(self, self.arrowSize, 'down', self.pos + botArrowPos, pathNo)
            else:
                arrow = triangleObject(self, self.arrowSize, 'right', self.pos + rightArrowPos, pathNo)
                rightArrowPos.setY(rightArrowPos.y() - self.arrowGap)
            
            pathNo = pathNo + 1
            arrow.setZValue(5)
            self.scene.addItem(arrow)
            self.arrowList.append(arrow)

        self.scene.addItem(self.boxOutline)

    def closeButton(self):
        self.sourceObject.callRemove()
        self.view.drawScene(self.view.rootSource)

    def addFilter(self, Filter, pathNo):
        tempFilter = type(Filter)(self.view.parent.hardwareManager)
        tempFilter.onCreationParent()
        self.sourceObject.addFilter(pathNo, tempFilter)
        self.view.drawScene(self.view.rootSource)

    def addSocket(self, socket, pathNo):
        socket.socket.unattach()
        self.sourceObject.attachSocket(pathNo, socket.socket)
        socket.socket.onAttach(self.sourceObject)
        self.view.drawScene(self.view.rootSource)
        self.view.parent.mW.hardwareWidget.iScene.connectPlugsAndSockets()

    def arrowPressed(self, pathNo, pos):
        menu = QMenu()

        addFilterMenu = menu.addMenu('Add Filter')
        filterMenuAction = filterSelectionWidget(self, menu, pathNo)
        addSocketMenu = menu.addMenu("Add Socket")
        socketMenuAction = socketSelectionWidget(self, menu, pathNo)
        addFilterMenu.addAction(filterMenuAction)
        addSocketMenu.addAction(socketMenuAction)
        action = menu.exec_(pos)

    def mousePressed(self, pos):
        pass

    def checkColliders(self, pos):
        if(self.rect.contains(pos)):
            return True
        else:
            return False

class filterSelectionWidget(QWidgetAction):
    def __init__(self, parent, menu, pathNo):
        super().__init__(None)
        self.parent = parent
        self.menu = menu
        self.pathNo = pathNo
        self.pWidget = QWidget()
        self.pLayout = QVBoxLayout()
        #self.pLabel = QLabel("Filters:")
        #self.pLayout.addWidget(self.pLabel)
        self.pSpinBox = QListWidget()
        self.pSpinBox.itemClicked.connect(self.itemClicked)
        self.pLayout.addWidget(self.pSpinBox)
        self.pWidget.setLayout(self.pLayout)

        self.setDefaultWidget(self.pWidget)

        self.populateBox()

    def itemClicked(self):
        curItem = self.pSpinBox.currentItem()
        self.parent.addFilter(curItem.filterClass, self.pathNo)
        self.menu.close()

    def populateBox(self):
        for filterClass in self.parent.view.parent.hardwareManager.filtersAvailable:
            item = filterSelectionItem(filterClass.filterType, filterClass)
            self.pSpinBox.addItem(item)

class filterSelectionItem(QListWidgetItem):
    def __init__(self, name, filterClass):
        super().__init__(name)
        self.name = name
        self.filterClass = filterClass

class socketSelectionWidget(QWidgetAction):
    def __init__(self, parent, menu, pathNo):
        super().__init__(None)
        self.parent = parent
        self.menu = menu
        self.pathNo = pathNo
        self.pWidget = QWidget()
        self.pLayout = QVBoxLayout()
        #self.pLabel = QLabel("Sockets:")
        #self.pLayout.addWidget(self.pLabel)
        self.pSpinBox = QListWidget()
        self.pSpinBox.itemClicked.connect(self.itemClicked)
        self.pLayout.addWidget(self.pSpinBox)
        self.pWidget.setLayout(self.pLayout)

        self.setDefaultWidget(self.pWidget)

        self.populateBox()

    def itemClicked(self):
        curItem = self.pSpinBox.currentItem()
        self.parent.addSocket(curItem, self.pathNo)
        self.menu.close()

    def populateBox(self):
        for socket in self.parent.view.parent.mW.instrumentWidget.instrumentManager.currentInstrument.getSockets():
            item = socketSelectionItem(socket.name, socket)
            self.pSpinBox.addItem(item)

class socketSelectionItem(QListWidgetItem):
    def __init__(self, name, socket):
        super().__init__(name)
        self.name = name
        self.socket = socket

class closeObject(QGraphicsPolygonItem):

    def __init__(self, Object, size, pos):
        super().__init__()
        self.object = Object
        self.pos = pos
        self.size = size

        self.poly = QPolygonF()
        self.poly.append(pos + QPointF(0, 0))
        self.poly.append(pos + QPointF(0, size))
        self.poly.append(pos + QPointF(size, size))
        self.poly.append(pos + QPointF(size, 0))
        self.poly.append(pos + QPoint(0, 0))

        self.setPolygon(self.poly)

    def mousePressEvent(self, event):
        if(self.contains(event.pos())):
            event.accept()
            self.object.closeButton()

    def paint(self, painter, options, widget=None):
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        brush = QBrush(QColor(255, 100, 100))
        painter.setBrush(brush)
        path.addPolygon(self.poly)
        painter.drawPath(path.simplified())

        pen = QPen(Qt.black, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)

        painter.drawPolygon(self.poly)
        painter.drawLine(self.pos.x() + 2, self.pos.y() + 2, self.pos.x() + self.size - 2, self.pos.y()+self.size - 2)
        painter.drawLine(self.pos.x() + self.size - 2, self.pos.y() + 2, self.pos.x() + 2, self.pos.y()+self.size - 2)

class arrowObject(QGraphicsPolygonItem):

    def __init__(self, column, start, end):
        super().__init__()
        self.column = column
        self.start = start
        self.end = end

    def paint(self, painter, options, widget=None):
        pen = QPen(Qt.darkGray, 2, Qt.DashLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self.start.x(), self.start.y(), self.end.x(), self.start.y())
        painter.drawLine(self.end.x(), self.start.y(), self.end.x(), self.end.y())
        super().paint(painter, options, widget)

class triangleObject(QGraphicsPolygonItem):

    def __init__(self, Object, size, direction, pos, pathNo):
        super().__init__()
        self.object = Object
        self.pos = pos
        self.pathNo = pathNo
        self.size = size
        self.direction = direction
        self.poly = QPolygonF()

        if(self.direction == 'right'):
            self.poly.append(pos + QPointF(0, 0))
            self.poly.append(pos + QPointF(0, self.size))
            self.poly.append(pos + QPointF(self.size, self.size/2))
            self.poly.append(pos + QPointF(0, 0))
        if(self.direction == 'down'):
            self.poly.append(pos + QPointF(0, 0))
            self.poly.append(pos + QPointF(self.size/2, self.size))
            self.poly.append(pos + QPointF(self.size, 0))
            self.poly.append(pos + QPointF(0, 0))

        self.setPolygon(self.poly)

    def checkCollide(self, pos):
        if(self.contains(pos)):
            return True
        else:
            return False

    def mousePressEvent(self, event):
        if(self.checkCollide(event.pos())):
            event.accept()
            self.object.arrowPressed(self.pathNo, event.screenPos())

class roundedRectObject(QGraphicsRectItem):

    def __init__(self, Object, rect, radius, topRound, botRound, brush):
        super().__init__(rect)
        self.object = Object
        self.rect = rect
        self.radius = radius
        self.topRound = topRound
        self.botRound = botRound
        self.brush = brush
        self.setZValue(-30)

    def mousePressEvent(self, event):
        event.accept()
        self.object.mousePressed(event.pos())

    def paint(self, painter, option, widget=None):
        pen = QPen(Qt.black, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        painter.setBrush(self.brush)
        painter.setPen(pen)
        path.addRoundedRect(self.rect, self.radius, self.radius)

        if(self.topRound is False):
            path.addRoundedRect(self.rect.adjusted(0, 0, 0, -self.radius), 6, 6)

        if(self.botRound is False):
            path.addRoundedRect(self.rect.adjusted(0, self.radius, 0, 0), 6, 6)

        painter.drawPath(path.simplified())