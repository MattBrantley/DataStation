from PyQt5.Qt import *
import os, uuid
from Constants import DSConstants as DSConstants
import numpy as np
from Managers.InstrumentManager.Sockets import Socket
from DSWidgets.controlWidget import readyCheckPacket

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
        return self.filterSettings['filterInputSource']

    def Get_Type(self):
        return self.filterSettings['filterType']

############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, hM):
        self.filterSettings = dict()
        self.filterSettings['name'] = 'Unnamed ' + self.filterType
        self.filterSettings['uuid'] = str(uuid.uuid4())
        self.filterSettings['filterType'] = self.filterType
        self.filterSettings['filterIdentifier'] = self.filterIdentifier
        self.filterSettings['iconGraphicSrc'] = self.iconGraphicSrc
        self.filterSettings['filterInputSource'] = None

        self.iM = None
        self.mW = None #These are declared by the calling class
        self.hW = None

        paths = list()
        for i in range(self.numPaths):
            paths.append(None)
        self.filterSettings['paths'] = paths

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

        if(self.filterInputSource is None or self.filterInputPathNo is None):
            return readyCheckPacket('Filter', DSConstants.READY_CHECK_ERROR, msg='Filter Is Not Attached!')
        else:
            subs.append(self.filterInputSource.procReverseParent(self.filterInputPathNo, packetOut))
        
        #return readyCheckPacket('Filter', DSConstants.READY_CHECK_READY)
        return readyCheckPacket('Filter', DSConstants.READY_CHECK_READY, subs=subs)

    def procReverse(self, pathNo, packetIn, packetType): ### OVERRIDE ME!! ####
        return None

    def onCreationParent(self):
        self.hM.mW.postLog('Added Filter: ' + self.filterType, DSConstants.LOG_PRIORITY_MED)

        self.onCreation()

    def onCreation(self): ### OVERRIDE ME!! ####
        pass

##### Search Functions ######

    def getPathNumber(self, uuid):
        index = 1
        for path in self.filterSettings['paths']:
            if(path == uuid):
                return index
            index += 1

    def getSockets(self):
        sockets = list()
        for path in self.filterSettings['paths']:
            if(path is not None):
                if(issubclass(type(path), Socket) is True):
                    sockets.append(path)
                else:
                    result = path.getSockets()
                    if(result is not None):
                        for socket in result:
                            sockets.append(socket)
        return sockets

    def getSource(self):
        if(self.filterSettings['filterInputSource'] is not None):
            return self.filterSettings['filterInputSource'].getSource()
        else:
            self.mW.postLog('ERROR: Filter called during getSource that has no root parent!', DSConstants.LOG_PRIORITY_HIGH)
            return None #This is bad - Filter needs to be removed in this case.

##### Filter Manipulation Functions #####

    def savePacket(self):
        return self.filterSettings
        
    def loadPacket(self, loadPacket):
        if(isinstance(loadPacket, dict) is False):
            return #loadPacket is malformed - can't run
        
        for key, value in loadPacket.items():
            self.filterSettings[key] = value
        # restoreState is called directly by the instrumentManager

    def restoreState(self):
        newPaths = list()
        for path in self.filterSettings['paths']:
            if(path is None):
                newPaths.append(None) # This wasn't attached in this state, so just return None
            else:
                targetFilterOrSocket = self.hM.getFilterOrSourceByUUID(uuid) #Search for Filter
                if(targetFilterOrSocket is None):
                    targetFilterOrSocket = self.iM.getSocketByUUID(uuid) #If it's not a filter, search for a Socket
                if(targetFilterOrSocket is None):
                    self.mW.postLog('FILTER RESTORE ERROR: ' + self.filterSettings['name'] + ' (' + type(self).__name__ + ') Trying To Attach To Path Filter/Socket that does not exist!!!' , DSConstants.LOG_PRIORITY_MED)
                    newPaths.append(None)
                else:
                    newPaths.append(path)
                
        self.filterSettings['paths'] = newPaths

        targetFilterOrSource = self.hM.getFilterOrSourceByUUID(self.filterSettings['filterInputSource'])
        if(targetFilterOrSource is None):
            self.mW.postLog('FILTER RESTORE ERROR: ' + self.filterSettings['name'] + ' (' + type(self).__name__ + ') Trying To Attach To Input Filter/Source that does not exist!!!' , DSConstants.LOG_PRIORITY_MED)
            self.filterSettings['filterInputSource'] = None
            #This is bad - Filter needs to be removed in this case.

    def detatchPathOther(self, uuid):
        newPaths = list()
        found = False
        for path in self.filterSettings['paths']:
            if(path == uuid):
                newPaths.append(None)
                found = True
            else:
                newPaths.append(path)

        return found

    def reattachPath(self, uuid):
        for path in self.filterSettings['paths']:
            if(path == uuid):
                return True
            else:
                return False

    def attachPathOther(self, pathNo, uuid):
        self.filterSettings['paths'][pathNo-1] = uuid
        return True

    def attachPathSelf(self, pathNo, uuid):
        if(uuid is None):
            self.mW.postLog('FILTER ATTACH ERROR: ' + self.filterSettings['name'] + ' (' + type(self).__name__ + ') Trying To Attach To Path Filter/Socket that is NoneValue!!!' , DSConstants.LOG_PRIORITY_MED)
            self.filterSettings['paths'][pathNo-1] = None
            return False 

        targetFilterOrSocket = self.hM.getFilterOrSourceByUUID(uuid) #Search for Filter
        if(targetFilterOrSocket is None):
            targetFilterOrSocket = self.iM.getSocketByUUID(uuid) #If it's not a filter, search for a Socket
        if(targetFilterOrSocket is None):
            self.mW.postLog('FILTER ATTACH ERROR: ' + self.filterSettings['name'] + ' (' + type(self).__name__ + ') Trying To Attach To Path Filter/Socket that does not exist!!!' , DSConstants.LOG_PRIORITY_MED)
            self.filterSettings['paths'][pathNo-1] = None
            return False
        
        self.filterSettings['paths'][pathNo-1] = uuid
        return True
            
class AnalogFilter(Filter):
    def __init__(self, hM, **kwargs):
        super().__init__(hM, **kwargs)

class DigitalFilter(Filter):
    def __init__(self, hM, **kwargs):
        super().__init__(hM, **kwargs)