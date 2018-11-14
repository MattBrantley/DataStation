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
    Module_Flags = [mfs.CAN_DELETE]
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
        self.loadedInstruments = loadedInstruments(self)

        self.initActionsAndToolbar()
        self.initLayout()

        self.updateToolbarState()

        self.prevInstrumentPath = self.Read_Setting('Instrument_Path')
        self.prevSequencePath = self.Read_Setting('Sequence_Path')

        self.iM.Sequence_Loaded.connect(self.sequenceLoaded) 
        #self.iM.Sequence_Saved.connect(self.sequenceLoaded)

        self.iM.Instrument_Removed.connect(self.populateInstrumentList)
        self.iM.Instrument_New.connect(self.populateInstrumentList)
        self.iM.Instrument_Name_Changed.connect(self.populateInstrumentList)

        self.iM.Component_Programming_Modified.connect(self.componentProgrammingModified)

        self.populateInstrumentList(None)

    def componentProgrammingModified(self, instrument, component):
        if instrument is self.targetInstrument:
            self.sequenceView.drawPlotForComponent(instrument, component)

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
            if self.prevInstrumentPath == instrument.Get_Path():
                self.instrumentSelectionBox.setCurrentIndex(idx+1)
                #instrument.Load_Sequence(self.prevSequencePath)
                #if isinstance(prevInstrumentPath, str):
                #    self.openInstrument(prevInstrumentPath)

    def initActionsAndToolbar(self):
        self.newAction = QAction('New', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('New')
        #self.newAction.triggered.connect(self.iM.newSequence)

        self.saveAction = QAction('Save', self)
        self.saveAction.setStatusTip('Save')
        self.saveAction.triggered.connect(self.saveSeq)

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

    def saveSeq(self):
        if self.targetInstrument is not None:
            if self.targetInstrument.Get_Sequence().Get_Path() is None:
                # Sequence is new
                seqDir = self.targetInstrument.Get_Sequence_Directory()
                options = QFileDialog.Options()
                options |= QFileDialog.DontUseNativeDialog
                fileName, _ = QFileDialog.getSaveFileName(self,"Save Sequence", seqDir,"Sequence File (*.dssequence)", options=options)
                if fileName:
                    self.targetInstrument.Save_Sequence(fileName)
            else:
                self.targetInstrument.Save_Sequence(self.targetInstrument.Get_Sequence().Get_Path())

    def saveAsSeq(self):
        if self.targetInstrument is not None:
            seqDir = self.targetInstrument.Get_Sequence_Directory()
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getSaveFileName(self,"Save Sequence", seqDir,"Sequence File (*.dssequence)", options=options)
            if fileName:
                self.targetInstrument.Save_Sequence(fileName)

    def instrumentSelectionChanged(self, index):
        self.getInstrumentBoxInstrument()

    def getInstrumentBoxInstrument(self):
        index = self.instrumentSelectionBox.currentIndex()
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
            self.sequenceNavigator.setEnabled(True)
            self.Write_Setting('Instrument_Path', instrument.Get_Path())
        else:
            self.sequenceView.clearAllPlots()
            self.setWindowTitle('Sequencer (None)')
            self.sequenceNavigator.setEnabled(False)
            self.Write_Setting('Instrument_Path', None)

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
        self.Write_Setting('Sequence_Path', instrument.Get_Sequence().Get_Path())
        seqInfo = instrument.Get_Sequence()
        self.setWindowTitle('Sequencer (' + seqInfo.Get_Path() + ')')
        self.getInstrumentBoxInstrument()

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

    def getPlotByComp(self, comp):
        for plot in self.plotList:
            if plot.component is comp:
                return plot
        return None

    def loadInstrument(self, instrument):
        for component in instrument.Get_Components():
            plot = self.getPlotByComp(component)
            if plot is None:
                self.addPlot(instrument, component)
            else:
                self.drawPlotForComponent(instrument, component)
        self.canvas.restoreZoom()
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

                            #### Analog Sparse
                            for cmd in packet.Get_Commands(commandType=AnalogSparseCommand):
                                data.append(cmd.pairs)
                            if(data):
                                plotData = np.vstack(data)
                                plot.Add_Line(plotData[:,0], plotData[:,1], stepped=True)

                            #### Analog Waveform
                            for cmd in packet.Get_Commands(commandType=AnalogWaveformCommand):
                                data.append(cmd.toPairs())
                            if(data):
                                plotData = np.vstack(data)
                                plot.Add_Line(plotData[:,0], plotData[:,1], stepped=False)
                            #else:
                            #    plot.Add_Line(np.zeros(1), np.zeros(1), stepped=False)

                            #### Digital Sprase
                            for cmd in packet.Get_Commands(commandType=DigitalSparseCommand):
                                data.append(cmd.pairs)
                            if(data):
                                plotData = np.vstack(data)
                                plot.Add_Line(plotData[:,0], plotData[:,1], stepped=True)

                        else:
                            pass
                            #plot.Add_Line(np.zeros(1), np.zeros(1))

    def componentStandardFieldChanged(self, instrument, component, field):
        if instrument is self.module.targetInstrument:
            if field == 'name':
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
            plot.sequencerEditWidget.refreshTable()
            plot.sequencerEditWidget.show()
        else:
            plot.sequencerEditWidget.hide()