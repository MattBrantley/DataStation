from PyQt5.Qt import *
import os, uuid
from src.Constants import DSConstants as DSConstants, readyCheckPacket
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

    def Get_Sockets(self):
        return self.getSockets()

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
        self.mW = None # These are defined by hardwareManager immediately after generation
        self.hM = None # These are defined by hardwareManager immediately after generation
        self.hW = None # These are defined by hardwareManager immediately after generation

##### DataStation Interface Functions #####

    def getUUID(self):
        return self.filterSettings['uuid']

##### Functions Over-Ridden By Factoried Components #####

    def procForwardParent(self, packetIn):
        packetType = self.getPacketType(packetIn)

        if(packetType is None):
            #Incoming packet is an unknown type
            return None

        packetOut = self.procForward(packetIn, packetType)
        if(packetOut is None):
            packetOut = packetIn
        
        return packetOut

    def procForward(self, inputs): ### OVERRIDE ME!! ####
        return None

    def procReverseParent(self, packetIn):
        subs = list()
        packetType = self.getPacketType(packetIn)

        if(packetType is None):
            #Incoming packet is an unknown type
            return readyCheckPacket('Filter', DSConstants.READY_CHECK_ERROR, msg='Unknown Packet Type Transferred!')

        packetOut = self.procReverse(pathNo, packetIn, packetType)
        if(packetOut is None):
            packetOut = packetIn

        if(self.filterSettings['inputSource'] is None or self.filterSettings['inputSourcePathNo'] is None):
            return readyCheckPacket('Filter', DSConstants.READY_CHECK_ERROR, msg='Filter Is Not Attached!')
        else:
            subs.append(self.filterSettings['inputSource'].procReverseParent(self.filterInputPathNo, packetOut))
        
        #return readyCheckPacket('Filter', DSConstants.READY_CHECK_READY)
        return readyCheckPacket('Filter', DSConstants.READY_CHECK_READY, subs=subs)

    def procReverse(self, pathNo, packetIn, packetType): ### OVERRIDE ME!! ####
        return None

    def onCreationParent(self):
        self.onCreation()

    def onCreation(self): ### OVERRIDE ME!! ####
        pass

##### Search Functions ######

    def getSockets(self):
        if(self.iM.Get_Instrument() is None):
            return list()
        outputFilters = self.hM.Get_Filters(inputUUID = self.filterSettings['uuid'])
        outputSockets = self.iM.Get_Instrument().Get_Sockets(inputUUID = self.filterSettings['uuid'])

        for Filter in outputFilters:
            outputSockets += Filter.Get_Sockets()

        return outputSockets

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

        self.restoreState()

    def restoreState(self):
        if(self.filterSettings['inputSource'] is None):
            self.filterSettings['inputSourcePathNo'] = None
            return # Previous filter state was not connected to anything
        if(self.filterSettings['inputSourcePathNo'] is None):
            self.filterSettings['inputSource'] = None
            return # Previous filter state was not connected to anything; even if it was, we don't know to what path.

        target = self.hM.Get_Sources(uuid=self.filterSettings['inputSource'])
        if(len(target) == 0):
            target = self.hM.Get_Filters(uuid=self.filterSettings['inputSource'])

        if(len(target) == 0):
            self.filterSettings['inputSource'] = None
            self.filterSettings['inputSourcePathNo'] = None
            self.mW.postLog('FILTER RESTORE ERROR: ' + self.filterSettings['name'] + ' (' + type(self).__name__ + ') Trying To Attach To Filter/Source that does not exist!!!' , DSConstants.LOG_PRIORITY_MED)
            return # No Filter or Source found at that uuid - clear this filter's reference.

    def attachInput(self, uuid, pathNumber):

        # Remove anything else that has a connection to what this is connecting to
        filtersAttached = self.hM.Get_Filters(inputUUID = uuid, pathNo=pathNumber)
        for Filter in filtersAttached:
            Filter.Detatch_Input()
        if(self.iM.Get_Instrument() is not None):
            socketsAttached = self.iM.Get_Instrument().Get_Sockets(inputUUID = uuid, pathNo=pathNumber)
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
        outputSockets = self.iM.Get_Instrument().Get_Sockets(inputUUID = self.filterSettings['uuid'])
        for Socket in outputSockets:
            Socket.Detatch_Input()
        self.hM.removeFilter(self)

class AnalogFilter(Filter):
    def __init__(self, hM, **kwargs):
        super().__init__(hM, **kwargs)

class DigitalFilter(Filter):
    def __init__(self, hM, **kwargs):
        super().__init__(hM, **kwargs)