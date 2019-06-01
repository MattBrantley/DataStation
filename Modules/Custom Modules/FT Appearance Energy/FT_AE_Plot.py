from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import os

class FT_AE_Plot(QWidget):
    def __init__(self, module):
        super().__init__(None)
        self.module = module
        self.ds = module.ds
        self.iM = module.ds.iM

        