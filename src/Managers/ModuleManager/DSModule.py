from PyQt5.Qt import *

class DSModule(QDockWidget):
    
############################################################################################
##################################### EXTERNAL SIGNALS #####################################
    

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################


############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, mW):
        super().__init__()
        self.mW = mW
        self.iM = mW.iM
        self.hM = mW.hM
        self.mM = mW.mM
        self.wM = mW.wM

        #self.widget = QListWidget()
        #self.widget.setMinimumSize(300, 300)
        #self.layout().addWidget(self.widget)
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)

        self.setWidget(self.mainWidget)

        self.mainLayout.addWidget(QPushButton('Hi'))