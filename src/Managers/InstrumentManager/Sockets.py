from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, uuid
from src.Constants import DSConstants as DSConstants, readyCheckPacket
from src.Managers.HardwareManager.Sources import Source

class Socket():
############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Get_Name(self):
        return self.socketSettings['name']

    def Get_Source(self):
        return self.getSource()

    def Get_Sockets(self):
        return self

    def Get_UUID(self):
        return self.socketSettings['uuid']

    def Get_Input_UUID(self):
        if(self.socketSettings['inputSourcePathNo'] is None):
            return None
        else:
            return self.socketSettings['inputSource']

    def Get_Input_Path_Number(self):
        if(self.socketSettings['inputSource'] is None):
            return None
        else:
            return self.socketSettings['inputSourcePathNo']

    def Attach_Input(self, uuid, pathNo):
        self.attach(uuid, pathNo)

    def Detatch_Input(self):
        self.detatch()

    def Get_Programming_Packet(self):
        return self.programmingPacket

    def Set_Programming_Packet(self, packet):
        self.programmingPacket = packet

############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, cP, name):
        super().__init__()
        self.socketSettings = dict()
        self.socketSettings['tag'] = '[??]'
        self.socketSettings['name'] = name
        self.socketSettings['inputSource'] = None
        self.socketSettings['inputSourcePathNo'] = None
        self.socketSettings['uuid'] = str(uuid.uuid4())
        self.socketSettings['drivingSocket'] = True
        self.cP = cP
        self.iM = cP.iM
        self.hM = cP.iM.hM
        self.mW = cP.iM.mW

        self.programmingPacket = None

##### DataStation Interface Functions #####

    def readyCheck(self):
        if(self.getSource() is not None):
            return readyCheckPacket('Socket [' + self.socketSettings['name'] + ']', DSConstants.READY_CHECK_READY)
        else:
            return readyCheckPacket('Socket [' + self.socketSettings['name'] + ']', DSConstants.READY_CHECK_ERROR, msg='Socket Has No Source!')

    def getUUID(self):
        return self.socketSettings['uuid']

    def pushProgramming(self):
        target = self.getInputObject()
        if(target is not None):
            target[0].getProgrammingPacket(self.programmingPacket)

##### Search Functions #####

    def getInputObject(self):
        if(self.socketSettings['inputSource'] is None or self.socketSettings['inputSourcePathNo'] is None):
            return None
        else:
            inputObj = self.hM.Get_Filters(uuid=self.socketSettings['inputSource'])
            if not inputObj:
                inputObj = self.hM.Get_Sources(uuid=self.socketSettings['inputSource'])
            if not inputObj:
                return None
        return inputObj

    def getSource(self):
        inputObj = self.getInputObject()
        if(inputObj is None):
            return None
        if(issubclass(Source, type(inputObj[0])) is True):
            return inputObj[0]
        else:
            return inputObj[0].Get_Source()

##### Socket Manipulation Functions #####

    def savePacket(self):
        return self.socketSettings

    def loadPacket(self, loadPacket):
        if(isinstance(loadPacket, dict) is False):
            return #loadPacket is malformed - can't run

        for key, value in loadPacket.items():
            self.socketSettings[key] = value

        #self.restoreState()

    def restoreState(self):
        if(self.socketSettings['inputSource'] is None):
            self.socketSettings['inputSourcePathNo'] = None
            return # Previous socket state was not connected to anything
        if(self.socketSettings['inputSourcePathNo'] is None):
            self.socketSettings['inputSource'] = None
            return # Previous socket state was not connected to anything; even if it was, we don't know to what path.

        target = self.hM.Get_Sources(uuid=self.socketSettings['inputSource'])
        if(len(target) == 0):
            target = self.hM.Get_Filters(uuid=self.socketSettings['inputSource'])

        if(len(target) == 0):
            self.socketSettings['inputSource'] = None
            self.socketSettings['inputSourcePathNo'] = None
            self.mW.postLog('SOCKET RESTORE ERROR: ' + self.socketSettings['name'] + ' (' + type(self).__name__ + ') Trying To Attach To Filter/Source that does not exist!!!' , DSConstants.LOG_PRIORITY_MED)
            return # No Filter or Source found at that uuid - clear this socket's reference.
        
    def detatch(self):
        self.socketSettings['inputSource'] = None
        self.socketSettings['inputSourcePathNo'] = None
        self.cP.socketDetatched(self)

    def attach(self, uuid, pathNumber):
        # Remove anything else that has a connection to what this is connecting to
        filtersAttached = self.hM.Get_Filters(inputUUID = uuid, pathNo=pathNumber)
        for Filter in filtersAttached:
            Filter.Detatch_Input()
        if(self.iM.Get_Instrument() is not None):
            socketsAttached = self.iM.Get_Instrument().Get_Sockets(inputUUID = uuid, pathNo=pathNumber)
            for Socket in socketsAttached:
                Socket.Detatch_Input()

        self.socketSettings['inputSource'] = uuid
        self.socketSettings['inputSourcePathNo'] = pathNumber
        self.cP.socketAttached(self)
            
    def sendData(self, packet): ### STILL NEEDS ADDRESSING
        # There used to be some RadyCheck Syntax here - I couldn't understand it so I cut it out.
        # I will need to add it back in at some point
        pass

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
