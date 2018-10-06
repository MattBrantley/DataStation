from PyQt5.Qt import *

class DSWindow(QMainWindow):

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    
############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, mW):
        super().__init__()
        self.mW = mW
        self.AnimatedDocks = True
        self.setDockNestingEnabled(True)
        self.setGeometry(300, 300, 1280, 720)
        self.show()

##### Modules #####
    def transferModule(self, module):
        self.addDockWidget(Qt.LeftDockWidgetArea, module)
