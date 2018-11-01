from PyQt5.Qt import *
import time, os
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs
from src.Constants import logObject

class logView(DSModule):
    Module_Name = 'Log View'
    Module_Flags = [mfs.CAN_DELETE, mfs.CAN_FLOAT, mfs.LATE_CLOSE]

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.logTextEdit = QPlainTextEdit()
        self.resize(600, 200)
        self.logPath = os.path.join(self.modDataPath, 'Logs')
        #self.setFeatures(QtGui.QDockWidget.DockWidgetFloatable | QtGui.QDockWidget.DockWidgetMovable)
        #self.hide()
        self.initTime = time.localtime()
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

        self.currentLogFile = os.path.join(self.logPath, time.strftime('%m_%d_%Y____%H_%M_%S', self.initTime) + '.txt')
        os.makedirs(os.path.dirname(self.currentLogFile), exist_ok=True)

        for logItem in self.ds.logText:
            self.postLog(logItem)

    def writeToLogFile(self, logText):

        with open(self.currentLogFile, 'a') as file:
            file.write(logText + '\n')
            

    def postLog(self, log, **kwargs):
        if('newline' in kwargs):
            if(kwargs['newline'] == False):
                self.logTextEdit.insertPlainText(log.text)
                return

        self.logTextEdit.appendPlainText(log.timeText() + log.text)
        self.writeToLogFile(log.timeText() + log.text)
        #self.logTextEdit.appendPlainText(time.strftime('[%m/%d/%Y %H:%M:%S] ') + text)
        self.logTextEdit.verticalScrollBar().setValue(self.logTextEdit.verticalScrollBar().maximum())
        