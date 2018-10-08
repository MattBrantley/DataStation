from PyQt5.Qt import *
import os, time

class loadingScreenWidget(QMainWindow):
    def __init__(self, core):
        super().__init__(None)
        self.core = core

        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)

        self.splashImage = QPixmap(os.path.join(self.core.srcDir, r'DSIcons\DataStation_Full.png'))
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

        self.setCentralWidget(self.mainWidget)
        self.centerWindow()
        self.show()

        self.core.Log_Posted.connect(self.postLog)

    def postLog(self, text, **kwargs):
        if('newline' in kwargs):
            if(kwargs['newline'] == False):
                self.logWindow.insertPlainText(text)
                return

        self.logWindow.appendPlainText(time.strftime('[%m/%d/%Y %H:%M:%S] ') + text)
        self.logWindow.verticalScrollBar().setValue(self.logWindow.verticalScrollBar().maximum())
        

    def centerWindow(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

