import os, sys, imp, time, inspect, json as json, uuid
from src.Constants import DSConstants as DSConstants
from src.Constants import readyCheckPacket
from PyQt5.Qt import *

class WorkspaceManager(QObject):

############################################################################################
##################################### EXTERNAL SIGNALS #####################################

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        
    def connections(self, iM, hM):
        self.iM = iM
        self.hM = hM
