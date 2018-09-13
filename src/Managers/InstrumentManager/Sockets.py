from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import uuid
import os, sys, imp, math
from Constants import DSConstants as DSConstants
from DSWidgets.controlWidget import readyCheckPacket

class Socket(QObject):

    def __init__(self, cP, name):
        super().__init__()
        self.socketSettings = dict()
        self.socketSettings['tag'] = '[??]'
        self.socketSettings['name'] = name
        self.socketSettings['filterInputSource'] = None
        self.socketSettings['uuid'] = str(uuid.uuid4())
        self.socketSettings['paths'] = None
        self.socketSettings['drivingSocket'] = True
        self.cP = cP
        self.iM = cP.iM
        self.mW = cP.iM.mW

##### DataStation Interface Functions #####

    def readyCheck(self):
        if(self.getSource() is not None):
            return readyCheckPacket('Socket [' + self.socketSettings['name'] + ']', DSConstants.READY_CHECK_READY)
        else:
            return readyCheckPacket('Socket [' + self.socketSettings['name'] + ']', DSConstants.READY_CHECK_ERROR, msg='Socket Has No Source!')

    def getUUID(self):
        return self.socketSettings['uuid']

##### Search Functions #####

    def getSockets(self):
        return self

    def getSource(self):
        if(self.socketSettings['filterInputSource'] is not None):
            return self.socketSettings['filterInputSource'].getSource()
        else:
            return None

##### Socket Manipulation Functions #####

    def savePacket(self):
        return self.socketSettings

    def loadPacket(self, loadPacket):
        if(isinstance(loadPacket, dict) is False):
            return #loadPacket is malformed - can't run

        for key, value in loadPacket.items():
            self.socketSettings[key] = value

        self.restoreState()

    def restoreState(self):
        if(self.socketSettings['filterInputSource'] is None):
            return # Previous socket state was not connected to anything

        targetFilterOrSource = self.iM.getFilterOrSourceByUUID(self.socketSettings['filterInputSource'])

        if(targetFilterOrSource is None):
            self.socketSettings['filterInputSource'] = None
            self.mW.postLog('SOCKET RESTORE ERROR: ' + self.socketSettings['name'] + ' (' + type(self).__name__ + ') Trying To Attach To Filter/Source that does not exist!!!' , DSConstants.LOG_PRIORITY_MED)
            return # No Filter or Source found at that uuid - clear this socket's reference.

        if(targetFilterOrSource.reattachPath(self, self.socketSettings['uuid']) is False):
            self.socketSettings['filterInputSource'] = None 
            self.mW.postLog('SOCKET RESTORE ERROR: ' + self.socketSettings['name'] + ' (' + type(self).__name__ + ') Trying To Attach To Filter/Source that does not recognize it!!!' , DSConstants.LOG_PRIORITY_MED)
            return # The target Filter or Source did not recognize this Socket - clear this socket's reference.
        
    def attachInputOther(self, uuid):
        self.socketSettings['filterInputSource'] = uuid
        self.cP.socketAttached(self)

    def detatchInputSelf(self):
        if(self.socketSettings['filterInputSource'] is None):
            return # This socket isn't attached - so no need to detatch it

        # Since this is a self detatchment, it looks for the other side of the linkage to notify it
        targetFilterOrSource = self.iM.getFilterOrSourceByUUID(self.socketSettings['filterInputSource'])
        self.socketSettings['filterInputSource'] = None
        if(targetFilterOrSource is None):
            self.mW.postLog('SOCKET DETATCH WARNING: ' + self.socketSettings['name'] + ' (' + type(self).__name__ + ') Detatched Socket from Filter/Source that does not exist!!!' , DSConstants.LOG_PRIORITY_MED)
            return # Our reference was for an object that doesn't exist

        if(targetFilterOrSource.detatchPathOther(self.socketSettings['uuid']) is False):
            self.mW.postLog('SOCKET DETATCH WARNING: ' + self.socketSettings['name'] + ' (' + type(self).__name__ + ') Detatched Socket from Filter/Source that does not recognize it!!' , DSConstants.LOG_PRIORITY_MED)
            return # Our reference doesn't have a linkage to this socket

        self.cP.socketDetatched(self)

    def detatchInputOther(self, uuid):
        if(self.socketSettings['filterInputSource'] != uuid):
            return False
        else:
            self.socketSettings['filterInputSource'] = None # Socket recognizes this uuid as being it's input source and acknowledges the detatchment
            
    def sendData(self, packet):
        # There used to be some RadyCheck Syntax here - I couldn't understand it so I cut it out.
        # I will need to add it back in at some point
        self.filterInputSource.procReverseParent(self.getUUID(), packet)

class AOSocket(Socket):
    def __init__(self, cP, name, vMin, vMax, prec):
        super().__init__(cP, name)
        self.socketSettings['tag'] = '[AO]'
        self.socketSettings['vMin'] = vMin
        self.socketSettings['vMax'] = vMax
        self.socketSettings['prec'] = prec

class AISocket(Socket):
    def __init__(self, cP, name, vMin, vMax, prec):
        super().__init__(cP, name)
        self.socketSettings['tag'] = '[AI]'
        self.socketSettings['vMin'] = vMin
        self.socketSettings['vMax'] = vMax
        self.socketSettings['prec'] = prec

class DOSocket(Socket):
    def __init__(self, cP, name):
        super().__init__(cP, name)
        self.socketSettings['tag'] = '[DO]'
        
class DISocket(Socket):
    def __init__(self, cP, name):
        super().__init__(cP, name)
        self.socketSettings['tag'] = '[DI]'

class waveformPacket():
    def __init__(self, waveformData, rate=None):
        self.waveformData = waveformData
        self.physicalConnectorID = ''
        self.rate = rate