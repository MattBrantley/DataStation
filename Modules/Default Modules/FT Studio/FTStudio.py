from PyQt5.Qt import *
from PyQt5.QtGui import *
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs
from src.Managers.HardwareManager.PacketMeasurements import AnalogWaveformMeasurement
from src.Managers.ModuleManager.ModuleResource import *
from PyQt5.QtChart import *
from functools import partial
import scipy.constants as spc
import numpy as np
import os

class FTStudio(DSModule):
    Module_Name = 'FT Studio'
    Module_Flags = [mfs.CAN_DELETE]

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.mM = ds.mM

        self.initWindow()

        self.selectedPacket = None

        self.mM.Resource_Added.connect(self.populateTreeWidget)
        self.mM.Resource_Removed.connect(self.populateTreeWidget)

    def initWindow(self):
        self.mainContainer = QSplitter()
        self.configContainer = QTabWidget()
        self.initConfigWidgets()

        self.FTContainer = QSplitter()
        self.initFTContainer()

        self.mainContainer.addWidget(self.configContainer)
        self.mainContainer.addWidget(self.FTContainer)
        self.mainContainer.setStretchFactor(1, 2)

        self.setWidget(self.mainContainer)

        self.populateTreeWidget()

    def initConfigWidgets(self):
        self.TreeWidget = QTreeWidget()
        self.TreeWidget.setHeaderLabels(['Resources'])
        self.TreeWidget.currentItemChanged.connect(self.treeSelectionChanged)

        self.configWidget = QWidget()
        self.configContainer.addTab(self.TreeWidget, 'Resources')
        self.configContainer.addTab(self.configWidget, 'Config')

    def populateTreeWidget(self):
        self.TreeWidget.clear()

        for module in self.mM.Get_Module_Instances():
            resources = module.Get_Module().Get_Resources(type=MeasurementPacketResource)
            if resources:
                moduleItem = QTreeWidgetItem([module.Get_Module().Get_Name()])
                self.TreeWidget.addTopLevelItem(moduleItem)
                for resource in resources:
                    resourceItem = QTreeWidgetItem(['Measurement'])
                    resourceItem.packetResource = resource
                    moduleItem.addChild(resourceItem)

    def initFTContainer(self):
        self.FTContainer.setOrientation(Qt.Vertical)

        self.spectrumWindow = spectrumView()
        self.transientWindow = transientView()

        self.FTContainer.addWidget(self.spectrumWindow)
        self.FTContainer.addWidget(self.transientWindow)

    def treeSelectionChanged(self, item, oldItem):
        if hasattr(item, 'packetResource'):
            self.selectedPacket = item.packetResource
            self.processPacket()

    def processPacket(self):
        if self.selectedPacket is not None:
            self.transientWindow.clearData()
            self.transientWindow.addData(self.selectedPacket.Get_Measurement_Packet())

            self.spectrumWindow.clearData()
            self.spectrumWindow.addData(self.selectedPacket.Get_Measurement_Packet())


class spectrumView(QChartView):
    def __init__(self):
        super().__init__()
        self.initChart()
        self.initView()

    def initChart(self):
        self.chart = measurementChart()
        self.setChart(self.chart)

        self.xValueAxis = QValueAxis()
        self.xValueAxis.setTitleText('m/z')
        self.chart.addAxis(self.xValueAxis, Qt.AlignBottom)

        self.yValueAxis = QValueAxis()
        self.yValueAxis.setTitleText('Intensity (arb)')
        self.chart.addAxis(self.yValueAxis, Qt.AlignLeft)

    def initView(self):
        self.setRubberBand(QChartView.RectangleRubberBand)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFrameStyle(QFrame.NoFrame)

    def clearData(self):
        self.chart.removeAllSeries()

    def addData(self, packet, color=None):
        for measurement in packet.Get_Measurements():
            xData, yData = self.doFFT(measurement.yData(), measurement.stepSize())
            print(xData.shape)
            print(yData.shape)
            self.createLine(xData, yData, color=color)
            #self.createLine(measurement.xData(zeroOrigin=True), measurement.yData(), color=color)

    def createSelectionRect(self):
        rect = QRectF(1, 1, 1, 1)
        rectItem = QGraphicsRectItem(rect)
        self.chart.add

    def createLine(self, xdata, ydata, color=None):
        length = xdata.shape[0]
        ydata = ydata[0:length]
        curve = QLineSeries()
        pen = curve.pen()
        if color is not None:
            pen.setColor(color)
        pen.setWidthF(.1)
        curve.setPen(pen)
        curve.setUseOpenGL(True)
        curve.append(self.series_to_polyline(xdata, ydata))
        self.chart.addSeries(curve)

        #self.xValueAxis.setRange(xdata.min(), xdata.max())
        self.xValueAxis.setRange(20, 2000)
        self.yValueAxis.setRange(ydata.min(), ydata.max())

        curve.attachAxis(self.xValueAxis)
        curve.attachAxis(self.yValueAxis)
        #self.chart.createDefaultAxes()

    def series_to_polyline(self, xdata, ydata):
        size = len(xdata)
        polyline = QPolygonF(size)
        pointer = polyline.data()
        dtype, tinfo = np.float, np.finfo  # integers: = np.int, np.iinfo
        pointer.setsize(2*polyline.size()*tinfo(dtype).dtype.itemsize)
        memory = np.frombuffer(pointer, dtype)
        memory[:(size-1)*2+1:2] = xdata
        memory[1:(size-1)*2+2:2] = ydata
        return polyline        

    ##### MATHS #####
    def doFFT(self, data, dT):
        yData = np.fft.rfft(data)
        yData = np.abs(yData)**2
        xData = np.fft.rfftfreq(data.shape[0], d=dT)
        vfunc = np.vectorize(self.ftomz)
        xData = vfunc(xData[1:], 9.34)

        return xData, yData[1:]

        #return xData, yData

    def ftomz(self, f, b):
        return (spc.e*b) / (2*spc.pi*f) / 1.660539e-27

    def mousePressEvent(self, mouseEvent):
        if(mouseEvent.buttons() & Qt.RightButton):
            mouseEvent.accept()
        else:
            super().mousePressEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        if(mouseEvent.button() & Qt.RightButton):
            self.chart.zoomReset()
            mouseEvent.accept()
        else:
            super().mouseReleaseEvent(mouseEvent)

class transientView(QChartView):
    def __init__(self):
        super().__init__()
        self.initChart()
        self.initView()

    def initChart(self):
        self.chart = measurementChart()
        self.setChart(self.chart)

        self.xValueAxis = QValueAxis()
        self.xValueAxis.setTitleText('Time (s)')
        self.chart.addAxis(self.xValueAxis, Qt.AlignBottom)

        self.yValueAxis = QValueAxis()
        self.yValueAxis.setTitleText('Voltage (V)')
        self.chart.addAxis(self.yValueAxis, Qt.AlignLeft)

    def initView(self):
        #self.setRubberBand(QChartView.HorizontalRubberBand)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFrameStyle(QFrame.NoFrame)

    def clearData(self):
        self.chart.removeAllSeries()

    def addData(self, packet, color=None):
        for measurement in packet.Get_Measurements():
            self.createLine(measurement.xData(zeroOrigin=True), measurement.yData(), color=color)

    def createSelectionRect(self):
        rect = QRectF(1, 1, 1, 1)
        rectItem = QGraphicsRectItem(rect)
        self.chart.add

    def createLine(self, xdata, ydata, color=None):
        length = xdata.shape[0]
        ydata = ydata[0:length]
        curve = QLineSeries()
        pen = curve.pen()
        if color is not None:
            pen.setColor(color)
        pen.setWidthF(.1)
        curve.setPen(pen)
        curve.setUseOpenGL(True)
        curve.append(self.series_to_polyline(xdata, ydata))
        self.chart.addSeries(curve)

        self.xValueAxis.setRange(xdata.min(), xdata.max())
        self.yValueAxis.setRange(ydata.min(), ydata.max())

        curve.attachAxis(self.xValueAxis)
        curve.attachAxis(self.yValueAxis)
        #self.chart.createDefaultAxes()

    def series_to_polyline(self, xdata, ydata):
        size = len(xdata)
        polyline = QPolygonF(size)
        pointer = polyline.data()
        dtype, tinfo = np.float, np.finfo  # integers: = np.int, np.iinfo
        pointer.setsize(2*polyline.size()*tinfo(dtype).dtype.itemsize)
        memory = np.frombuffer(pointer, dtype)
        memory[:(size-1)*2+1:2] = xdata
        memory[1:(size-1)*2+2:2] = ydata
        return polyline        

class measurementChart(QChart):
    def __init__(self):
        super().__init__()
        self.legend().hide()
        self.setMargins(QMargins(0, 0, 0, 0))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setBackgroundRoundness(0)
        self.setPlotAreaBackgroundVisible(False)
        self.setMargins(QMargins(24, 0, 0, 0))