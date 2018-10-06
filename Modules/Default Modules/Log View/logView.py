from PyQt5.Qt import *
import time
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class logView(DSModule):
    Module_Name = 'Log View'
    Module_Flags = [mfs.SHOW_ON_CREATION, mfs.FLOAT_ON_CREATION]

    def __init__(self, mW):
        super().__init__(mW)
        self.logTextEdit = QPlainTextEdit()
        self.resize(600, 200)
        #self.setFeatures(QtGui.QDockWidget.DockWidgetFloatable | QtGui.QDockWidget.DockWidgetMovable)
        #self.hide()
        self.setWidget(self.logTextEdit)
        self.mW = mW
        self.logTextEdit.setReadOnly(True)
        self.logTextEdit.setWordWrapMode(QTextOption.NoWrap)
        #self.logTextEdit.setCenterOnScroll(True)

        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(8)

        self.logTextEdit.setFont(font)

    def postLog(self, text, **kwargs):
        if('newline' in kwargs):
            if(kwargs['newline'] == False):
                self.logTextEdit.insertPlainText(text)
                return

        self.logTextEdit.appendPlainText(time.strftime('[%m/%d/%Y %H:%M:%S] ') + text)
        self.logTextEdit.verticalScrollBar().setValue(self.logTextEdit.verticalScrollBar().maximum())
        