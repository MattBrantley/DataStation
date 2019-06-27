from PyQt5.Qt import *
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDial
from AnalogGaugeWidgetPyQt.analoggaugewidget import AnalogGaugeWidget
import PyQt5.QtCore as QtCore
from decimal import Decimal
import os, time, numpy as np, pyqtgraph as pg, random, math
from src.Managers.ModuleManager.DSModule import DSModule
from functools import partial
from src.Constants import DSConstants as DSConstants
from src.Constants import moduleFlags as mfs

class System_Pressure(DSModule):
    Module_Name = 'System Pressure Monitor'
    Module_Flags = [mfs.CAN_DELETE]

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.targetInstrument = None

        self.writeMatrix = np.zeros((1))
        self.displayMatrix = None
        self.collectVector = None

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.setupUI()

        # self.iM.Instrument_Sequence_Running.connect(self.instrumentSequenceRunning)
        # self.iM.Socket_Measurement_Packet_Recieved.connect(self.measurementPacketRecieved)

    def setupUI(self):
        self.mainContainer = QMainWindow()

        self.pressureView = Pressure_View(self)
        self.setWidget(self.pressureView)

    # def instrumentSequenceRunning(self, instrument):
    #     self.writeMatrix = np.zeros((len(instrument.Get_Components())))

    # def measurementPacketRecieved(self, instrument, component, socket, packet):
    #     index = instrument.Get_Components().index(component)
    #     for measurement in packet.Get_Measurements():
    #         self.writeMatrix[index] = measurement.yData()

    #     if 0 in self.writeMatrix:
    #         pass
    #     else:
    #         self.addMeasurementVector()

    # def addMeasurementVector(self):
    #     if self.displayMatrix is None:
    #         self.displayMatrix = self.writeMatrix
    #     else:
    #         self.displayMatrix = np.vstack((self.displayMatrix, self.writeMatrix))


    #     if self.collectVector is None:
    #         self.collectVector = np.array([0])
    #     else:
    #         val = self.collectVector[-1]+1
    #         self.collectVector = np.hstack((self.collectVector, val))

    #     self.plotWidget.update()

class Pressure_View(QWidget):
    def __init__(self, module):
        super().__init__(None)
        self.module = module
        self.mainLayout = QVBoxLayout()

        self.topContainer = QWidget()
        self.topLayout = QHBoxLayout()
        self.topLayout.setContentsMargins(0,0,0,0)
        self.topContainer.setLayout(self.topLayout)

        self.bottomContainer = QWidget()
        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setContentsMargins(0,0,0,0)
        self.bottomContainer.setLayout(self.bottomLayout)

        self.mainLayout.addWidget(self.topContainer)
        self.mainLayout.addWidget(self.bottomContainer)

        self.setLayout(self.mainLayout)

        self.topPressure1 = Pressure_Widget_Main(self.module, -12, -6, -10, 'ICR Cell')
        self.topPressure2 = Pressure_Widget_Main(self.module, -12, -6, -9, 'Transfer Chamber')
        self.topPressure3 = Pressure_Widget_Main(self.module, -12, -6, -9, 'Source Chamber')
        self.topLayout.addWidget(self.topPressure1)
        self.topLayout.addWidget(self.topPressure2)
        self.topLayout.addWidget(self.topPressure3)

        self.botPressure1 = Pressure_Widget_Main(self.module, -3, 3, -1, 'ICR Cell Backing')
        self.botPressure2 = Pressure_Widget_Main(self.module, -3, 3, -1, 'Transfer Chamber Backing')
        self.botPressure3 = Pressure_Widget_Main(self.module, -3, 3, -1, 'Source Chamber Backing')
        self.botPressure4 = Pressure_Widget_Main(self.module, -3, 3, 1, 'Pulse Valve Gas')
        self.bottomLayout.addWidget(self.botPressure1)
        self.bottomLayout.addWidget(self.botPressure2)
        self.bottomLayout.addWidget(self.botPressure3)
        self.bottomLayout.addWidget(self.botPressure4)

class Pressure_Widget_Main(QWidget):
    def __init__(self, module, minVal, maxVal, setVal, title):
        super().__init__()
        self.module = module
        self.minVal = minVal
        self.maxVal = maxVal
        self.setVal = setVal
        self.title = 'Empty'
        self.initMain()

        self.targetComponent = None

        self.dial.set_current_value(0.023)

        self.module.iM.Socket_Measurement_Packet_Recieved.connect(self.measurementPacketRecieved)

    def measurementPacketRecieved(self, instrument, component, socket, packet):
        if component == self.targetComponent:
            if isinstance(packet.getMeasurements()[0].yData(), float):
                self.dial.set_current_value(packet.getMeasurements()[0].yData())
                self.plot.setText(str(packet.getMeasurements()[0].yData()))

    def initMain(self):
        self.layout = QVBoxLayout()

        self.topContainer = QWidget()
        self.topLayout = QHBoxLayout()
        self.topLayout.setAlignment(Qt.AlignTop)
        self.topContainer.setLayout(self.topLayout)
        self.topContainer.setContentsMargins(0,0,0,0)

        self.bottomContainer = QWidget()
        self.bottomLayout = QVBoxLayout()
        self.bottomContainer.setLayout(self.bottomLayout)
        self.bottomContainer.setContentsMargins(0,0,0,0)

        self.layout.addWidget(self.topContainer)
        self.layout.addWidget(self.bottomContainer)

        self.settingsButton = Settings_Button(self.module, self)
        self.dial = Pressure_Dial(self.minVal, self.maxVal, self.setVal)
        self.topLayout.addWidget(self.settingsButton)
        self.topLayout.addWidget(self.dial)

        self.label = QLabel()
        self.label.setText(self.title)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Calibri", 14, QFont.Bold))
        self.plot = QTextEdit()
        self.bottomLayout.addWidget(self.label)
        #self.bottomLayout.addWidget(self.plot)

        self.setLayout(self.layout)

class Pressure_Dial(AnalogGaugeWidget):
    def __init__(self, minVal, maxVal, setVal):
        super().__init__()
        self.set_MinValue(minVal)
        self.set_MaxValue(maxVal)
        self.set_scala_main_count(self.value_max-self.value_min)
        self.logMode = True
        self.units = "Torr"

        setScale = ((setVal-minVal)/(maxVal-minVal))

        self.set_scale_polygon_colors([[.00, Qt.green],
                                     [setScale+0.05, Qt.yellow],
                                     [setScale+0.1, Qt.red],
                                     [1, Qt.transparent]])

    def set_current_value(self, value):
        #print(self.calcAdjVal(value))
        self.update_value(self.calcAdjVal(value))

    def calcAdjVal(self, number):
        (sign, digits, exponent) = Decimal(number).as_tuple()
        mantissa = len(digits) + exponent - 1
        number = Decimal(number).scaleb(-mantissa).normalize()

        if mantissa >= 0:
            return mantissa+(number/10)
        else:
            return mantissa-(number/10)



class Settings_Button(QWidget):
    def __init__(self, module, widget):
        super().__init__()
        self.module = module
        self.widget = widget
        self.setFixedWidth(20)

        self.configPixmap = QPixmap(os.path.join(self.module.ds.srcDir, 'icons5/zoom-in.png'))
        self.configIcon = QIcon(self.configPixmap)
        self.configButton = QPushButton()
        self.configButton.setIcon(self.configIcon)
        self.configButton.setFixedSize(20,20)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.configButton)
        self.layout.addStretch(1)
        self.setLayout(self.layout)

        self.configButton.pressed.connect(self.configPressed)

    def configureMenu(self):
        self.menuItems = list() # Keeps everytihng in memory - otherwise the menu doesn't work.
        self.configMenu = QMenu()
        self.componentSelection = QMenu('Select Component')
        for instrument in self.module.iM.Get_Instruments():
            instrumentMenu = QMenu(instrument.Get_Name())
            self.menuItems.append(instrumentMenu)
            self.componentSelection.addMenu(instrumentMenu)
            for component in instrument.Get_Components():
                socketMenu = QAction(component.Get_Name())
                socketMenu.triggered.connect(partial(self.setTargetComponent, component))
                self.menuItems.append(socketMenu)
                instrumentMenu.addAction(socketMenu)
                if component == self.widget.targetComponent:
                    pass
                    #instrumentMenu.setChecked(True)


        self.configMenu.addMenu(self.componentSelection)

    def configPressed(self):
        self.configureMenu()
        action = self.configMenu.exec_(QCursor().pos())
        if(action is None):
            pass

    def setTargetComponent(self, component):
        self.widget.targetComponent = component
        self.widget.label.setText(component.Get_Name())

# class Pressure_Plot(pg.PlotWidget):
#     def __init__(self, module):
#         super().__init__(None)
#         self.module = module

#         self.pens = []
#         self.pens.append(pg.mkPen('b', width = 2))
#         self.pens.append(pg.mkPen('g', width = 2))
#         self.pens.append(pg.mkPen('r', width = 2))
#         self.pens.append(pg.mkPen('c', width = 2))
#         self.pens.append(pg.mkPen('m', width = 2))
#         self.pens.append(pg.mkPen('k', width = 2))

#         self.legendItems = []

#         self.getPlotItem().addLegend()

#         self.legender = self.getPlotItem().legend

#     def update(self):
#         self.getPlotItem().clear()
#         self.getPlotItem().setLogMode(y=10)

#         if self.module.collectVector is not None:
#             if self.module.displayMatrix.ndim == 1:
#                 for i in range(0, self.module.displayMatrix.shape[0]):
#                     plotter = self.plot(self.module.collectVector, np.array([self.module.displayMatrix[i]]), pen=self.pens[i])
#             else:
#                 for i in range(0, self.module.displayMatrix.shape[1]):
#                     plotter = self.plot(self.module.collectVector, self.module.displayMatrix[:,i], pen=self.pens[i])



# class Pressure_Config(QWidget):
#     def __init__(self, module):
#         super().__init__(None)
#         self.module = module