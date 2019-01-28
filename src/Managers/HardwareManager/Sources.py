from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, uuid, numpy as np
from src.Constants import DSConstants as DSConstants
from src.Managers.InstrumentManager.Sockets import *
from src.Managers.HardwareManager.PacketCommands import *

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

    def Get_Hardware_Device(self):
        return self.handler

    def Get_Programming_Instrument(self):
        return self.getProgrammingInstrument()

    def Get_Handler(self):
        return self.Get_Hardware_Device()

    def Get_UUID(self):
        return self.sourceSettings['uuid']

    def Get_Number_Of_Paths(self):
        return 1

    def Push_Measurement_Packet(self, measurementPacket):
        self.pushMeasurementPacket(measurementPacket)

    def Is_Registered(self):
        if self.isRegistered is True:
            return True
        else:
            return False

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, handler, name, physConID, trigger=False):
        self.iM = None
        self.handler = handler
        self.isRegistered = False
        self.sourceSettings = dict()
        self.sourceSettings['name'] = name
        self.sourceSettings['uuid'] = str(uuid.uuid4())
        self.sourceSettings['physConID'] = physConID
        self.sourceSettings['trigger'] = trigger
        self.sourceSettings['enabled'] = False
        self.programmingPacket = None
 
##### DataStation Interface Functions #####

    def readyCheck(self, traceIn):
        if self.Is_Registered() is False:
            return False

        trace = traceIn.copy()
        trace.append(self)

        socketInstrumentUUIDList = list()
        for socket in self.getSockets():
            if socket.socketSettings['drivingSocket'] == True:
                socketInstrumentUUIDList.append(socket.Get_Component().Get_Instrument().Get_UUID())
        if len(socketInstrumentUUIDList) != len(set(socketInstrumentUUIDList)):
            trace[0].Fail_Ready_Check(trace, 'Source Has More Than One Driving Socket From An Instrument!')
            return False

        #drivingSocketCount = 0
        #for socket in self.getSockets():
        #    if socket.socketSettings['drivingSocket'] == True:
        #        drivingSocketCount = drivingSocketCount + 1

        #if drivingSocketCount > 1:
        #    trace[0].Fail_Ready_Check(trace, 'Source Has More Than One Driving Socket!')
        #    return False

        if self.programmingPacket is None:
            trace[0].Fail_Ready_Check(trace, 'Active Source Has No Programming Packet')
            return False

        self.hWare.readyCheck(trace)
        return True

    def getUUID(self):
        return self.sourceSettings['uuid']

    def registerHWare(self, hWare):
        self.hWare = hWare
        self.ds = hWare.ds
        self.iM = hWare.ds.iM
        self.hM = hWare.ds.hM
        self.isRegistered = True

    def getProgrammingPacket(self, programmingPacket):
        self.programmingPacket = programmingPacket
        self.hWare.Set_Active_Instrument(self.Get_Programming_Instrument())
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

    def getProgrammingInstrument(self):
        if self.programmingPacket is not None:
            return self.programmingPacket.Get_Origin_Socket().Get_Component().Get_Instrument()
        else:
            return None

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
    def __init__(self, handler, name, vMin, vMax, prec, physConID, trigger=False):
        super().__init__(handler, name, physConID, trigger=trigger)
        self.sourceSettings['vMin'] = vMin
        self.sourceSettings['vMax'] = vMax
        self.sourceSettings['prec'] = prec

    def readyCheck(self, traceIn):
        if super().readyCheck(traceIn) is False:
            return
        trace = traceIn.copy()
        trace.append(self)

        for command in self.programmingPacket.Get_Commands():
            if(isinstance(command, AnalogAcquisitionCommand) is False):
                trace[0].Fail_Ready_Check(trace, 'Analog Input Source Recieved Unknown Programming Packet Type! ' + command.__str__())
            else:
                if(self.commandInSourceRange(command) is False):
                    trace[0].Fail_Ready_Check(trace, 'Analog Input Source Programming Packet Out Of Source Range')

    def parsePacket(self, packetIn):
        self.programmingPacket = packetIn
        self.programmingPacket.physicalConnectorID = self.physicalConnectorID

    def commandInSourceRange(self, cmd):
        return True



class AOSource(Source):
    def __init__(self, handler, name, vMin, vMax, prec, physConID):
        super().__init__(handler, name, physConID)
        self.sourceSettings['vMin'] = vMin
        self.sourceSettings['vMax'] = vMax
        self.sourceSettings['prec'] = prec

    def readyCheck(self, traceIn):
        if super().readyCheck(traceIn) is False:
            return
        trace = traceIn.copy()
        trace.append(self)

        for command in self.programmingPacket.Get_Commands():
            if(isinstance(command, (AnalogWaveformCommand, AnalogSparseCommand)) is False):
                trace[0].Fail_Ready_Check(trace, 'Analog Output Source Recieved Unknown Programming Packet Type! ' + command.__str__())
            else:
                if(self.commandInSourceRange(command) is False):
                    trace[0].Fail_Ready_Check(trace, 'Analog Output Source Programming Packet Out Of Source Range')

    def parsePacket(self, packetIn):
        self.programmingPacket = packetIn
        self.programmingPacket.physicalConnectorID = self.physicalConnectorID
            
    def commandInSourceRange(self, cmd):
        #if(cmd.waveformData is None):
        #    return True
        #yAxis = cmd.waveformData[:,1]
        #if(yAxis.max() > self.vMax):
        #    return False
        #if(yAxis.min() < self.vMin):
        #    return False

        return True



class DISource(Source):
    def __init__(self, handler, name, physConID, trigger=False):
        super().__init__(handler, name, physConID, trigger=trigger)

    def readyCheck(self, traceIn):
        if super().readyCheck(traceIn) is False:
            return
        trace = traceIn.copy()
        trace.append(self)
        super().readyCheck(traceIn)

        for command in self.programmingPacket.Get_Commands():
            if(isinstance(command, DigitalAcquisitionCommand) is False):
                trace[0].Fail_Ready_Check(trace, 'Digital Input Source Recieved Unknown Programming Packet Type! ' + command.__str__())
            else:
                if(self.commandInSourceRange(command) is False):
                    trace[0].Fail_Ready_Check(trace, 'Digital Input Source Programming Packet Out Of Source Range')

    def parsePacket(self, packetIn):
        self.programmingPacket = packetIn
        self.programmingPacket.physicalConnectorID = self.physicalConnectorID

    def commandInSourceRange(self, cmd):
        return True



class DOSource(Source):
    def __init__(self, handler, name, physConID):
        super().__init__(handler, name, physConID)

    def readyCheck(self, traceIn):
        if super().readyCheck(traceIn) is False:
            return
        trace = traceIn.copy()
        trace.append(self)

        for command in self.programmingPacket.Get_Commands():
            if(isinstance(command, (DigitalWaveformCommand, DigitalSparseCommand)) is False):
                trace[0].Fail_Ready_Check(trace, 'Digital Output Source Recieved Unknown Programming Packet Type! ' + command.__str__())
            else:
                if(self.commandInSourceRange(command) is False):
                    trace[0].Fail_Ready_Check(trace, 'Digital Output Source Programming Packet Out Of Source Range')

    def parsePacket(self, packetIn):
        self.programmingPacket = packetIn
        self.programmingPacket.physicalConnectorID = self.physicalConnectorID

    def commandInSourceRange(self, cmd):
        return True