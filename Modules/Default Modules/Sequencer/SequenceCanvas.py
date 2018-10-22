from PyQt5.QtChart import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys, math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np
class SequencePlot(QObject):

    def __init__(self, canvas, title='Untitled'):
        super().__init__()
        self.title = title
        self.canvas = canvas
        self.createObjects()

        #self.reserve = QLineSeries()
        #self.reserve.append(-900000, -900000)
        #self.canvas.chart.addSeries(self.reserve)
        #self.yAxis.updateAxis()
        #self.updateXMinMax(np.array([0, 1]))
        #self.reserve.attachAxis(self.canvas.xAxis)
        #self.reserve.attachAxis(self.canvas.yAxis)

    def createObjects(self):
        self.yMin = 90000
        self.yMax = -90000

        self.minYAxisObject = self.canvas.scene().addText('min')
        self.maxYAxisObject = self.canvas.scene().addText('max')

        self.yAxisLine = QGraphicsLineItem(0, 0, 0, 0) 
        self.yAxisLinePen = QPen(Qt.gray)
        self.yAxisLine.setPen(self.yAxisLinePen)
        self.canvas.scene().addItem(self.yAxisLine)

        self.titleObject = self.canvas.scene().addText('<center>' + self.title + '</center>')

        self.testLine = QGraphicsLineItem(0, 0, 0, 0)
        self.canvas.scene().addItem(self.testLine)

        self.titleObject.setParent(self)
        self.dataSetList = list()
        self.yAxis = self.canvas.yAxis
        self.redrawLabels()

    def remove(self): # Not Working
        self.canvas.scene().removeItem(self.minYAxisObject)
        self.canvas.scene().removeItem(self.maxYAxisObject)
        self.canvas.scene().removeItem(self.titleObject)
        self.canvas.scene().removeItem(self.yAxisLine)
        self.Clear_Lines()
        self.yAxis.updateAxis()

    def setTitle(self, newTitle):
        self.title = newTitle
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

    def Clear_Lines(self):
        for dataSet in self.dataSetList:
            dataSet.clear()

    def Add_Line(self, xdata, ydata):
        self.updateXMinMax(xdata)
        xdata = np.insert(xdata, 0, -900)
        xdata = np.append(xdata, 900)

        ydata = np.insert(ydata, 0, ydata[0])
        ydata = np.append(ydata, ydata[-1])

        newLine = DSLineSeries(self.canvas, self, xdata, ydata)
        self.updateYMinMax(newLine)

        newLine.setParent(self.titleObject)
        self.dataSetList.append(newLine)
        self.canvas.chart.addSeries(newLine)
        self.yAxis.updateAxis()
        newLine.attachAxies()
        self.redrawLabels()
        self.canvas.update()

    def Is_Range(self, point):
        point2 = QPointF(point)
        point2.setX(point.x() * self.canvas.pixelToUnitsX())
        point2.setY(point.y() * self.canvas.pixelToUnitsY())
        if (self.getYMin() < point2.y()) and (self.getYMax() > point2.y()):
            self.canvas.mouseRightClick(self, point)

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
        xMin = 42 - self.minYAxisObject.boundingRect().width()
        yMin = 1/self.canvas.pixelToUnitsY() * self.getYMax() - self.minYAxisObject.boundingRect().height()
        self.minYAxisObject.setPos(xMin, yMin)
        yMin = yMin + self.minYAxisObject.boundingRect().height()

        self.maxYAxisObject.setHtml("{:.1f}".format(self.yMax))
        xMax = 42 - self.maxYAxisObject.boundingRect().width()
        yMax = 1/self.canvas.pixelToUnitsY() * self.getYMin()
        self.maxYAxisObject.setPos(xMax, yMax)

        self.yAxisLine.setLine(40, yMin-10, 40, yMax+10)

        self.titleObject.setHtml('<center>' + self.title + '</center>')
        self.titleObject.setRotation(0)
        self.titleObject.setTextWidth((yMin-yMax)-26)
        ytitle = (yMin + yMax)/2
        center = self.titleObject.boundingRect().center()
        goal = QPointF(self.titleObject.boundingRect().height()/2, ytitle)
        trans = goal - center
        height = self.titleObject.boundingRect().height()
        width = self.titleObject.boundingRect().width()
        self.titleObject.setPos(trans)
        self.titleObject.setTransformOriginPoint(self.titleObject.boundingRect().center())
        self.titleObject.setRotation(-90)

        self.testLine.setLine(8, ytitle, 8, ytitle)

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
        self.append(self.series_to_polyline(self.xdata, self.ydata))

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
        if ydata.max() != 0:
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
    rightClicked = pyqtSignal(object, object) # QPoint, PlotObject

##### EXTERNAL FUNCTIONS #####
    def Add_Plot(self):
        plot = SequencePlot(self)
        self.plotList.append(plot)

        self.redrawLabels()
        return plot

    def Clear_Plots(self):
        for plot in self.plotList:
            plot.remove()

        self.plotList = list()

    def Remove_Plot(self, plot): # Not Working
        for plot in self.plotList:
            plot.remove()

        self.plotList.remove(plot)

        for plot in self.plotList:
            plot.createObjects()
            plot.Redraw_Lines()

##### INTERNAL USE ONLY #####
    def __init__(self):
        super().__init__()
        self.chart = DSChart()
        self.chart.setMargins(QMargins(24, 0, 0, 0))
        self.chart.legend().hide()
        self.plotList = list()

        self.setFrameStyle(QFrame.NoFrame)

        self.xAxis = QValueAxis()
        self.xAxis.setTickCount(11)
        self.xAxis.setTitleText('Time (s)')
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

        if(mouseEvent.buttons() & Qt.RightButton):
            for plot in self.plotList:
                plot.Is_Range(mouseEvent.pos())

    def mouseRightClick(self, plot, point):
        self.rightClicked.emit(plot, point)

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
        if(mouseEvent.buttons() & Qt.LeftButton):
            self.restoreZoom()
        else:
            mouseEvent.ignore()

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

# class TestWindow(QMainWindow):
#     def __init__(self, parent=None):
#         super(TestWindow, self).__init__(parent=parent)
#         self.mainWidget = SequenceCanvas()
#         self.setCentralWidget(self.mainWidget)

#         a = self.mainWidget.Add_Plot()
#         a.Add_Line
#         a.setTitle('a')

#         b = self.mainWidget.Add_Plot()
#         b.Add_Line(np.linspace(0., 100., 5000), np.random.random_sample(5000))
#         b.setTitle('b')

#         c = self.mainWidget.Add_Plot()
#         c.Add_Line(np.linspace(0., 100., 5000), np.random.random_sample(5000))
#         c.Add_Line(np.linspace(0., 100., 5000), np.random.random_sample(5000))

#         self.mainWidget.Clear_Plots()
#         d = self.mainWidget.Add_Plot()
#         d.Add_Line(np.linspace(0., 100., 5000), np.random.random_sample(5000))
#         d.Add_Line(np.linspace(0., 100., 5000), np.random.random_sample(5000))
#         #self.mainWidget.Remove_Plot(c)

# if __name__ == '__main__':
#     app = QApplication(sys.argv)

#     window = TestWindow()
#     window.show()
#     window.resize(500, 400)
#     sys.exit(app.exec_())