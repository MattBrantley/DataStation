from PyQt5.Qt import *
import os, uuid
from Constants import DSConstants as DSConstants
import numpy as np
from Sockets import *
from DSWidgets.controlWidget import readyCheckPacket

class Filter():
    filterType = 'Default Filter'
    filterIdentifier = 'DefFil'
    filterVersion = '1.0'
    filterCreator = 'Matthew R. Brantley'
    filterVersionDate = '8/13/2018'
    iconGraphicSrc = 'default.png'
    numPaths = 1
    mainWindow = None
    valid = False

    FILTER_FORWARD = 100
    FILTER_REVERSE = 101
    FILTER_PACKET_DC_WAVEFORM = 200
    FILTER_PACKET_DIO_WAVEFORM = 201

    def __init__(self, hardwareManager, **kwargs):
        self.filterSettings = dict()
        self.paths = list()
        self.filterSettings['name'] = ''
        self.hardwareManager = hardwareManager
        self.name = kwargs.get('name', self.filterType)
        self.filterObject = None
        self.filterInputSource = None
        self.filterInputPathNo = None
        self.uuid = str(uuid.uuid4())

    def getPacketType(self, packetIn):
        if(packetIn is None):
            return None
        if(issubclass(type(packetIn), DCWaveformPacket)):
            return self.FILTER_PACKET_DC_WAVEFORM
        if(issubclass(type(packetIn), DIOWaveformPacket)):
            return self.FILTER_PACKET_DIO_WAVEFORM
        
        return None

    def isDCWaveformPacket(self, packetIn):
        if(self.getPacketType(packetIn) == self.FILTER_PACKET_DC_WAVEFORM):
            return True
        else:
            return False

    def isDIOWaveformPacket(self, packetIn):
        if(self.getPacketType(packetIn) == self.FILTER_PACKET_DIO_WAVEFORM):
            return True
        else:
            return False

    def procForwardParent(self, packetIn):
        packetType = self.getPacketType(packetIn)

        if(packetType is None):
            #Incoming packet is an unknown type
            return None

        packetOut = self.procForward(packetIn, packetType)
        if(packetOut is None):
            packetOut = packetIn
        
        return packetOut

    def procForward(self, inputs):
        return None

    def procReverseParent(self, pathNo, packetIn):
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

    def procReverse(self, pathNo, packetIn, packetType):
        return None

    def onCreationParent(self):
        self.hardwareManager.mainWindow.postLog('Added Filter: ' + self.filterType, DSConstants.LOG_PRIORITY_MED)
        self.paths.clear()
        for i in range(0, self.numPaths):
            self.paths.append(None)

        self.onCreation()

    def onCreation(self):
        pass

    def walkPathsForDraw(self, curColumn, view, branchRoot):
        tempColumn, filterObject = view.addFilterObject(self, branchRoot, curColumn)

        self.filterObject = filterObject

        newRoot = False
        for path in self.paths:
            if(path is not None):
                if(path.filterInputSource == self):
                    path.walkPathsForDraw(tempColumn, view, newRoot)
            newRoot = True

    def unattach(self, pathNo):
        self.paths[pathNo-1] = None

    def callRemove(self):
        for path in self.paths:
            if(path is not None):
                path.callRemove()

        self.filterInputSource.unattach(self.filterInputPathNo)
    
    def addFilter(self, pathNo, filterIn):
        if(self.paths[pathNo-1] is not None):
            if(issubclass(type(self.paths[pathNo-1]), Socket)):
                self.paths[pathNo-1].unattach()

        filterIn.filterInputSource = self
        filterIn.filterInputPathNo = pathNo
        self.paths[pathNo-1] = filterIn

    def attachSocket(self, pathNo, socketIn):
        socketIn.filterInputSource = self
        socketIn.filterInputPathNo = pathNo
        self.paths[pathNo-1] = socketIn

    def reattachSocket(self, socketIn, pathNo):
        if(self.paths[pathNo-1] is not None):
            return None
        else:
            self.paths[pathNo-1] = socketIn
            return self

    def savePaths(self):
        pathSaveData = list()
        index = 1
        for path in self.paths:
            pathData = dict()
            pathData['pathNo'] = index
            if(path is None):
                pathData['data'] = None
            else:
                pathData['data'] = path.onSave()
            
            pathSaveData.append(pathData)
            index = index + 1
        
        return pathSaveData

    def onSave(self):
        savePacket = dict()
        savePacket['filterSettings'] = self.filterSettings
        savePacket['filterType'] = self.filterType
        savePacket['filterIdentifier'] = self.filterIdentifier
        savePacket['uuid'] = self.uuid
        savePacket['name'] = self.name
        savePacket['paths'] = self.savePaths()

        return savePacket    
        
    def onLoad(self, loadPacket):
        self.loadPacket = loadPacket
        if('name' in loadPacket):
            self.name = loadPacket['name']
        if('uuid' in loadPacket):
            self.uuid = loadPacket['uuid']
        if('filterSettings' in loadPacket):
            self.filterSettings = loadPacket['filterSettings']

        loadPaths = 1
        if('paths' in loadPacket):
            for path in loadPacket['paths']:
                if(loadPaths > self.numPaths):
                    return
                loadPaths = loadPaths + 1
                if('pathNo' in path and 'data' in path):
                    if(path['data'] is not None and path['pathNo'] is not None):
                        self.paths[path['pathNo']-1] = self.hardwareManager.loadFilterFromData(self, path['data'], path['pathNo'])

    def getSockets(self):
        sockets = list()
        for path in self.paths:
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
        if(self.filterInputSource is not None):
            return self.filterInputSource.getSource()
        else:
            self.hardwareManager.mainWindow.postLog('ERROR: Filter called during getSource that has no root parent!', DSConstants.LOG_PRIORITY_HIGHT)
            return None

    def followPath(self, pathNumber):
        if(pathNumber > len(self.paths) or pathNumber <= 0):
            return
        
        if(self.paths[pathNumber] is not None):
            pass
        else:
            return