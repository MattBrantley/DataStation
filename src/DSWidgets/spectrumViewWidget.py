from PyQt5.Qt import *
import pyqtgraph as pg
from bokeh.io import output_notebook, show, save
from bokeh.plotting import figure, output_file
from bokeh.embed import file_html
from bokeh.resources import Resources
from bokeh.server.server import Server
from bokeh.themes import Theme
from bokeh.layouts import layout
import numpy as np
from PyQt5.QtWebEngineWidgets import QWebEngineView
import asyncio
import holoviews as hv
import datashader as ds
from holoviews.operation.datashader import datashade, rasterize
hv.extension('bokeh')

from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider

from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature

class spectrumViewWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole
    startBokehSever = pyqtSignal(object) # bokehEventLoop
    stopBokehServer = pyqtSignal()

    def __init__(self, mW):
        super().__init__('Spectrum View')
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.pen = pg.mkPen(QColor(0,0,0), width=2)

        self.initBokehServer()

        self.browser = QWebEngineView()
        self.setWidget(self.browser)

        self.iM.Socket_Measurement_Packet_Recieved.connect(self.measurementRecieved)
        self.mW.DataStation_Closing.connect(self.closeServer)

    def initBokehServer(self):
        self.bokehEventLoop = asyncio.new_event_loop()
        self.bokehServer = bokehServer()
        self.thread = QThread()

        self.bokehServer.moveToThread(self.thread)

        self.startBokehSever.connect(self.bokehServer.startServer)
        self.stopBokehServer.connect(self.bokehServer.stopServer)

        self.thread.start()
        self.startBokehSever.emit(self.bokehEventLoop)

    def closeServer(self):
        self.stopBokehServer.emit()
        
    def plot(self, data):
        self.bokehEventLoop.call_soon_threadsafe(self.bokehServer.newData, data)
        self.browser.load(QUrl('http://localhost:5006/sequencer'))

    def measurementRecieved(self, instrument, component, socket, measurementPacket):
        data = measurementPacket.Get_Measurements()
        self.plot(data[0])

class bokehServer(QObject):
    
    def __init__(self):
        super().__init__()

    def startServer(self, eventLoop):
        self.plotData = None
        asyncio.set_event_loop(eventLoop)
        self.server = Server({'/sequencer': self.modify_doc}, num_procs=1)
        self.server.start()
        self.server.io_loop.start()

    def stopServer(self):
        self.server.stop()

    def newData(self, data):
        p = figure(plot_width=400, plot_height=400, title="Transient")
        t = np.arange(0, data.wave.shape[0], 1)
        t = np.multiply(t, 1/data.f)
        p.line(t, data.wave)
        grid = layout(children=[[p]], sizing_mode='stretch_both', merge_tools=True)
        self.plotData = grid

    def modify_doc(self, doc):
        if(self.plotData is not None):
            grid = self.plotData
            doc.add_root(grid)

        doc.theme = Theme(filename='D:/InstrPlatform/DataStation/src/TestScripts/theme.yaml')
