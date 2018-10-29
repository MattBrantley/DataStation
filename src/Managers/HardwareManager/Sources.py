from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, uuid, numpy as np
from src.Constants import DSConstants as DSConstants
from src.Managers.InstrumentManager.Sockets import *

class Source():
############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################
    def Get_Name(self):
        return self.sourceSettings['name']

    def Get_Connector_ID(self):
        return self.sourceSettings['physConID']

    def Get_Sockets(self):
        return self.getSockets()

    def Get_Source(self):
        return self

    def Get_UUID(self):
        return self.sourceSettings['uuid']

    def Get_Number_Of_Paths(self):
        return 1

    def Push_Measurement_Packet(self, measurementPacket):
        self.pushMeasurementPacket(measurementPacket)

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, name, physConID, trigger=False):
        self.iM = None
        self.sourceSettings = dict()
        self.sourceSettings['name'] = name
        self.sourceSettings['uuid'] = str(uuid.uuid4())
        self.sourceSettings['physConID'] = physConID
        self.sourceSettings['trigger'] = trigger
        self.sourceSettings['enabled'] = False
        self.programmingPacket = None
 
##### DataStation Interface Functions #####

    def readyCheck(self, traceIn):
        trace = list(traceIn).append(self)
        drivingSocketCount = 0
        for socket in self.getSockets():
            if socket.socketSettings['drivingSocket'] == True:
                drivingSocketCount = drivingSocketCount + 1

        if drivingSocketCount > 1:
            self.iM.Fail_Ready_Check(trace, 'Source Has More Than One Driving Socket!')

        if self.programmingPacket is None:
            self.iM.Fail_Ready_Check(trace, 'Active Source Has No Programming Packet')

        self.hWare.readyCheck(trace)

    def getUUID(self):
        return self.sourceSettings['uuid']

    def registerHWare(self, hWare):
        self.hWare = hWare
        self.ds = hWare.ds
        self.iM = hWare.ds.iM
        self.hM = hWare.ds.hM

    def getProgrammingPacket(self, programmingPacket):
        self.programmingPacket = programmingPacket
        self.hWare.programDataReceived(self)

    def isConnected(self):
        if(self.getSockets()):
            return True
        else:
            return False

    def pushMeasurementPacket(self, measurementPacket):
        sockets = self.Get_Sockets()
        if(sockets):
            sockets[0].getMeasurementPacket(measurementPacket)

##### Search Functions #####
    def getSockets(self):
        outputSockets = list()
        outputFilters = self.hM.Get_Filters(inputUUID = self.sourceSettings['uuid'])
        for instrument in self.iM.Get_Instruments():
            outputSockets += instrument.Get_Sockets(inputUUID = self.sourceSettings['uuid'])

        for Filter in outputFilters:
            outputSockets += Filter.Get_Sockets()

        return outputSockets

##### Functions Over-Ridden By Factoried Sources #####
    def procReverseParent(self, packetIn):
        #Source got the packet!
        return self.parsePacket(packetIn)

    def parsePacket(self, packetIn): ### OVERRIDE ME!! ####
        pass

##### Source Manipulation Functions #####
    def attachPathOther(self, uuid):
        self.sourceSettings['paths'][0] = uuid
        return True # Sources don't retain their connection information, always returns True
                    # This means anything that tells the Source it is attached will be.

    def attachPathSelf(self, pathNo, uuid):
        if(uuid is None):
            self.ds.postLog('SOURCE ATTACH ERROR: ' + self.sourceSettings['name'] + ' (' + type(self).__name__ + ') Trying To Attach To Path Filter/Socket that is NoneValue!!!' , DSConstants.LOG_PRIORITY_MED)
            self.sourceSettings['paths'][pathNo-1] = None
            return False 

        targetFilterOrSocket = self.hM.getFilterOrSourceByUUID(uuid) #Search for Filter
        if(targetFilterOrSocket is None):
            targetFilterOrSocket = self.hM.getSocketByUUID(uuid) #If it's not a filter, search for a Socket
        if(targetFilterOrSocket is None):
            self.ds.postLog('SOURCE ATTACH ERROR: ' + self.sourceSettings['name'] + ' (' + type(self).__name__ + ') Trying To Attach To Path Filter/Socket that does not exist!!!' , DSConstants.LOG_PRIORITY_MED)
            self.sourceSettings['paths'][pathNo-1] = None
            return False
        
        self.sourceSettings['paths'][pathNo-1] = uuid
        return True

    def detatchPathOther(self, uuid):
        newPaths = list()
        found = False
        for path in self.sourceSettings['paths']:
            if(path == uuid):
                newPaths.append(None)
                found = True
            else:
                newPaths.append(path)

        return found

    def savePacket(self):
        return self.sourceSettings

    def loadPacket(self, loadPacket):
        self.sourceSettings = loadPacket

    def program(self):
        self.hWare.program(self)

class AISource(Source):
    def __init__(self, name, vMin, vMax, prec, physConID, trigger=False):
        super().__init__(name, physConID, trigger=trigger)
        self.sourceSettings['vMin'] = vMin
        self.sourceSettings['vMax'] = vMax
        self.sourceSettings['prec'] = prec

    def readyCheck(self, traceIn):
        trace = list(traceIn).append(self)
        super().readyCheck(traceIn)
        if(isinstance(self.programmingPacket, waveformPacket) is False):
            self.iM.Fail_Ready_Check(trace, 'Analog Input Source Recieved Unknown Programming Packet Type!')
        
        if(self.packetInSourceRange(self.programmingPacket) is False):
            self.iM.Fail_Ready_Check(trace, 'Analog Input Source Programming Packet Out Of Source Range')

    def parsePacket(self, packetIn):
        self.programmingPacket = packetIn
        self.programmingPacket.physicalConnectorID = self.physicalConnectorID

    def packetInSourceRange(self, packetIn):
        return True

class AOSource(Source):
    def __init__(self, name, vMin, vMax, prec, physConID):
        super().__init__(name, physConID)
        self.sourceSettings['vMin'] = vMin
        self.sourceSettings['vMax'] = vMax
        self.sourceSettings['prec'] = prec

    def readyCheck(self, traceIn):
        trace = list(traceIn).append(self)
        super().readyCheck(traceIn)
        if(isinstance(self.programmingPacket, waveformPacket) is False):
            self.iM.Fail_Ready_Check(trace, 'Analog Input Source Recieved Unknown Programming Packet Type!')
        
        if(self.packetInSourceRange(self.programmingPacket) is False):
            self.iM.Fail_Ready_Check(trace, 'Analog Input Source Programming Packet Out Of Source Range')

    def parsePacket(self, packetIn):
        self.programmingPacket = packetIn
        self.programmingPacket.physicalConnectorID = self.physicalConnectorID
            
    def packetInSourceRange(self, packetIn):
        if(packetIn.waveformData is None):
            return True
        yAxis = packetIn.waveformData[:,1]
        if(yAxis.max() > self.vMax):
            return False
        if(yAxis.min() < self.vMin):
            return False

        return True

class DOSource(Source):
    def __init__(self, name, physConID):
        super().__init__(name, physConID)

    def readyCheck(self, traceIn):
        trace = list(traceIn).append(self)
        super().readyCheck(traceIn)
        if(isinstance(self.programmingPacket, waveformPacket) is False):
            self.iM.Fail_Ready_Check(trace, 'Analog Input Source Recieved Unknown Programming Packet Type!')
        
        if(self.packetInSourceRange(self.programmingPacket) is False):
            self.iM.Fail_Ready_Check(trace, 'Analog Input Source Programming Packet Out Of Source Range')

    def parsePacket(self, packetIn):
        self.programmingPacket = packetIn
        self.programmingPacket.physicalConnectorID = self.physicalConnectorID

    def packetInSourceRange(self, packetIn):
        return True

class DISource(Source):
    def __init__(self, name, physConID, trigger=False):
        super().__init__(name, physConID, trigger=trigger)

    def readyCheck(self, traceIn):
        trace = list(traceIn).append(self)
        super().readyCheck(traceIn)
        if(isinstance(self.programmingPacket, waveformPacket) is False):
            self.iM.Fail_Ready_Check(trace, 'Analog Input Source Recieved Unknown Programming Packet Type!')
        
        if(self.packetInSourceRange(self.programmingPacket) is False):
            self.iM.Fail_Ready_Check(trace, 'Analog Input Source Programming Packet Out Of Source Range')

    def parsePacket(self, packetIn):
        self.programmingPacket = packetIn
        self.programmingPacket.physicalConnectorID = self.physicalConnectorID

    def packetInSourceRange(self, packetIn):
        return True