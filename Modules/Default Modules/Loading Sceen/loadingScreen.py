from PyQt5.Qt import *
import os, time
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class loadingScreen(DSModule):
    Module_Name = 'Default Loading Screen'
    Module_Flags = []

    def __init__(self, ds):
        super().__init__(ds)
        self.ds = ds
        self.setWindowTitle('DataStation is Loading..')

        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)

        self.splashImage = QPixmap(os.path.join(self.ds.srcDir, r'DSIcons\DataStation_Full.png'))
        self.logoWidget = QLabel(self)
        self.logoWidget.setPixmap(self.splashImage)
        self.resize(self.splashImage.width(), self.splashImage.height())

        self.logWindow = QPlainTextEdit()
        self.logWindow.setMinimumHeight(300)
        self.logWindow.setReadOnly(True)
        self.logWindow.setWordWrapMode(QTextOption.NoWrap)

        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(8)

        self.logWindow.setFont(font)

        self.mainLayout.addWidget(self.logoWidget)
        self.mainLayout.addWidget(self.logWindow)

        self.setWidget(self.mainWidget)

        self.ds.Log_Posted.connect(self.postLog)

    def postLog(self, text, **kwargs):
        if('newline' in kwargs):
            if(kwargs['newline'] == False):
                self.logWindow.insertPlainText(text)
                return

        self.logWindow.appendPlainText(time.strftime('[%m/%d/%Y %H:%M:%S] ') + text)
        self.logWindow.verticalScrollBar().setValue(self.logWindow.verticalScrollBar().maximum())
    