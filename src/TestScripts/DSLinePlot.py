from PyQt5.QtChart import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys, math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np

class DSLinePlotWidget(QChartView):
    xAxisChanged = pyqtSignal(object, float, float)

##### EXTERNAL FUNCTIONS #####
    def Add_Line(self, xdata, ydata):
        curve = DSLineSeries()
        curve.pressed.connect(self.curveClicked)
        curve.setUseOpenGL(True)
        curve.append(self.series_to_polyline(xdata, ydata))
        self.chart.addSeries(curve)
        curve.attachAxis(self.xAxis)
        curve.attachAxis(self.yAxis)

    def Link_X_Axis_To_Group(self, axisGroup):
        axisGroup.xAxisChanged.connect(self.linkedXAxisChanged)
        axisGroup.registerToGroup(self)

##### INTERNAL USE ONLY #####
    def __init__(self, name, xAxis=None, yAxis=None):
        super().__init__()
        self.name = name
        self.chart = DSChart()
        self.chart.legend().hide()
        self.xAxis = QValueAxis()
        self.yAxis = QValueAxis()


        self.chart.addAxis(self.xAxis, Qt.AlignBottom)
        self.chart.addAxis(self.yAxis, Qt.AlignLeft)

        self.setFrameStyle(QFrame.NoFrame)

        self.setChart(self.chart)
        self.setRenderHint(QPainter.Antialiasing)

        self.mousePressLoc = None

        #Properties ----
        self.xPan = True
        self.yPan = False
        self.xZoom = True
        self.yZoom = False
        self.zoomSpeed = 3

        self.xBoundMin = -5
        self.xBoundMax = 5

        self.yBoundMin = -5
        self.yBoundMax = 5

##### MOUSE EVENTS #####
    def mousePressEvent(self, mouseEvent):
        if(mouseEvent.buttons() & Qt.LeftButton):
            self.mousePressLoc = mouseEvent.screenPos()

    def curveClicked(self, point):
        cursor = QCursor()
        self.mousePressLoc = cursor.pos()     

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

##### HELPER FUNCTIONS #####
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

    def series_to_polyline(self, xdata, ydata):
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
    
##### PLOT AXIS MANIPULATIONS #####
    def linkedXAxisChanged(self, source, xMin, xMax):
        if source is not self:
            self.xAxis.setRange(xMin, xMax)

    def zoomPlot(self, dX, dY, point): # dX and dY in percentage
        print('zoom')
        if(self.xZoom is True):
            widthL = (point.x() - self.xAxis.min()) * (dX * self.zoomSpeed)
            widthR = (self.xAxis.max() - point.x()) * (dX * self.zoomSpeed)
            self.xAxis.setRange(self.xAxis.min() + widthL, self.xAxis.max() - widthR)
            self.xAxisChanged.emit(self, self.xAxis.min(), self.xAxis.max())

        if(self.yZoom is True):
            heightT = (point.y() - self.yAxis.min()) * (dY * self.zoomSpeed)
            heightB = (self.yAxis.max() - point.y()) * (dY * self.zoomSpeed)
            self.yAxis.setRange(self.yAxis.min() + heightT, self.yAxis.max() - heightB)

    def panPlot(self, dX, dY):
        if(self.xPan is True):
            self.xAxis.setRange(self.xAxis.min() + dX, self.xAxis.max() + dX)
            self.xAxisChanged.emit(self, self.xAxis.min(), self.xAxis.max())

        if(self.yPan is True):
            self.yAxis.setMin(self.yAxis.min() - dY)
            self.yAxis.setMax(self.yAxis.max() - dY)

class DSLinePlotAxisGroup(QObject):
    xAxisChanged = pyqtSignal(object, float, float)

    def __init__(self):
        super().__init__()
        

    def signalXAxisChanged(self, source, xMin, xMax):
        self.xAxisChanged.emit(source, xMin, xMax)

    def registerToGroup(self, plot):
        plot.xAxisChanged.connect(self.signalXAxisChanged)

class DSChart(QChart):
    def __init__(self):
        super().__init__()
        self.setMargins(QMargins(0, 0, 0, 0))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setBackgroundRoundness(0)
        self.setPlotAreaBackgroundVisible(False)

    def mousePressEvent(self, mouseEvent):
        pass

class DSLineSeries(QLineSeries):
    def __init__(self):
        super().__init__()
        self.clicked.connect(self.onClicked)

    def onClicked(self):
        pass

class TestWindow(QMainWindow):
    def __init__(self, parent=None):
        super(TestWindow, self).__init__(parent=parent)
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        self.mainLayout.setSpacing(0)

        self.xAxisGroup = DSLinePlotAxisGroup()

        self.addPlot(500)
        self.addPlot(500)
        self.addPlot(500)
        self.addPlot(500)
        self.addPlot(500)
        self.addPlot(500)


        self.setCentralWidget(self.mainWidget)


    def addPlot(self, n):
        plot = DSLinePlotWidget("Plot")
        plot.Link_X_Axis_To_Group(self.xAxisGroup)
        self.mainLayout.addWidget(plot)
        plot.Add_Line(np.linspace(0., 100., n), np.random.random_sample(n))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = TestWindow()
    window.show()
    window.resize(500, 400)
    sys.exit(app.exec_())