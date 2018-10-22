from PyQt5.Qt import *
import pyqtgraph as pg # This library gives a bunch of FutureWarnings that are unpleasant! Fix for this is in the main .py file header.
import os, json, numpy as np, random, math
from eventListWidget import eventListWidget
from loadedInstruments import loadedInstruments
from src.Managers.HardwareManager.PacketCommands import *
from scipy import interpolate
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs
from sequenceTreeView import sequenceTreeView
from SequenceCanvas import SequenceCanvas

class Sequencer(DSModule):
    Module_Name = 'Sequencer'
    Module_Flags = []
    ITEM_GUID = Qt.UserRole

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM

        self.targetInstrument = None

        self.plotPaddingPercent = 1
        self.plotList = list()
        self.resize(1000, 800)

        self.xMin = 0
        self.xMax = 1

        self.sequenceNavigator = sequenceTreeView(self)
        self.sequenceView = sequencerPlot(self)
        #self.sequenceView = DSGraphicsLayoutWidget(self.ds, self)
        self.loadedInstruments = loadedInstruments(self)

        self.initActionsAndToolbar()
        self.initLayout()

        self.updateToolbarState()

        self.iM.Sequence_Loaded.connect(self.sequenceLoaded)
        #self.iM.Sequence_Saved.connect(self.sequenceLoaded)

        self.iM.Instrument_Removed.connect(self.populateInstrumentList)
        self.iM.Instrument_New.connect(self.populateInstrumentList)
        self.iM.Instrument_Name_Changed.connect(self.populateInstrumentList)

        self.populateInstrumentList(None)

    def populateInstrumentList(self, instrument):
        self.instrumentSelectionBox.clear()
        self.loadedInstruments.clear()
        self.instrumentSelectionBox.addItem('')
        for idx, instrument in enumerate(self.iM.Get_Instruments()):
            self.instrumentSelectionBox.addItem(instrument.Get_Name())
            self.instrumentSelectionBox.setItemData(idx+1, instrument.Get_UUID(), role=Qt.UserRole)
            #if(instrument.Get_UUID() == self.targetUUID):
            #    self.instrumentSelectionBox.setCurrentIndex(idx+1)

            self.loadedInstruments.addInstrument(instrument)

    def initActionsAndToolbar(self):
        self.newAction = QAction('New', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('New')
        #self.newAction.triggered.connect(self.iM.newSequence)

        self.saveAction = QAction('Save', self)
        self.saveAction.setStatusTip('Save')
        #self.saveAction.triggered.connect(self.iM.saveSequence)

        self.saveAsAction = QAction('Save As', self)
        self.saveAsAction.setStatusTip('Save As')
        #self.saveAsAction.triggered.connect(self.iM.saveSequenceAs)

        self.toggleTree = QToolButton(self)
        self.toggleTree.setIcon(QIcon(os.path.join(self.ds.srcDir, 'icons3\css.png')))
        self.toggleTree.setCheckable(True)
        self.toggleTree.setStatusTip('Show/Hide The Sequence Browser')
        self.toggleTree.toggled.connect(self.treeToggled)
        self.toggleTree.toggle()
        
        self.toolbar = QToolBar()
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.saveAsAction)
        
        self.toolbar.addSeparator()

        self.toolbar.addWidget(self.toggleTree)

        self.toolbar.addSeparator()

        self.instrumentSelectionBox = QComboBox(self.toolbar)
        self.instrumentSelectionBox.setMinimumWidth(200)
        self.instrumentSelectionBox.currentIndexChanged.connect(self.instrumentSelectionChanged)
        
        self.toolbar.addWidget(self.instrumentSelectionBox)

    def instrumentSelectionChanged(self, index):
        uuid = self.instrumentSelectionBox.itemData(index, role=Qt.UserRole)
        instrument = self.iM.Get_Instruments(uuid=uuid)

        if not instrument:
            instrument = None
        else:
            instrument = instrument[0]

        self.targetInstrument = instrument

        if(instrument is not None):
            self.setWindowTitle('Sequencer (' + instrument.Get_Name() + ')')
            self.sequenceView.loadInstrument(instrument)
            #self.Write_Setting('Instrument_Path', instrument.Get_Path())
        else:
            self.sequenceView.clearAllPlots()
            self.setWindowTitle('Sequencer (None)')
            #self.Write_Setting('Instrument_Path', None)

    def initLayout(self):
        self.mainContainer = QMainWindow()
        self.mainContainer.addToolBar(self.toolbar)
        self.sequencerContainer = QSplitter()
        
        self.sequencerContainer.addWidget(self.sequenceNavigator)
        self.sequencerContainer.addWidget(self.sequenceView)

        self.sequencerContainer.setStretchFactor(1, 3)
        self.setWidget(self.mainContainer)
        self.mainContainer.setCentralWidget(self.sequencerContainer)

    def sequenceLoaded(self, instrument): #Update when Sequence has been fixed in iM
        seqInfo = instrument.Get_Sequence()
        self.setWindowTitle('Sequencer (' + seqInfo[1] + ')')

    def sequenceUnloaded(self, instrument):
        self.setWindowTitle('Sequencer (None)')

    def treeToggled(self, checked):
        if(checked):
            self.sequenceNavigator.show()
        else:
            self.sequenceNavigator.hide()

    def updateToolbarState(self):
        self.saveAction.setEnabled(True)
        self.saveAsAction.setEnabled(True)

class sequencerPlot(QWidget):
    def __init__(self, module):
        super().__init__()
        self.module = module
        self.ds = module.ds
        self.iM = module.iM
        self.plotList = list()
        self.canvas = SequenceCanvas()
        self.canvas.rightClicked.connect(self.toggleEditWidget)
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.canvas)

        self.iM.Component_Added.connect(self.addPlot)
        self.iM.Component_Removed.connect(self.removePlot)
        self.iM.Component_Standard_Field_Changed.connect(self.componentStandardFieldChanged)

    def loadInstrument(self, instrument):
        for component in instrument.Get_Components():
            self.addPlot(instrument, component)
        self.canvas.restoreZoom()

    def addPlot(self, instrument, component):
        if instrument is self.module.targetInstrument:
            if(component.Get_Custom_Field('sequencerSettings') is None):
                component.Set_Custom_Field('sequencerSettings', {'show': True})

            settings = component.Get_Custom_Field('sequencerSettings')
            if(settings['show'] is True):
                plot = self.canvas.Add_Plot()
                plot.setTitle(component.Get_Standard_Field('name'))
                plot.component = component
                plot.sequencerEditWidget = eventListWidget(self.ds, self.module, component)
                self.plotList.append(plot)
                self.drawPlotForComponent(instrument, component)

    def drawPlotForComponent(self, instrument, component):
        if instrument is self.module.targetInstrument:
            for plot in self.plotList:
                if plot.component is component:
                    plot.Clear_Lines()
                    #plot.Add_Line(np.linspace(0., 100., 5000), np.random.random_sample(5000))

                    for socket in component.Get_Sockets():
                        packet = socket.Get_Programming_Packet()
                        if(packet is not None):
                            data = list()
                            for cmd in packet.Get_Commands(commandType=AnalogSparseCommand):
                                data.append(cmd.pairs)
                            if(data):
                                plotData = np.vstack(data)
                                #print(plotData)
                                plot.Add_Line(plotData[:,0], plotData[:,1])
                            else:
                                plot.Add_Line(np.zeros(1), np.zeros(1))
                        else:
                            plot.Add_Line(np.zeros(1), np.zeros(1))


    def componentStandardFieldChanged(self, instrument, component, field):
        if instrument is self.module.targetInstrument:
            if field == 'name':
                print('NAME')
                for plot in self.plotList:
                    if plot.component is component:
                        plot.setTitle(component.Get_Standard_Field('name'))

    def clearAllPlots(self):
        self.canvas.Clear_Plots()
        self.plotList = list()

    def removePlot(self, instrument, component):
        if instrument is self.module.targetInstrument:
            self.clearAllPlots()
            self.loadInstrument(instrument)

    def toggleEditWidget(self, plot, eventPos):
        plot.sequencerEditWidget.move(eventPos + QPoint(2, 2))
        if(plot.sequencerEditWidget.isHidden()):
            plot.sequencerEditWidget.updateTitle()
            plot.sequencerEditWidget.show()
        else:
            plot.sequencerEditWidget.hide()

class DSGraphicsLayoutWidget(pg.GraphicsLayoutWidget):

    def __init__(self, ds, dockWidget):
        super().__init__()
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM

        self.xMin = 0
        self.xMax = 1
        self.xPadding = 2 # Percentage

        pg.setConfigOptions(antialias=True)
        self.dockWidget = dockWidget
        self.referencePlot = None
        self.plotList = list()
        self.setBackground(QColor(255, 255, 255))

        self.iM.Component_Added.connect(self.addNewPlot) #addPlot is reserved by pyqtgraph!
        self.iM.Component_Removed.connect(self.removePlot)

    def addNewPlot(self, instrument, component):
        if(component.Get_Custom_Field('sequencerSettings') is None):
            component.Set_Custom_Field('sequencerSettings', {'show': True})

        settings = component.Get_Custom_Field('sequencerSettings')
        if(settings['show'] is True):
            self.nextRow()
            plot = DSPlotItem(self.ds, self, component)
            self.plotList.append(plot)

            if(len(self.plotList) == 1):
                self.referencePlot = plot
            else:
                plot.plotItem.setXLink(self.referencePlot.plotItem)
            self.plotList.append(plot)

        self.setBottomAxis()

    def removePlot(self, instrument, component):
        for plot in self.plotList:
            if(plot.component is component):
                print('found the one to remove')
        print('could not find the one to remove')

        self.setBottomAxis()

    def setBottomAxis(self):
        for plot in self.plotList:
            plotTemp = plot
            plotTemp.setShowXAxis(False)
        plotTemp.setShowXAxis(True)

    def findPlotByMousePos(self, pos):
        plotsInRange = list()
        for plot in self.plotList:
            # Okay - so there is a glitch in pyqtgraph that adjustes the offset for other widgets in the scene by offsetting the bounding QRect
            # into the plot area (it seems to do this TWICE). Because the sequencer browser is causing this - we are adjusting the QRect collision
            # area to account for this. It's not pretty but it works.
            sequenceNavigatorWidth = self.dockWidget.sequenceNavigator.width()
            adjViewGeometry = plot.plotItem.getViewBox().screenGeometry().adjusted(-sequenceNavigatorWidth, 0, sequenceNavigatorWidth, 0)
            if(adjViewGeometry.contains(pos)):
                plotsInRange.append(plot)
        return plotsInRange

    def mouseDoubleClickEvent(self, event):
        if(event.buttons() == Qt.LeftButton):
            super().mouseDoubleClickEvent(event)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
        selectedPlots = self.findPlotByMousePos(event.globalPos())
        if selectedPlots:
            selectedPlots[0].toggleEditWidget(event.globalPos())

    def mousePressEvent(self, event):
        if(event.buttons() == Qt.RightButton):
            event.accept()
            selectedPlots = self.findPlotByMousePos(event.globalPos())
            if (len(selectedPlots) > 0):
                selectedPlots[0].toggleEditWidget(event.globalPos())
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if(event.button() == 2):
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if(event.buttons() & Qt.RightButton):
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def updateBounds(self):
        self.xMin = 9000
        self.xMax = -9000
        for plot in self.plotList:
            plot.getYBounds()
            xMin, xMax = plot.getXBounds()
            if(xMin < self.xMin):
                self.xMin = xMin
                for plot in self.plotList:
                    plot.plotItem.setLimits(xMin = self.xMin)

            if(xMax > self.xMax):
                self.xMax = xMax
                for plot in self.plotList:
                    plot.plotItem.setLimits(xMax = self.xMax)

class DSPlotItem():
    plotPaddingPercent = 1

    def __init__(self, ds, plotLayout, comp):
        super().__init__()

        self.ds = ds
        self.iM = ds.iM
        self.component = comp
        self.plotLayout = plotLayout
        self.plotItem = plotLayout.addPlot()
        self.pen = pg.mkPen(QColor(0,0,0), width=2)
        self.showXAxis = True
        self.plotDataList = list()

        a = sequencePlotDataItem(x=[-90, 90], y=[0, 0], pen = self.pen)
        self.plotItem.addItem(a)

        self.iM.Component_Programming_Modified.connect(self.plot)
        self.plot(None, self.component)

    def setShowXAxis(self, toggle):
        self.showXAxis = toggle
        if(toggle is True):
            self.plotItem.showAxis('bottom', True)
            self.plotItem.showLabel('bottom', True)
        else:
            self.plotItem.showAxis('bottom', False)
            self.plotItem.showLabel('bottom', False)

    def plot(self, instrument, component):
        if(component is self.component):
            self.plotItem.clear()
            for socket in component.Get_Sockets():
                packet = socket.Get_Programming_Packet()
                if(packet is not None):
                    data = list()
                    for cmd in packet.Get_Commands(commandType=AnalogSparseCommand):
                        data.append(cmd.pairs)
                    if(data):
                        plotData = np.vstack(data)
                        plotData = self.formatStepMode(plotData)
                        self.plotDataList.append(plotData)
                        plotExpanded = np.vstack([[-900, plotData[0,1]], plotData, [900, plotData[-1,1]]])
                        a = sequencePlotDataItem(x=plotExpanded[:,0], y=plotExpanded[:,1], pen=self.pen)
                        self.plotItem.addItem(a)
                        self.plotItem.getViewBox().autoRange()
                else:
                    pass

        self.plotItem.setLimits(xMin = 0, xMax = 1)
        self.plotLayout.updateBounds()
        self.plotItem.setMouseEnabled(x=True, y=False)
        self.plotItem.setLabels(bottom='Time (s)', left='voltage')
        self.setShowXAxis(self.showXAxis)
        self.plotItem.setLabel('left', self.component.Get_Standard_Field('name'))
        self.plotItem.setDownsampling(ds=True, auto=True, mode='peak') #mode='peak' produces strange results with large gaps in data
        self.plotItem.setClipToView(True)

    def formatStepMode(self, pairs):
        x = np.zeros(pairs.shape[0]*2)
        y = np.zeros(pairs.shape[0]*2)
        x[0::2] = pairs[:,0]
        x[1::2] = pairs[:,0]
        y[0::2] = pairs[:,1]
        y[1::2] = pairs[:,1]
        y = np.roll(y,1)

        return np.vstack([x,y]).transpose()

    def getXBounds(self):
        xMin = 0
        xMax = 0
        for plotData in self.plotDataList:
            xMinT = plotData[:,0].min()
            if(xMinT < xMin):
                xMin = xMinT
            xMaxT = plotData[:,0].max()
            if(xMaxT > xMax):
                xMax = xMaxT
        return xMin, xMax

    def getYBounds(self):
        yMin = 0
        yMax = 1
        for plotData in self.plotDataList:
            yMinT = plotData[:,1].min()
            if(yMinT < yMin):
                yMin = yMinT
            yMaxT = plotData[:,1].max()
            if(yMaxT > yMax):
                yMax = yMaxT
        self.plotItem.setLimits(yMin=yMin, yMax=yMax)
       
    def toggleEditWidget(self, eventPos):
        self.sequencerEditWidget.move(eventPos + QPoint(2, 2))
        if(self.sequencerEditWidget.isHidden()):
            self.sequencerEditWidget.updateTitle()
            self.sequencerEditWidget.show()
        else:
            self.sequencerEditWidget.hide()
 
class sequencePlotDataItem(pg.PlotDataItem):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

    def interpolatePairs(self, x, y, interval):
        xAxis = np.arange(x[0], x[-1]+interval, interval)
        f = interpolate.interp1d(x, y, kind='previous', fill_value='extrapolate')
        yAxis = f(xAxis)
        #result = np.vstack([xAxis, yAxis]).transpose()
        return xAxis, yAxis

    def find_nearest(self, array, value):
        idx = np.searchsorted(array, value, side='left')
        if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
            return array[idx-1]
        else:
            return array[idx]

    def getData(self):
        if self.xData is None:
            return (None, None)
            
        if self.xDisp is None:
            x = self.xData
            y = self.yData
                    
            ds = self.opts['downsample']
            if not isinstance(ds, int):
                ds = 1
                
            if self.opts['autoDownsample']:
                # this option presumes that x-values have uniform spacing
                range = self.viewRect()
                if range is not None:
                    dx = float(x[-1]-x[0]) / (len(x)-1)
                    x0 = (range.left()-x[0]) / dx
                    x1 = (range.right()-x[0]) / dx
                    width = self.getViewBox().width()
                    #width = range.width()
                    if width != 0.0:
                        #ds = int(max(1, int((x1-x0) / (width*self.opts['autoDownsampleFactor']))))
                        ds = int(max(1, int((x1-x0) / (width*0.0002))))
                        

                        #print('ds=' + str(ds))
                    ## downsampling is expensive; delay until after clipping.
            
            if self.opts['clipToView']:
                range = self.viewRect()
                x0 = np.searchsorted(x, range.left(), side='left')
                if(x0 > 0):
                    x0 -= 1
                x1 = np.searchsorted(x, range.right(), side='left')
                if(x1 < x.shape[0]):
                    x1 += 1
                x = x[x0:x1]
                y = y[x0:x1]
                    
            if ds > 1:
                if self.opts['downsampleMethod'] == 'subsample':
                    x = x[::ds]
                    y = y[::ds]
                elif self.opts['downsampleMethod'] == 'mean':
                    n = len(x) // ds
                    x = x[:n*ds:ds]
                    y = y[:n*ds].reshape(n,ds).mean(axis=1)
                elif self.opts['downsampleMethod'] == 'peak':
                    n = len(x) // ds
                    x1 = np.empty((n,2))
                    x1[:] = x[:n*ds:ds,np.newaxis]
                    x = x1.reshape(n*2)
                    y1 = np.empty((n,2))
                    y2 = y[:n*ds].reshape((n, ds))
                    y1[:,0] = y2.max(axis=1)
                    y1[:,1] = y2.min(axis=1)
                    y = y1.reshape(n*2)


            #x,y = self.interpolatePairs(x, y, 0.001)
                
            self.xDisp = x
            self.yDisp = y
        return self.xDisp, self.yDisp
