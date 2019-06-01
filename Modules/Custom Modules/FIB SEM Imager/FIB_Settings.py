from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import os

class FIB_Settings(QWidget):
    def __init__(self, module):
        super().__init__(None)
        self.module = module
        self.ds = module.ds
        self.iM = module.ds.iM

        self.dirtyFlag = True

        self.setupUI()

    def setupUI(self):
        self.layout = QFormLayout()

        self.XResolution = QLineEdit('500')
        self.XResolution.setEnabled(True)
        self.XResolutionValidator = QIntValidator(50, 5000)
        self.XResolution.setValidator(self.XResolutionValidator)

        self.YResolution = QLineEdit('500')
        self.YResolution.setEnabled(True)
        self.YResolutionValidator = QIntValidator(50, 5000)
        self.YResolution.setValidator(self.XResolutionValidator)

        self.dwellTime = QLineEdit('1')
        self.dwellTime.setEnabled(True)
        self.dwellTimeValidator = QDoubleValidator(0.001, 50, 3)
        self.dwellTime.setValidator(self.dwellTimeValidator)

        self.XAmplitude = QLineEdit('10')
        self.XAmplitude.setEnabled(True)
        self.XAmplitudeValidator = QDoubleValidator(0.01, 10, 2)
        self.XAmplitude.setValidator(self.XAmplitudeValidator)

        self.YAmplitude = QLineEdit('10')
        self.YAmplitude.setEnabled(True)
        self.YAmplitudeValidator = QDoubleValidator(0.01, 10, 2)
        self.YAmplitude.setValidator(self.YAmplitudeValidator)

        self.pixelCount = QLineEdit('')
        self.pixelCount.setEnabled(False)

        self.imageTime = QLineEdit('')
        self.imageTime.setEnabled(False)

        self.layout.addRow('X Resolution (px): ', self.XResolution)
        self.layout.addRow('Y Resolution (px): ', self.YResolution)
        self.layout.addRow('X Amplitude (V): ', self.XAmplitude)
        self.layout.addRow('Y Amplitude (V): ', self.YAmplitude)
        self.layout.addRow('Dwell Time (us): ', self.dwellTime)
        self.layout.addRow('Pixel Count: ', self.pixelCount)
        self.layout.addRow('Image Time (ms): ', self.imageTime)

        self.setLayout(self.layout)

        self.updateUI()

        self.XResolution.textChanged.connect(self.setDirtyFlag)
        self.YResolution.textChanged.connect(self.setDirtyFlag)
        self.XAmplitude.textChanged.connect(self.setDirtyFlag)
        self.YAmplitude.textChanged.connect(self.setDirtyFlag)
        self.dwellTime.textChanged.connect(self.setDirtyFlag)

        self.XResolution.editingFinished.connect(self.updateUI)
        self.YResolution.editingFinished.connect(self.updateUI)
        self.XAmplitude.editingFinished.connect(self.updateUI)
        self.YAmplitude.editingFinished.connect(self.updateUI)
        self.dwellTime.editingFinished.connect(self.updateUI)

    def setDirtyFlag(self):
        self.dirtyFlag = True

    def updateUI(self):
        if self.dirtyFlag:
            numPixels = int(self.XResolution.text()) * int(self.YResolution.text())
            self.pixelCount.setText(str(numPixels))

            imageTime = numPixels*float(self.dwellTime.text())/1000
            self.imageTime.setText(str(imageTime))

            progData = {}
            progData['XResolution'] = int(self.XResolution.text())
            progData['YResolution'] = int(self.YResolution.text())
            progData['XAmplitude'] = int(self.XAmplitude.text())
            progData['YAmplitude'] = int(self.YAmplitude.text())
            progData['Dwell Time'] = float(self.dwellTime.text())

            self.module.updateProgramming(progData=progData)

            self.dirtyFlag = False