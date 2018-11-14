from PyQt5.Qt import *
from PyQt5.QtGui import *
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs
from src.Managers.HardwareManager.PacketMeasurements import AnalogWaveformMeasurement
from src.Managers.ModuleManager.ModuleResource import *
from PyQt5.QtChart import *
from functools import partial
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

        self.targetSocket = None

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
        self.layerLayout.setStackingMode(QStackedLayout.StackAll)
        self.container.setLayout(self.layerLayout)
        self.setWidget(self.container)

        #### Overlay ####
        self.overlayWidget = overlayWidget(self)
        self.layerLayout.addWidget(self.overlayWidget)

        #### Measurement ####
        self.measurementViewer = measurementView()
        self.layerLayout.addWidget(self.measurementViewer)

    def setTargetSocket(self, socket):
        self.targetSocket = socket
        self.setWindowTitle(self.Module_Name + ' [' + self.targetSocket.Get_Name() + ']')

    def loadPacketResource(self, measurementPacket):
        self.measurementViewer.clearData()
        self.measurementViewer.addData(measurementPacket)

    def newMeasurement(self, instrument, component, socket, packet):
        if socket is self.targetSocket:
            self.measurementViewer.clearData()
            self.measurementViewer.addData(packet)

    def populateSocketSelection(self):
        self.socketSelectionBox.clear()

        for instrument in self.iM.Get_Instruments():
            for socket in instrument.Get_Sockets():
                self.socketSelectionBox.addItem(socket.Get_Name())

class overlayWidget(QWidget):
    def __init__(self, module):
        super().__init__()
        self.module = module
        self.ds = module.ds
        self.iM = self.ds.iM
        self.mM = self.ds.mM
        self.initWidget()

    def initWidget(self):
        self.overlayLayout = QVBoxLayout()
        self.overlayLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.overlayLayout)

        self.configPixmap = QPixmap(os.path.join(self.ds.srcDir, 'icons5/zoom-in.png'))
        self.configIcon = QIcon(self.configPixmap)
        self.configButton = QPushButton()
        self.configButton.setIcon(self.configIcon)
        self.configButton.setFixedSize(20,20)
        self.configButton.pressed.connect(self.configPressed)
        self.overlayLayout.addWidget(self.configButton)
        self.overlayLayout.addStretch()

    def mousePressEvent(self, mouseEvent):
        self.module.measurementViewer.mousePressEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        self.module.measurementViewer.mouseReleaseEvent(mouseEvent)

    def mouseMoveEvent(self, mouseMoveEvent):
        self.module.measurementViewer.mouseMoveEvent(mouseMoveEvent)

    def configureMenu(self):
        self.menuItems = list() # Keeps everytihng in memory - otherwise the menu doesn't work.
        self.configMenu = QMenu()
        self.socketSelection = QMenu('Select Socket')
        for instrument in self.iM.Get_Instruments():
            instrumentMenu = QMenu(instrument.Get_Name())
            self.menuItems.append(instrumentMenu)
            self.socketSelection.addMenu(instrumentMenu)
            for socket in instrument.Get_Sockets():
                socketMenu = QAction(socket.Get_Name())
                socketMenu.triggered.connect(partial(self.module.setTargetSocket, socket))
                self.menuItems.append(socketMenu)
                instrumentMenu.addAction(socketMenu)

        self.resourceSelection = QMenu('Resource Packets')
        for module in self.mM.Get_Module_Instances():
            moduleMenu = QMenu(module.Get_Module().Module_Name)
            self.menuItems.append(moduleMenu)
            self.resourceSelection.addMenu(moduleMenu)
            for resource in module.Get_Module().Get_Resources(type=MeasurementPacketResource):
                resourceMenu = QAction(resource.Get_Name())
                resourceMenu.triggered.connect(partial(self.module.loadPacketResource, resource.Get_Measurement_Packet()))
                self.menuItems.append(resourceMenu)
                moduleMenu.addAction(resourceMenu)

        self.configMenu.addMenu(self.resourceSelection)
        self.configMenu.addMenu(self.socketSelection)

    def configPressed(self):
        self.configureMenu()
        action = self.configMenu.exec_(QCursor().pos())
        if(action is None):
            pass

class measurementView(QChartView):
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
        self.setRubberBand(QChartView.HorizontalRubberBand)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFrameStyle(QFrame.NoFrame)

    def clearData(self):
        self.chart.removeAllSeries()

    def addData(self, packet, color=None):
        for measurement in packet.Get_Measurements():
            self.createLine(measurement.xData(zeroOrigin=True), measurement.yData(), color=color)

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
        #curve.append(self.series_to_polyline(xdata, ydata))
        curve.replace(self.series_to_polyline(xdata, ydata))
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

class measurementChart(QChart):
    def __init__(self):
        super().__init__()
        self.legend().hide()
        self.setMargins(QMargins(0, 0, 0, 0))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setBackgroundRoundness(0)
        self.setPlotAreaBackgroundVisible(False)
        self.setMargins(QMargins(24, 0, 0, 0))