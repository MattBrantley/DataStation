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
            xData, yData = self.doFFT(measurement.xData(zeroOrigin=True), measurement.stepSize())
            self.createLine(xData, yData, color=color)
            #self.createLine(measurement.xData(zeroOrigin=True), measurement.yData(), color=color)

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