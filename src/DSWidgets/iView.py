import pyqtgraph as pg # This library gives a bunch of FutureWarnings that are unpleasant! Fix for this is in the main .py file header.
from PyQt5.Qt import QPixmap, QDataStream, QIODevice, QCursor
import os
from pyqtgraph import QtGui, QtCore
from pyqtgraph import Point
import numpy as np

class iView(pg.GraphicsWindow):
    def __init__(self, mainWindow, parent=None):
        super(iView, self).__init__(parent)

        self.mainWindow = mainWindow
        self.setAcceptDrops(True)
        self.view = self.addViewBox()
        self.view.setAspectLocked()
        self.view.setRange(pg.QtCore.QRectF(0, 0, 2000, 2000))
        self.view.Antialiasing = True
        self.setBackground('w')

    def dragEnterEvent(self, e):
        if(e.mimeData().text() == "compDrag"):
            e.accept()

    def dragMoveEvent(self, e):
        if(e.mimeData().text() == "compDrag"):
            e.accept()

    def dropEvent(self, e):
        windowXSize = self.viewRect().width()
        windowYSize = self.viewRect().height()
        dropXPercent = (e.pos().x()-self.viewRect().left())/windowXSize
        dropYPercent = (e.pos().y()-self.viewRect().top())/windowYSize
        dropX = (dropXPercent*self.view.viewRect().width()) + self.view.viewRect().left()
        dropY = self.view.viewRect().bottom() - (dropYPercent*self.view.viewRect().height())

        data = e.mimeData().data("application/compName")
        data2 = e.mimeData().data("application/compIndex")
        stream = QDataStream(data, QIODevice.ReadOnly)
        stream2 = QDataStream(data2, QIODevice.ReadOnly)
        text = stream.readQString()
        index = stream2.readInt()

        result = self.mainWindow.instrumentManager.addCompToInstrument(index)

        if result is not None:
            m = iViewComponent(self.mainWindow, index, result, width=1, height=1, pos=(dropX, dropY))
            self.view.addItem(m)

class ParamObj:
    # Just a helper for tracking parameters and responding to changes
    def __init__(self):
        self.__params = {}
    
    def __setitem__(self, item, val):
        self.setParam(item, val)
        
    def setParam(self, param, val):
        self.setParams(**{param:val})
        
    def setParams(self, **params):
        """Set parameters for this optic. This is a good function to override for subclasses."""
        self.__params.update(params)
        self.paramStateChanged()

    def paramStateChanged(self):
        pass

    def __getitem__(self, item):
        return self.getParam(item)

    def getParam(self, param):
        return self.__params[param]

class iViewGraphic(pg.GraphicsObject, ParamObj):
    def __init__(self, src, pen=None, brush=None, **opts):
        defaults = dict(width=2, height=2)
        defaults.update(opts)
        ParamObj.__init__(self)
        pg.GraphicsObject.__init__(self)
        
        self.pxm = QPixmap(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'User Components\img\\' + src))
        self.surfaces = [iViewGraphicBound(self.pxm.width(), self.pxm.height())]
        

        if pen is None:
            self.pen = pg.mkPen((220,220,255,200), width=1, cosmetic=True)
        else:
            self.pen = pg.mkPen(pen)
        
        if brush is None: 
            self.brush = pg.mkBrush((230, 230, 255, 30))
        else:
            self.brush = pg.mkBrush(brush)

        self.setParams(**defaults)

    def paramStateChanged(self):
        self.updateSurfaces()

    def updateSurfaces(self):
        self.surfaces[0].setParams(self.pxm.width(), self.pxm.height())
        
        self.path = QtGui.QPainterPath()
        self.path.connectPath(self.surfaces[0].path.translated(self.surfaces[0].pos()))
        self.path.closeSubpath()
        
    def boundingRect(self):
        return self.path.boundingRect()
        
    def shape(self):
        return self.path
    
    def paint(self, p, *args):
        p.setRenderHints(p.renderHints() | p.Antialiasing)
        p.drawPixmap(0, 0, self.path.boundingRect().width(), self.path.boundingRect().height(), self.pxm)

class iViewGraphicBound(pg.GraphicsObject, ParamObj):
    def __init__(self, width=None, height=None):
        pg.GraphicsObject.__init__(self)
        
        self.width = width 
        self.height = height
        self.mkPath()
    
    def setParams(self, width, height):
        self.width = width
        self.height = height
        self.mkPath()
    
    def mkPath(self):
        self.prepareGeometryChange()
        width = self.width
        height = self.height
        self.path = QtGui.QPainterPath()
        self.path.addRect(0, 0, width, height)
        
    def boundingRect(self):
        return self.path.boundingRect()
        
    def paint(self, p, *args):
        return 

class iViewObject(pg.GraphicsObject, ParamObj):
    sigStateChanged = QtCore.Signal()
    mainWindow = None
    index = 0
    instrComp = None

    def __init__(self, gitem, **params):
        ParamObj.__init__(self)
        pg.GraphicsObject.__init__(self) #, [0,0], [1,1])

        self.gitem = gitem
        gitem.setParentItem(self)
        
        self.roi = pg.ROI([0,0], [1,1])
        self.roi.pen = pg.mkPen((0,0,255,0), width=0, cosmetic=True)
        handle = self.roi.addRotateHandle([1, 1], [0.5, 0.5])
        handle.pen = pg.mkPen('r')
        handle.currentPen = handle.pen
        handle.update()

        self.roi.rotateSnap = True
        self.roi.translateSnap = True
        self.roi.setParentItem(self)
        
        defaults = {
            'pos': Point(0,0),
            'angle': 0,
        }
        defaults.update(params)
        self.roi.sigRegionChanged.connect(self.roiChanged)
        self.roi.sigClicked.connect(self.clicked)
        self.roi.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        self.setParams(**defaults)
    
    def clicked(self):
        if(self.instrComp is not None):
            self.instrComp.onLeftClick(QCursor.pos())

    def updateTransform(self):
        self.resetTransform()
        self.setPos(0, 0)
        self.translate(Point(self['pos']))
        self.rotate(self['angle'])
        
    def setParam(self, param, val):
        ParamObj.setParam(self, param, val)

    def paramStateChanged(self):
        """Some parameters of the optic have changed."""
        # Move graphics item
        self.gitem.setPos(Point(self['pos']))
        self.gitem.resetTransform()
        self.gitem.rotate(self['angle'])
        
        # Move ROI to match
        try:
            self.roi.sigRegionChanged.disconnect(self.roiChanged)
            br = self.gitem.boundingRect()
            o = self.gitem.mapToParent(br.topLeft())
            self.roi.setAngle(self['angle'])
            self.roi.setPos(o)
            self.roi.setSize([br.width(), br.height()])
        finally:
            self.roi.sigRegionChanged.connect(self.roiChanged)
        self.sigStateChanged.emit()

    def roiChanged(self, *args):
        pos = self.roi.pos()
        # rotate gitem temporarily so we can decide where it will need to move
        self.gitem.resetTransform()
        self.gitem.rotate(self.roi.angle())
        br = self.gitem.boundingRect()
        o1 = self.gitem.mapToParent(br.topLeft())
        self.setParams(angle=self.roi.angle(), pos=pos + (self.gitem.pos() - o1))
        
    def boundingRect(self):
        return QtCore.QRectF()
        
    def paint(self, p, *args):
        pass

class iViewComponent(iViewObject):
    def __init__(self, mainWindow, index, instrComp, **params):
        defaults = {
            'width': 1,
            'height': 1,
            'angle' : 180
        }
        self.mainWindow = mainWindow
        self.indexComp = index
        self.instrComp = instrComp
        defaults.update(params)
        src = self.mainWindow.instrumentManager.componentsAvailable[index].layoutGraphicSrc
        self.gitem = iViewGraphic(src, brush=(100,100,100,255), **defaults)
        iViewObject.__init__(self, self.gitem, **defaults)