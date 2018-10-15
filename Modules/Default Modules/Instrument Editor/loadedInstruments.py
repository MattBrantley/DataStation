from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import os

class loadedInstruments(QWidget):
    def __init__(self, module):
        super().__init__(None)
        self.module = module
        self.ds = module.ds
        self.iM = module.ds.iM
        self.widgetList = list()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addStretch()

    def clear(self):
        for widget in self.widgetList:
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self.widgetList.clear()
        
    def addInstrument(self, instrument):
        widget = instrumentItemWidget(self.module, instrument)
        self.widgetList.append(widget)

        self.layout.insertWidget(self.layout.count()-1, widget)

class instrumentItemWidget(QWidget):
    def __init__(self, module, instrument):
        super().__init__(None)
        self.instrument = instrument
        self.module = module

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.nameWidget = QLabel(self.instrument.Get_Name())
        self.another = QPushButton(QIcon(os.path.join(module.ds.srcDir, 'icons5/cancel-2.png')), '')
        self.another.pressed.connect(self.closeButton)
        self.layout.addWidget(self.nameWidget)
        self.layout.addWidget(self.another)

    def closeButton(self):
        self.module.iM.closeInstrument(self.instrument)