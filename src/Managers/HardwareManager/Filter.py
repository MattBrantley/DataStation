from PyQt5.Qt import *
import os, uuid
from src.Constants import DSConstants as DSConstants
import numpy as np
from src.Managers.InstrumentManager.Sockets import Socket
from src.Managers.HardwareManager.Sources import Source

class Filter():
    filterType = 'Default Filter'
    filterIdentifier = 'DefFil'
    filterVersion = '1.0'
    filterCreator = 'Matthew R. Brantley'
    filterVersionDate = '8/13/2018'
    iconGraphicSrc = 'default.png'
    numPaths = 1
    valid = False

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Get_Name(self):
        return self.filterSettings['name']

    def Get_Source(self):
        return self.getSource()

    def Get_Socket(self):
        return self.getSocket()

    def Get_UUID(self):
        return self.filterSettings['uuid']

    def Get_Input_UUID(self):
        return self.filterSettings['inputSource']

    def Get_Input_Path_Number(self):
        return self.filterSettings['inputSourcePathNo']

    def Get_Number_Of_Paths(self):
        return self.numPaths

    def Attach_Input(self, uuid, pathNo):
        return self.attachInput(uuid, pathNo)

    def Detatch_Input(self):
        self.detatch()

    def Get_Type(self):
        return self.filterSettings['filterType']

    def Remove(self):
        self.removeFilter()

############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, hM):
        self.filterSettings = dict()
        self.filterSettings['name'] = 'Unnamed ' + self.filterType
        self.filterSettings['uuid'] = str(uuid.uuid4())
        self.filterSettings['filterType'] = self.filterType
        self.filterSettings['filterIdentifier'] = self.filterIdentifier
        self.filterSettings['iconGraphicSrc'] = self.iconGraphicSrc
        self.filterSettings['inputSource'] = None
        self.filterSettings['inputSourcePathNo'] = None

        self.iM = None # These are defined by hardwareManager immediately after generation
        self.ds = None # These are defined by hardwareManager immediately after generation
        self.hM = None # These are defined by hardwareManager immediately after generation
        self.hW = None # These are defined by hardwareManager immediately after generation

##### DataStation Interface Functions #####

    def getUUID(self):
        return self.filterSettings['uuid']

    def readyCheck(self, traceIn):
        trace = traceIn.copy()
        trace.append(self)

        if self.getInputObject() is not None:
            self.getInputObject().readyCheck(trace)

    def getInputObject(self):
        if(self.filterSettings['inputSource'] is None or self.filterSettings['inputSourcePathNo'] is None):
            return None
        else:
            inputObj = self.hM.Get_Filters(uuid=self.filterSettings['inputSource'])
            if not inputObj:
                inputObj = self.hM.Get_Sources(uuid=self.filterSettings['inputSource'])
            if not inputObj:
                return None
        return inputObj[0]

    def getProgrammingPacket(self, programmingPacket):
        programmingPacket = self.procForwardParent(programmingPacket)
        self.Get_Source().getProgrammingPacket(programmingPacket)

    def getMeasurementPacket(self, measurementPacket):
        measurementPacket = self.procReverseParent(measurementPacket)
        socket = self.Get_Socket()
        if(socket):
            socket.getMeasurementPacket(measurementPacket)

##### Functions Over-Ridden By Factoried Filters #####

    def procForwardParent(self, programmingPacket):
        packetOut = self.procForward(programmingPacket)
        if(packetOut is None):
            packetOut = packetIn
        
        return packetOut

    def procReverseParent(self, measurementPacket):
        packetOut = self.procReverse(measurementPacket)
        if(packetOut is None):
            packetOut = packetIn

        return packetOut

    def procForward(self, programmingPacket): ## OVERRIDE ME!! ##
        return None

    def procReverse(self, measurementPacket): ### OVERRIDE ME!! ####
        return None

    def onCreationParent(self):
        self.onCreation()

    def onCreation(self): ### OVERRIDE ME!! ####
        pass

##### Search Functions ######

    def getSocket(self):
        outputFilters = self.hM.Get_Filters(inputUUID = self.filterSettings['uuid'])
        if outputFilters:
            return outputFilters[0]

        for instrument in self.iM.Get_Instruments():
            outputSocket = instrument.Get_Sockets(inputUUID = self.filterSettings['uuid'])
            if outputSocket:
                return outputSocket[0]

        return None

        # for Filter in outputFilters:
        #     outputSockets += Filter.Get_Sockets()

        # return outputSockets

    def getSource(self):
        if(self.filterSettings['inputSource'] is None or self.filterSettings['inputSourcePathNo'] is None):
            return None
        else:
            inputObj = self.hM.Get_Filters(uuid=self.filterSettings['inputSource'])
            if not inputObj:
                inputObj = self.hM.Get_Sources(uuid=self.filterSettings['inputSource'])
            if not inputObj:
                return None
            if(issubclass(Source, type(inputObj[0])) is True):
                return inputObj[0]
            else:
                return inputObj[0].Get_Source()

##### Filter Manipulation Functions #####

    def savePacket(self):
        return self.filterSettings
        
    def loadPacket(self, loadPacket):
        if(isinstance(loadPacket, dict) is False):
            return #loadPacket is malformed - can't run
        
        for key, value in loadPacket.items():
            self.filterSettings[key] = value

        #self.restoreState()

    # def restoreState(self):
    #     if(self.filterSettings['inputSource'] is None):
    #         self.filterSettings['inputSourcePathNo'] = None
    #         return # Previous filter state was not connected to anything
    #     if(self.filterSettings['inputSourcePathNo'] is None):
    #         self.filterSettings['inputSource'] = None
    #         return # Previous filter state was not connected to anything; even if it was, we don't know to what path.

    #     print(self.filterSettings['inputSource'])
    #     target = self.hM.Get_Sources(uuid=self.filterSettings['inputSource'])
    #     if(len(target) == 0):
    #         target = self.hM.Get_Filters(uuid=self.filterSettings['inputSource'])

    #     if(len(target) == 0):
    #         self.filterSettings['inputSource'] = None
    #         self.filterSettings['inputSourcePathNo'] = None
    #         self.ds.postLog('FILTER RESTORE ERROR: ' + self.filterSettings['name'] + ' (' + type(self).__name__ + ') Trying To Attach To Filter/Source that does not exist!!!' , DSConstants.LOG_PRIORITY_MED)
    #         return # No Filter or Source found at that uuid - clear this filter's reference.

    def attachInput(self, uuid, pathNumber):

        # Remove anything else that has a connection to what this is connecting to
        filtersAttached = self.hM.Get_Filters(inputUUID = uuid, pathNo=pathNumber)
        for Filter in filtersAttached:
            Filter.Detatch_Input()
        for instrument in self.iM.Get_Instruments():
            socketsAttached = instrument.Get_Sockets(inputUUID = uuid, pathNo=pathNumber)
            for Socket in socketsAttached:
                Socket.Detatch_Input()

        self.filterSettings['inputSource'] = uuid
        self.filterSettings['inputSourcePathNo'] = pathNumber
        self.hM.filterAttached(self)
        return True

    def detatch(self):
        self.filterSettings['inputSource'] = None
        self.filterSettings['inputSourcePathNo'] = None
        self.hM.filterDetatched(self)

    def removeFilter(self):
        self.detatch()
        outputFilters = self.hM.Get_Filters(inputUUID = self.filterSettings['uuid'])
        for Filter in outputFilters:
            Filter.Remove()
        for insturment in self.iM.Get_Instruments():
            outputSockets = insturment.Get_Sockets(inputUUID = self.filterSettings['uuid'])
            for Socket in outputSockets:
                Socket.Detatch_Input()
        self.hM.removeFilter(self)

class AnalogFilter(Filter):
    def __init__(self, hM, **kwargs):
        super().__init__(hM, **kwargs)

class DigitalFilter(Filter):
    def __init__(self, hM, **kwargs):
        super().__init__(hM, **kwargs)