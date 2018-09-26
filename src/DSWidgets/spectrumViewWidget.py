from PyQt5.Qt import *
import pyqtgraph as pg
from bokeh.io import output_notebook, show, save
from bokeh.plotting import figure, output_file
from bokeh.embed import file_html
from bokeh.resources import Resources
from bokeh.layouts import layout
import numpy as np
from PyQt5.QtWebEngineWidgets import QWebEngineView

class spectrumViewWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole

    def __init__(self, mW):
        super().__init__('Spectrum View')
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.wM = mW.wM
        self.pen = pg.mkPen(QColor(0,0,0), width=2)

        #self.graphicsLayout = pg.GraphicsLayoutWidget()
        #self.graphicsLayout.setBackground(QColor(255, 255, 255))
        #self.transientPlot = self.graphicsLayout.addPlot()

        self.browser = QWebEngineView()
        #self.browser.load(QUrl("http://news.google.com"))

        self.setWidget(self.browser)
        self.iM.Socket_Measurement_Packet_Recieved.connect(self.measurementRecieved)

        
    def plot(self, data):
        #print('plotting')
        #output_file('test', title='Bokeh Test', mode='inline')
        p = figure(plot_width=400, plot_height=400, title="Bokeh")
        print(data.wave.shape)
        t = np.arange(0, data.wave.shape[0], 1)
        t = np.multiply(t, 1/data.f)
        p.line(t, data.wave)
        grid = layout(children=[[p]], sizing_mode='stretch_both', merge_tools=True)
        save(grid)
        html = file_html(grid, Resources(mode='cdn'), 'test') #change 'cdn' to 'inline' for offline viewing
        self.browser.setHtml(html)
        #print(html)
        #show(p)

        #self.transientPlot.clear()
        #plotItem = pg.PlotDataItem(y=data, pen = self.pen)
        #self.transientPlot.addItem(plotItem)
        #self.transientPlot.getViewBox().autoRange()

    def measurementRecieved(self, instrument, component, socket, measurementPacket):
        data = measurementPacket.Get_Measurements()
        self.plot(data[0])
        print('SpecWidget got signal!')