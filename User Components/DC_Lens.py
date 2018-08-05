# -*- coding: utf-8 -*-
"""
A simple DC Lens.
"""
from Component import Component
from PyQt5.Qt import *
from PyQt5.QtGui import *
import os
from decimal import Decimal

class User_Component(Component):
    name = ''
    componentType = 'DC Lens'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    layoutGraphicSrc = 'Lens.png'
    iconGraphicSrc = 'Lens.png'
    valid = False

    vMin = 0.0
    vMax = 0.0

    def onCreation(self):
        self.containerWidget = self.configWidgetContent()
        self.configWidget.setWidget(self.containerWidget)

    def configWidgetContent(self):
        self.container = QWidget()
        self.fbox = QFormLayout()

        self.nameBox = QLineEdit(self.name)
        self.nameBox.textChanged.connect(self.saveWidgetValues)
        self.fbox.addRow("Name:", self.nameBox)

        self.minVBox = QDoubleSpinBox()
        self.minVBox.setRange(-5000, 5000)
        self.minVBox.setValue(self.vMin)
        self.minVBox.valueChanged.connect(self.saveWidgetValues)
        self.fbox.addRow("Min (V):", self.minVBox)

        self.maxVBox = QDoubleSpinBox()
        self.maxVBox.setRange(-5000, 5000)
        self.maxVBox.setValue(self.vMax)
        self.maxVBox.valueChanged.connect(self.saveWidgetValues)
        self.fbox.addRow("Max (V):", self.maxVBox)

        self.container.setLayout(self.fbox)
        return self.container

    def saveWidgetValues(self):
        self.name = self.nameBox.text()
        self.vMin = self.minVBox.value()
        self.vMax = self.maxVBox.value()
        self.checkValidity()

    def checkValidity(self):
        if(self.vMax <= self.vMin):
            self.valid = False
            self.maxVBox.setStyleSheet("QDoubleSpinBox {background-color: red;}")
            self.minVBox.setStyleSheet("QDoubleSpinBox {background-color: red;}")
        else:
            self.valid = True
            self.maxVBox.setStyleSheet("QDoubleSpinBox {background-color: white;}")
            self.minVBox.setStyleSheet("QDoubleSpinBox {background-color: white;}")
