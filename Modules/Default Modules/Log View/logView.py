from PyQt5.Qt import *
import time
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs
from src.Constants import logObject

class logView(DSModule):
    Module_Name = 'Log View'
    Module_Flags = [mfs.CAN_DELETE, mfs.CAN_FLOAT]

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.logTextEdit = QPlainTextEdit()
        self.resize(600, 200)
        #self.setFeatures(QtGui.QDockWidget.DockWidgetFloatable | QtGui.QDockWidget.DockWidgetMovable)
        #self.hide()
        self.setWidget(self.logTextEdit)
        self.ds = ds
        self.logTextEdit.setReadOnly(True)
        self.logTextEdit.setWordWrapMode(QTextOption.NoWrap)
        #self.logTextEdit.setCenterOnScroll(True)

        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(8)

        self.logTextEdit.setFont(font)

        for logItem in self.ds.logText:
            self.postLog(logItem)

    def postLog(self, log, **kwargs):
        if('newline' in kwargs):
            if(kwargs['newline'] == False):
                self.logTextEdit.insertPlainText(log.text)
                return

        self.logTextEdit.appendPlainText(log.timeText() + log.text)
        #self.logTextEdit.appendPlainText(time.strftime('[%m/%d/%Y %H:%M:%S] ') + text)
        self.logTextEdit.verticalScrollBar().setValue(self.logTextEdit.verticalScrollBar().maximum())
        