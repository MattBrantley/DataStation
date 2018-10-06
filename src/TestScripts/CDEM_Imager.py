from PyQt5.QtChart import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys, math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import numpy as np

class TestWindow(QMainWindow):
    def __init__(self, parent=None):
        super(TestWindow, self).__init__(parent=parent)
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)
        self.mainLayout.setSpacing(0)

        self.setCentralWidget(self.mainWidget)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = TestWindow()
    window.show()
    window.resize(500, 400)
    sys.exit(app.exec_())