import time
import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class threadTest(QThread):
    responseA = pyqtSignal()
    responseB = pyqtSignal()
    responseC = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.state = 'A'

    def run(self):
        while(True):
            self.sleep(1)
            if(self.state == 'A'):
                self.responseA.emit()
            elif(self.state == 'B'):
                self.responseB.emit()
            elif(self.state == 'C'):
                self.responseC.emit()

    def slotA(self):
        self.state = 'A'

    def slotB(self):
        self.state = 'B'

    def slotC(self):
        self.state = 'C'

class mainWindow(QMainWindow):
    signalA = pyqtSignal()
    signalB = pyqtSignal()
    signalC = pyqtSignal()

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.initUI()
        self.initThread()

    def initUI(self):
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

        self.listBox = QListWidget()
        self.buttonA = QPushButton('Start A')
        self.buttonA.pressed.connect(self.APressed)
        self.buttonB = QPushButton('Start B')
        self.buttonB.pressed.connect(self.BPressed)
        self.buttonC = QPushButton('Start C')
        self.buttonC.pressed.connect(self.CPressed)

        self.mainLayout.addWidget(self.listBox)
        self.mainLayout.addWidget(self.buttonA)
        self.mainLayout.addWidget(self.buttonB)
        self.mainLayout.addWidget(self.buttonC)

        self.resize(500,500)
        self.show()

    def initThread(self):
        self.thread = threadTest()
        self.signalA.connect(self.thread.slotA)
        self.signalB.connect(self.thread.slotB)
        self.signalC.connect(self.thread.slotC)
        self.thread.start()
        self.thread.responseA.connect(self.AResponse)
        self.thread.responseB.connect(self.BResponse)
        self.thread.responseC.connect(self.CResponse)

    def APressed(self):
        print('[Main] A was pressed.')
        self.signalA.emit()

    def BPressed(self):
        print('[Main] B was pressed.')
        self.signalB.emit()

    def CPressed(self):
        print('[Main] C was pressed.')
        self.signalC.emit()

    def AResponse(self):
        self.listBox.addItem(QListWidgetItem('Reponse A'))

    def BResponse(self):
        self.listBox.addItem(QListWidgetItem('Reponse B'))

    def CResponse(self):
        self.listBox.addItem(QListWidgetItem('Reponse C'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mW = mainWindow(app)
    try:
        sys.exit(app.exec_())
    except:
        pass

 