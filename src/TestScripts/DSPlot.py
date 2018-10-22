from PyQt5.QtChart import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys, math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np

class DSPlotCanvas(QGraphicsView):
    
############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Add_Line(self, xdata, ydata):
        curve = DSLineSeries()
        #curve.pressed.connect(self.curveClicked)
        curve.setUseOpenGL(True)
        curve.append(self.series_to_polyline(xdata, ydata))
        self.chart.addSeries(curve)
        curve.attachAxis(self.xAxis)
        curve.attachAxis(self.yAxis)

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self):
        super().__init__()
        self.chart = DSChart()
        self.chart.legend().hide()

        self.setFrameStyle(QFrame.NoFrame)

        self.xAxis = QValueAxis()
        self.yAxis = QValueAxis()

    ##### MOUSE EVENTS #####

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
        self.mainWidget = DSPlotCanvas()
        self.setCentralWidget(self.mainWidget)

        self.mainWidget.Add_Line(np.linspace(0., 100., 50000), np.random.random_sample(50000))
        #self.mainWidget.Add_Plot(np.linspace(0., 100., 5000), np.random.random_sample(5000))
        #self.mainWidget.Add_Plot(np.linspace(0., 100., 5000), np.random.random_sample(5000))
        #self.mainWidget.Add_Plot(np.linspace(0., 100., 5000), np.random.random_sample(5000))
        #self.mainWidget.Add_Plot(np.linspace(0., 100., 5000), np.random.random_sample(5000))
        #self.mainWidget.Add_Plot(np.linspace(0., 100., 5000), np.random.random_sample(5000))
        #self.mainWidget.Add_Plot(np.linspace(0., 100., 5000), np.random.random_sample(5000))

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = TestWindow()
    window.show()
    window.resize(500, 400)
    sys.exit(app.exec_())