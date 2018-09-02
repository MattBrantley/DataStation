from PyQt5.Qt import *
import time

class logDockWidget(QDockWidget):
    ITEM_GUID = Qt.UserRole

    def __init__(self, mW):
        super().__init__('Log')
        self.logTextEdit = QPlainTextEdit()
        self.resize(600, 200)

        #self.hide()
        self.setWidget(self.logTextEdit)
        self.mW = mW
        self.logTextEdit.setReadOnly(True)

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