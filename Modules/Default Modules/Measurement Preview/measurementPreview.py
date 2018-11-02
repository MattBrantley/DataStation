from PyQt5.Qt import *
from PyQt5.QtGui import *
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs
from src.Managers.HardwareManager.PacketMeasurements import AnalogWaveformMeasurement
from PyQt5.QtChart import *
import numpy as np
import os

class measurementPreview(DSModule):
    Module_Name = 'Measurement Preview'
    Module_Flags = [mfs.CAN_DELETE]

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM

        self.initWindow()
        #self.initTitleBar()

        self.iM.Socket_Measurement_Packet_Recieved.connect(self.newMeasurement)
        #self.iM.Socket_Added.connect(self.populateSocketSelection)

    def initTitleBar(self):
        self.titleBarWidget = QWidget()
        self.titleBarLayout = QHBoxLayout()
        self.titleBarWidget.setLayout(self.titleBarLayout)

        self.titleBarWidget.setAutoFillBackground(True)

        self.configPixmap = QPixmap(os.path.join(self.ds.srcDir, 'icons5/zoom-in.png'))
        self.configIcon = QIcon(self.configPixmap)
        self.configButton = QPushButton()
        self.configButton.setIcon(self.configIcon)
        self.configButton.setFixedSize(20,20)

        self.titleBarLayout.addStretch()
        self.titleBarLayout.addWidget(self.configButton)

        self.setTitleBarWidget(self.titleBarWidget)

    def initWindow(self):
        self.container = QWidget()
        self.layerLayout = QStackedLayout()
        self.container.setLayout(self.layerLayout)
        self.setWidget(self.container)

        #### Overlay ####
        self.overlayWidget = QWidget()
        self.overlayLayout = QVBoxLayout()
        self.overlayLayout.setContentsMargins(0, 0, 0, 0)
        self.overlayWidget.setLayout(self.overlayLayout)

        #self.configPixmap = QPixmap(os.path.join(self.ds.srcDir, 'icons5/zoom-in.png'))
        #self.configIcon = QIcon(self.configPixmap)
        #self.configButton = QPushButton()
        #self.configButton.setIcon(self.configIcon)
        #self.configButton.setFixedSize(20,20)
        #self.overlayLayout.addWidget(self.configButton)
        #self.overlayLayout.addStretch()

        #self.layerLayout.addWidget(self.overlayWidget)

        #### Measurement ####
        self.measurementViewer = measurementView()
        self.layerLayout.addWidget(self.measurementViewer)

    def newMeasurement(self, instrument, component, socket, packet):
        print(instrument)
        print('new measurement')

    def populateSocketSelection(self):
        self.socketSelectionBox.clear()

        for instrument in self.iM.Get_Instruments():
            for socket in instrument.Get_Sockets():
                self.socketSelectionBox.addItem(socket.Get_Name())

class measurementView(QChartView):
    def __init__(self):
        super().__init__()
        self.initChart()
        self.initView()

    def initChart(self):
        self.chart = QChart()
        self.chart.setMargins(QMargins(0, 0, 0, 0))
        self.chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart.setBackgroundRoundness(0)
        self.chart.setPlotAreaBackgroundVisible(False)
        self.chart.setMargins(QMargins(24, 0, 0, 0))
        self.chart.legend().hide()

    def initView(self):
        self.setFrameStyle(QFrame.NoFrame)

    def addData(self, xdata, ydata, color=None):
        curve = QLineSeries()
        pen = curve.pen()
        if color is not None:
            pen.setColor(color)
        pen.setWidthF(.1)
        curve.setPen(pen)
        curve.setUseOpenGL(True)
        curve.append(self.series_to_polyline(xdata, ydata))
        self.chart.addSeries(curve)
        self.chart.createDefaultAxes()

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