from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, copy
from src.Constants import DSConstants as DSConstants
from src.Managers.InstrumentManager.Filter import Filter
from src.Managers.InstrumentManager.Sockets import Socket
from src.Managers.HardwareManager.Sources import Source

class filterStackWidget(QDockWidget):
    doNotAutoPopulate = True

    def __init__(self, mW):
        super().__init__('Filter Stack Editor', parent=mW)
        self.mW = mW
        self.hM = mW.hM
        self.iM = mW.iM
        self.wM = mW.wM
        self.hide()
        self.setAllowedAreas(Qt.NoDockWidgetArea)

        self.filterViewTransform = QTransform()
        self.filterViewScene = filterScene(self, self.filterViewTransform)
        self.filterView = filterView(self, self.filterViewScene, self.filterViewTransform)
        self.filterView.setTransform(self.filterViewTransform)

        self.setWidget(self.filterView)

        self.iM.Socket_Attached.connect(self.drawScene)
        self.iM.Socket_Detatched.connect(self.drawScene)
        self.hM.Filter_Attached.connect(self.drawScene)
        self.hM.Filter_Detatched.connect(self.drawScene)

        self.mW.DataStation_Loaded.connect(self.hide)

    def setSource(self, rootSource):
        self.rootSource = rootSource
        self.setWindowTitle('Filter Stack: '+ rootSource.Get_Name())

    def drawScene(self):
        self.filterView.drawScene(self.rootSource)

class filterView(QGraphicsView):
    filterObjList = list()
    filterColumnList = list()
    arrowList = list()
    rootSource = None
    rowBuffer = 4
    colBuffer = QPointF(0, 20)
    colGap = QPointF(10, 0)

    def __init__(self, mW, scene, transform):
        super().__init__()
        self.mW = mW
        self.hM = mW.hM
        self.iM = mW.iM
        self.wM = mW.wM
        self.mainScene = scene
        self.setScene(scene)
        self.mainTransform = transform
        self.setTransform(transform)
        self.setSceneRect(self.calcViewQRectF())
        self.drawOffset = QPoint(10, 10)
        self.columnDrawOffset = QPoint(0, 0)
        self.rowDrawOffset = QPoint(0, 0)
        self.filterObjectList = list()
        self.lastWidth = QPoint(0,0)

    def calcViewQRectF(self):
        rect = QRectF(0, 0, 400, 400)
        for object in self.filterObjList:
            bottomRightCorner = QPointF(object.pos.x() + object.rect.width(), object.pos.y() + object.rect.height())
            if(bottomRightCorner.x() > rect.right()):
                rect.setWidth(bottomRightCorner.x())
            if(bottomRightCorner.y() > rect.bottom()):
                rect.setHeight(bottomRightCorner.y())
        return rect

    def drawScene(self, source):
        self.filterObjectList.clear()

        self.columnDrawOffset = QPoint(0,0)
        self.mainScene.clear()
        self.walkColumn(source, QPoint(0,0))

        self.setSceneRect(self.calcViewQRectF())
        self.scene().update(self.calcViewQRectF())
    
    def drawColumn(self, objList, offset, new):
        drawObjects = list()
        self.rowDrawOffset = QPoint(0, offset.y())
        maxWidth = 0
        
        rowTopPoint = QPoint(self.rowDrawOffset)

        for obj in objList:
            if(issubclass(type(obj), Source)):
                drawObj = sourceWidgetObject(self.mW, obj, self, self.mainScene)
                self.filterObjList.append(drawObj)
            if(issubclass(type(obj), Filter)):
                drawObj = filterWidgetObject(self.mW, obj, self, self.mainScene)
                self.filterObjList.append(drawObj)
            if(issubclass(type(obj), Socket)):
                drawObj = socketWidgetObject(self.mW, obj, self, self.mainScene)
                self.filterObjList.append(drawObj)
            drawObjects.append(drawObj)
            if(drawObj.rect.width() > maxWidth):
                maxWidth = drawObj.rect.width()
            
            drawObj.drawObject(self.drawOffset + self.rowDrawOffset + self.columnDrawOffset)

            self.rowDrawOffset += QPoint(0, drawObj.rect.height())

        if(new is True): ### ARROWS ARE STILL WEIRD
            arrow = arrowObject(offset, self.drawOffset+rowTopPoint+self.columnDrawOffset+QPoint(maxWidth/2, 0))
            self.scene().addItem(arrow)

        self.columnDrawOffset += QPoint(maxWidth + 5, 0)
        return drawObjects
    
    def walkColumn(self, obj, offset, new=False):    

        columnList = list()
        branchList = list()
        columnList.append(obj)
        while(len(self.getRefObjects(obj)) != 0):
            refObjs = self.getRefObjects(obj)

            branchSub = list() # The sockets past number 1 are actually worked opposite of displayed order!
            for i in range(obj.Get_Number_Of_Paths()-1):
                branchSub.append(None)
            obj = None

            for refObj in refObjs:
                if(refObj.Get_Input_Path_Number() == 1):
                    if(refObj is not None):
                        columnList.append(refObj)
                    obj = refObj
                else:
                    branchSub[refObj.Get_Input_Path_Number()-2] = refObj
            branchList.append(branchSub)
        
        ref = self.drawColumn(columnList, offset, new) ### OFFSETS
        numBranch = len(branchList)
        branchList = reversed(branchList)
        for branch in branchList:
            numSub = 1
            for sub in branch:
                if(sub is not None):
                    self.walkColumn(sub, ref[numBranch-1].pointOfPathArrow(numSub+1) + QPoint(0, 10), new=True)
                numSub += 1
            numBranch -= 1

    def getRefObjects(self, obj):
        refList = list()
        if(obj is not None):
            if(self.iM.Get_Instrument() is not None):
                refList += self.iM.Get_Instrument().Get_Sockets(inputUUID=obj.Get_UUID())
            refList += self.hM.Get_Filters(inputUUID=obj.Get_UUID())
        return refList

    def addFilterObject(self, filterObj, branchRoot, curColumn):
        if(issubclass(type(filterObj), Filter)):
            filterObject = filterWidgetObject(filterObj, self, self.mainScene)
            self.filterObjList.append(filterObject)
        if(issubclass(type(filterObj), Socket)):
            socketObject = socketWidgetObject(filterObj, self, self.mainScene)
            self.filterObjList.append(socketObject)

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

class widgetObject():

    def __init__(self, mW, sourceObject, view, scene, color, topRound=False, botRound=False, topRadius=5, botRadius=5):
        self.mW = mW
        self.hM = mW.hM
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
        self.arrowList = list()

    def pointOfPathArrow(self, pathNum):
        for arrow in self.arrowList:
            if(arrow.pathNo == pathNum):
                return QPointF(arrow.pos.x()+self.arrowSize, arrow.pos.y())
        else:
            return QPointF(0, 0)

    def setPosOffset(self, pos):
        self.pos = pos

    def drawObject(self, colOffset):
        pass

    def mousePressed(self, pos):
        pass

    def checkColliders(self, pos):
        if(self.rect.contains(pos)):
            return True
        else:
            return False

    def arrowPressed(self, pathNo, pos):
        menu = QMenu()

        addFilterMenu = menu.addMenu('Add Filter')
        filterMenuAction = filterSelectionWidget(self, menu, pathNo, self.mW)
        addSocketMenu = menu.addMenu("Add Socket")
        socketMenuAction = socketSelectionWidget(self, menu, pathNo, self.mW)
        addFilterMenu.addAction(filterMenuAction)
        addSocketMenu.addAction(socketMenuAction)
        action = menu.exec_(pos)

    def addFilter(self, item, pathNo):
        newfilter = self.hM.Add_Filter(item.filterModel)
        if(newfilter is not None):
            newfilter.Attach_Input(self.sourceObject.Get_UUID(), pathNo)

    def addSocket(self, item, pathNo):
        item.socket.Attach_Input(self.sourceObject.Get_UUID(), pathNo)

class filterWidgetObject(widgetObject):
    def __init__(self, mW, sourceObject, view, scene):
        super().__init__(mW, sourceObject, view, scene, QColor(165, 214, 167))
        self.sourceObject = sourceObject
        self.mW = mW
        self.rect = QRectF(0, 0, 250, 80 + self.arrowGap*(self.sourceObject.Get_Number_Of_Paths()-1))
        self.type = "Filter"
        self.descString = 'Filter: ' + self.sourceObject.Get_Type()
    
    def drawObject(self, colOffset):
        self.pos = self.pos + colOffset
        self.rect.translate(self.pos)
        self.boxOutline = roundedRectObject(self, self.rect, 20, self.topRound, self.botRound, self.backgroundBrush)

        self.descStringObject = QGraphicsSimpleTextItem(self.descString)
        self.descStringObject.setPos(self.pos + QPoint(10, 10))
        self.scene.addItem(self.descStringObject)

        buttonSize = 12
        self.xButton = closeObject(self, buttonSize, self.pos + QPoint(self.rect.width()-buttonSize-10, 10))
        self.xButton.setZValue(10)
        self.scene.addItem(self.xButton)

        rightArrowPos = QPointF(self.rect.width()-self.arrowSize, self.rect.height()-self.arrowSize-15)
        for i in range(self.sourceObject.Get_Number_Of_Paths()):
            pathNo = i+1
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
        self.sourceObject.Remove()

class sourceWidgetObject(widgetObject):
    def __init__(self, mW, sourceObject, view, scene):
        super().__init__(mW, sourceObject, view, scene, QColor(239, 154, 154), topRound=True)
        self.mW = mW
        self.rect = QRectF(0, 0, 250, 80)
        self.type = "Source"
        self.descString = str(type(self.sourceObject).__name__) + ': ' + self.sourceObject.Get_Name()
    
    def drawObject(self, colOffset):
        self.pos = self.pos + colOffset
        self.rect.translate(self.pos)
        self.boxOutline = roundedRectObject(self, self.rect, 20, self.topRound, self.botRound, self.backgroundBrush)

        self.descStringObject = QGraphicsSimpleTextItem(self.descString)
        self.descStringObject.setPos(self.pos + QPoint(10, 10))
        self.scene.addItem(self.descStringObject)

        botArrowPos = QPointF(self.rect.width()/2 - self.arrowSize/2, self.rect.height() - self.arrowSize)
        arrow = triangleObject(self, self.arrowSize, 'down', self.pos + botArrowPos, 1)
        arrow.setZValue(5)
        self.scene.addItem(arrow)
        self.arrowList.append(arrow)

        self.scene.addItem(self.boxOutline)

class socketWidgetObject(widgetObject):
    def __init__(self, mW, sourceObject, view, scene):
        super().__init__(mW, sourceObject, view, scene, QColor(129, 212, 250), botRound=True)
        self.sourceObject = sourceObject
        self.mW = mW
        self.rect = QRectF(0, 0, 250, 80)
        self.type = "Socket"
        self.descString = "Socket: " + self.sourceObject.Get_Name()
    
    def drawObject(self, colOffset):
        self.pos = self.pos + colOffset
        self.rect.translate(self.pos)
        self.boxOutline = roundedRectObject(self, self.rect, 20, self.topRound, self.botRound, self.backgroundBrush)

        self.descStringObject = QGraphicsSimpleTextItem(self.descString)
        self.descStringObject.setPos(self.pos + QPoint(10, 10))
        self.scene.addItem(self.descStringObject)

        buttonSize = 12
        self.xButton = closeObject(self, buttonSize, self.pos + QPoint(self.rect.width()-buttonSize-10, 10))
        self.xButton.setZValue(10)
        self.scene.addItem(self.xButton)

        self.scene.addItem(self.boxOutline)

    def closeButton(self):
        self.sourceObject.Detatch_Input()

class filterSelectionWidget(QWidgetAction):
    def __init__(self, parent, menu, pathNo, mW):
        super().__init__(None)
        super().__init__(None)
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.parent = parent
        self.menu = menu
        self.pathNo = pathNo
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
        self.parent.addFilter(curItem, self.pathNo)
        self.menu.close()

    def populateBox(self):
        for filterModel in self.hM.Get_Filter_Models_Available():
            item = filterSelectionItem(filterModel.Get_Type(), filterModel)
            self.pSpinBox.addItem(item)

class filterSelectionItem(QListWidgetItem):
    def __init__(self, name, filterModel):
        super().__init__(name)
        self.name = name
        self.filterModel = filterModel

class socketSelectionWidget(QWidgetAction):
    def __init__(self, parent, menu, pathNo, mW):
        super().__init__(None)
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.parent = parent
        self.menu = menu
        self.pathNo = pathNo
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
        self.parent.addSocket(curItem, self.pathNo)
        self.menu.close()

    def populateBox(self):
        if(self.iM.Get_Instrument() is not None):
            for socket in self.iM.Get_Instrument().Get_Sockets():
                item = socketSelectionItem(socket.Get_Name(), socket) ##This is where we would alert if they are connect!
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

    def __init__(self, start, end):
        super().__init__()
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