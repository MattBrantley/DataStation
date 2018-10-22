from PyQt5.QtChart import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys, math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np
#   "{:.1f}".format(val)
class SequencePlot(QObject):
    def __init__(self, canvas, title='Untitled'):
        super().__init__()
        self.title = title
        self.canvas = canvas

        self.yMin = 90000
        self.yMax = -90000

        self.minYAxisObject = self.canvas.scene().addText('min')
        self.maxYAxisObject = self.canvas.scene().addText('max')

        self.yAxisLine = QGraphicsLineItem(0, 0, 0, 0) 
        self.yAxisLinePen = QPen(Qt.gray)
        self.yAxisLine.setPen(self.yAxisLinePen)
        self.canvas.scene().addItem(self.yAxisLine)

        self.titleObject = self.canvas.scene().addText(self.title)

        self.titleObject.setParent(self)
        self.dataSetList = list()
        self.yAxis = canvas.yAxis
        self.redrawLabels()

    def remove(self):
        self.canvas.scene().removeItem(self.minYAxisObject)
        self.canvas.scene().removeItem(self.maxYAxisObject)
        self.canvas.scene().removeItem(self.titleObject)
        self.canvas.scene().removeItem(self.yAxisLine)
        for dataSet in self.dataSetList:
            self.canvas.chart.removeSeries(dataSet)
            dataSet.deleteLater()
        self.yAxis.updateAxis()

    def setTitle(self, newTitle):
        self.title = newTitle
        #self.titleObject.setTransformOriginPoint(self.titleObject.boundingRect().center())
        self.redrawLabels()

    def updateXMinMax(self, xdata):
        tMin = xdata.min()
        if tMin < self.canvas.xMin:
            self.canvas.xMin = tMin
        tMax = xdata.max()
        if tMax > self.canvas.xMax:
            self.canvas.xMax = tMax

    def updateYMinMax(self, line):
        if line.seriesMin < self.yMin:
            self.yMin = line.seriesMin
        if line.seriesMax > self.yMax:
            self.yMax = line.seriesMax

    def Redraw_Lines(self):
        for dataSet in self.dataSetList:
            dataSet.redrawSet()

    def Add_Line(self, xdata, ydata):
        self.updateXMinMax(xdata)

        newLine = DSLineSeries(self.canvas, self, xdata, ydata)
        self.updateYMinMax(newLine)

        newLine.setParent(self.titleObject)
        self.dataSetList.append(newLine)
        self.canvas.chart.addSeries(newLine)
        self.yAxis.updateAxis()
        newLine.attachAxies()
        self.redrawLabels()

    def getYMin(self):
        try:
            index = self.canvas.getPlotIndex(self)
        except:
            index = len(self.canvas.plotList)
        return index * (self.canvas.padBetweenPlots/100) + index

    def getYMax(self):
        return self.getYMin() + 1

    def redrawLabels(self):
        self.minYAxisObject.setHtml("{:.1f}".format(self.yMin))
        xMin = 34 - self.minYAxisObject.boundingRect().width()
        yMin = 1/self.canvas.pixelToUnitsY() * self.getYMax() - self.minYAxisObject.boundingRect().height()
        self.minYAxisObject.setPos(xMin, yMin)

        self.maxYAxisObject.setHtml("{:.1f}".format(self.yMax))
        xMax = 34 - self.maxYAxisObject.boundingRect().width()
        yMax = 1/self.canvas.pixelToUnitsY() * self.getYMin()
        self.maxYAxisObject.setPos(xMax, yMax)

        self.yAxisLine.setLine(32, yMin+ self.minYAxisObject.boundingRect().height(), 32, yMax +2)

        self.titleObject.setHtml(self.title)
        ytitle = (yMin + yMax)/2
        self.titleObject.setTransformOriginPoint(self.titleObject.boundingRect().center())
        self.titleObject.boundingRect().moveCenter(QPointF(0, ytitle))
        self.titleObject.setPos(-self.titleObject.boundingRect().center().x() + 8, ytitle)
        self.titleObject.setRotation(-90)

class DSLineSeries(QLineSeries):
    def __init__(self, canvas, plot, xdata, ydata):
        super().__init__()
        self.canvas = canvas
        self.plot = plot
        self.clicked.connect(self.onClicked)
        self.pressed.connect(self.onPressed)
        self.doubleClicked.connect(self.onDoubleClicked)
        self.setUseOpenGL(True)
        self.append(self.series_to_polyline(xdata, ydata))
        
        self.xdata = xdata
        self.ydata = ydata

        self.seriesMin = 0
        self.seriesMax = 1

    def redrawSet(self):
        self.clear()
        self.appen

    def attachAxies(self):
        self.attachAxis(self.canvas.xAxis)
        self.attachAxis(self.canvas.yAxis)

    def onClicked(self):
        pass

    def onDoubleClicked(self, event):
        self.canvas.mouseDoubleClickEvent(event)

    def onPressed(self, point):
        cursor = QCursor()
        self.canvas.mousePressLoc = cursor.pos()   

    def series_to_polyline(self, xdata, ydata):
        self.seriesMin = ydata.min()
        self.seriesMax = ydata.max()
        ydata *= 1/ydata.max()
        ydata += self.plot.getYMin()
        #ydata += self.getYMin()

        ### CODE ADOPTED FROM MIT SOURCE ###
        size = len(xdata)
        polyline = QPolygonF(size)
        pointer = polyline.data()
        dtype, tinfo = np.float, np.finfo
        pointer.setsize(2*polyline.size()*tinfo(dtype).dtype.itemsize)
        memory = np.frombuffer(pointer, dtype)
        memory[:(size-1)*2+1:2] = xdata
        memory[1:(size-1)*2+2:2] = ydata

        return polyline

class SequenceCanvas(QChartView):

##### EXTERNAL FUNCTIONS #####
    def Add_Plot(self):
        plot = SequencePlot(self)
        self.plotList.append(plot)

        self.redrawLabels()
        return plot

    def Remove_Plot(self, plot):
        self.plotList.remove(plot)
        plot.remove()

        for plot in self.plotList:


##### INTERNAL USE ONLY #####
    def __init__(self):
        super().__init__()
        self.chart = DSChart()
        self.chart.setMargins(QMargins(16, 0, 0, 0))
        self.chart.legend().hide()
        self.plotList = list()

        self.setFrameStyle(QFrame.NoFrame)

        self.xAxis = QValueAxis()
        self.xAxis.setTickCount(11)
        self.chart.addAxis(self.xAxis, Qt.AlignBottom)

        self.yAxis = DSSequenceYAxis(self)
        self.chart.addAxis(self.yAxis, Qt.AlignLeft)

        self.setChart(self.chart)
        self.chart.plotAreaChanged.connect(self.redrawLabels)
        self.setRenderHint(QPainter.Antialiasing)

        self.mousePressLoc = None

        #Properties ----
        self.xPan = True
        self.yPan = False
        self.xZoom = True
        self.yZoom = False
        self.zoomSpeed = 3

        self.xMin = 0
        self.xMax = 1

        self.yMin = 0
        self.yMax = 1

        self.padBetweenPlots = 5 # in percent

##### MOUSE EVENTS #####
    def mousePressEvent(self, mouseEvent):
        if(mouseEvent.buttons() & Qt.LeftButton):
            self.mousePressLoc = mouseEvent.screenPos()

    def mouseMoveEvent(self, mouseEvent):
        if(mouseEvent.buttons() & Qt.LeftButton):
            if(self.mousePressLoc is None):
                self.mousePressLoc = mouseEvent.screenPos()
            dPoint = self.mousePressLoc - mouseEvent.screenPos()
            self.mousePressLoc = mouseEvent.screenPos()
            shiftX = dPoint.x()*self.pixelToUnitsX()
            shiftY = dPoint.y()*self.pixelToUnitsY()
            self.panPlot(shiftX, shiftY)

    def wheelEvent(self, wheelEvent):
        wheelAngleDelta = wheelEvent.angleDelta().y()/8

        if(wheelAngleDelta < 0):
            wheelAngleDelta = wheelAngleDelta * 1.5
        if(self.screenToPlotPoint(wheelEvent.pos()) is not False):
            self.zoomPlot(wheelAngleDelta/360, wheelAngleDelta/360, self.screenToPlotPoint(wheelEvent.pos()))
            
    def mouseDoubleClickEvent(self, mouseEvent):
        self.restoreZoom()

##### HELPER FUNCTIONS #####
    def getPlotIndex(self, plot):
        return self.plotList.index(plot)

    def pixelToUnitsX(self):
        xWidthPlot = self.xAxis.max()-self.xAxis.min()
        return xWidthPlot / self.chart.plotArea().width()

    def pixelToUnitsY(self):
        yWidthPlot = self.yAxis.max()-self.yAxis.min()
        return yWidthPlot / self.chart.plotArea().height()

    def screenToPlotPoint(self, pos):
        if(self.chart.plotArea().contains(pos)):
            xPoint = (pos.x() - self.chart.plotArea().left()) * self.pixelToUnitsX() + self.xAxis.min()
            yPoint = self.yAxis.max() - (pos.y() - self.chart.plotArea().top()) * self.pixelToUnitsY()

            return QPointF(xPoint, yPoint)
        else:
            return False
    
##### PLOT AXIS MANIPULATIONS #####
    def redrawLabels(self):
        for plot in self.plotList:
            plot.redrawLabels()

    def restoreZoom(self):
        self.xAxis.setRange(self.xMin, self.xMax)

    def zoomPlot(self, dX, dY, point): # dX and dY in percentage
        if(self.xZoom is True):
            xMin = self.xAxis.min() + (point.x() - self.xAxis.min()) * (dX * self.zoomSpeed)
            xMax = self.xAxis.max() - (self.xAxis.max() - point.x()) * (dX * self.zoomSpeed)

            if xMin < self.xMin:
                xMin = self.xMin
            if xMax > self.xMax:
                xMax = self.xMax

            self.xAxis.setRange(xMin, xMax)

        if(self.yZoom is True):
            yMin = self.yAxis.min() + (point.y() - self.yAxis.min()) * (dY * self.zoomSpeed)
            yMax = self.yAxis.max() - (self.yAxis.max() - point.y()) * (dY * self.zoomSpeed)

            if yMin < self.yMin:
                yMin = self.yMin
            if yMax > self.yMx:
                yMax = self.yMax

            self.yAxis.setRange(yMin, yMax)

    def panPlot(self, dX, dY):
        if(self.xPan is True):
            xMin = self.xAxis.min() + dX
            xMax = self.xAxis.max() + dX

            if xMin < self.xMin:
                xMin = self.xMin
                xMax = self.xAxis.max()
            if xMax > self.xMax:
                xMin = self.xAxis.min()
                xMax = self.xMax

            self.xAxis.setRange(xMin, xMax)

        if(self.yPan is True):
            yMin = self.yAxis.min() - dY
            yMax = self.yAxis.max() - dY
            
            if yMin < self.yMin:
                yMin = self.yMin
                yMax = self.yAxis.max()
            if yMax > self.yMx:
                yMin = self.yAxis.min()
                yMax = self.yMax
                
            self.yAxis.setRange(yMin, yMax)

class DSSequenceYAxis(QCategoryAxis):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.setMin(0)
        self.setMax(1)
        self.setStartValue(0)

    def updateAxis(self):
        for plot in self.canvas.plotList:
            self.setMax(plot.getYMax())

class DSChart(QChart):
    def __init__(self):
        super().__init__()
        self.setMargins(QMargins(0, 0, 0, 0))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setBackgroundRoundness(0)
        self.setPlotAreaBackgroundVisible(False)

    def mousePressEvent(self, mouseEvent):
        pass

    def mouseDoubleclickEvent(self, mouseEvent):
        pass

class TestWindow(QMainWindow):
    def __init__(self, parent=None):
        super(TestWindow, self).__init__(parent=parent)
        self.mainWidget = SequenceCanvas()
        self.setCentralWidget(self.mainWidget)

        a = self.mainWidget.Add_Plot()
        a.Add_Line(np.linspace(0., 100., 500000), np.random.random_sample(500000))
        a.setTitle('a')

        b = self.mainWidget.Add_Plot()
        b.Add_Line(np.linspace(0., 100., 5000), np.random.random_sample(5000))
        b.setTitle('b')

        c = self.mainWidget.Add_Plot()
        c.Add_Line(np.linspace(0., 100., 5000), np.random.random_sample(5000))
        c.Add_Line(np.linspace(0., 100., 5000), np.random.random_sample(5000))

        self.mainWidget.Remove_Plot(b)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = TestWindow()
    window.show()
    window.resize(500, 400)
    sys.exit(app.exec_())