from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math
from Constants import DSConstants as DSConstants
from Sockets import *
import uuid
from DSWidgets.controlWidget import readyCheckPacket
import numpy as np

class Source():
    name = "NULL"
    numPaths = 1

    def __init__(self, hardware):
        self.filterInputSource = None
        self.hardware = hardware
        self.paths = list()
        self.uuid = str(uuid.uuid4())
        self.physicalConnectorID = ''
        self.programData = None
        
    def addFilter(self, pathNo, filterIn):
        if(self.paths[pathNo-1] is not None):
            if(issubclass(type(self.paths[pathNo-1]), Socket)):
                self.paths[pathNo-1].unattach()

        filterIn.filterInputSource = self
        filterIn.filterInputPathNo = pathNo
        self.paths[pathNo-1] = filterIn
    
    def procReverseParent(self, pathNo, packetIn):
        #Source got the packet!
        return self.parsePacket(packetIn)

    def parsePacket(self, packetIn):
        return readyCheckPacket('Source', DSConstants.READY_CHECK_ERROR, msg='Critical Source Error! Default Source Object Used Somewhere!')

    def attachSocket(self, pathNo, socketIn):
        socketIn.filterInputSource = self
        socketIn.filterInputPathNo = pathNo
        self.paths[pathNo-1] = socketIn

    def unattach(self, pathNo):
        self.paths[pathNo-1] = None

    def detachSockets(self):
        if(self.paths[0] is not None):
            if(issubclass(type(self.paths[0]), Socket)):
                self.paths[0].unattach()
            self.paths[0] = None

    def getSource(self):
        return self

    def onSave(self):
        pass

    def onLoad(self, loadPacket):
        pass
        #self.filterInputSource =

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

    def pathListUUIDs(self):
        pathList = list()
        for path in self.paths:
            if(path is None):
                pathList.append(None)
            else:
                pathList.append(path.uuid)

    def reattachSocket(self, socketIn, pathNo):
        if(self.paths[pathNo-1] is not None):
            return None
        else:
            self.paths[pathNo-1] = socketIn
            return self

    def onLink(self):
        if('filterInputSource' in self.loadPacket):
            if(self.loadPacket['filterInputSource'] is not None):
                self.filterInputSource = self.hardware.hardwareManager.objFromUUID(self.loadPacket['filterInputSource'])
            else:
                self.filterInputSource = None

    def readyCheck(self):
        drivingSocketCount = 0
        for socket in self.getSockets():
            if(socket.drivingSocket == True):
                drivingSocketCount = drivingSocketCount + 1

        if(drivingSocketCount > 1):
            #self.hardware.hardwareManager.workspace.mainWindow.postLog('READY CHECK FAILED: Socket has more than one driving source!', DSConstants.LOG_PRIORITY_HIGH)
            #self.hardware.hardwareManager.workspace.mainWindow.controlWidget.addReadyCheckMessage('READY CHECK FAILED: Active Socket Has No Source!')
            return readyCheckPacket('Socket', DSConstants.READY_CHECK_ERROR, msg='Source Has More Than One Driving Socket!')

        return readyCheckPacket('Socket', DSConstants.READY_CHECK_READY)

    def onRemove(self):
        for socket in self.getSockets():
            socket.unattach()

        self.filterInputSource = None

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

    def getProgramData(self):
        if(len(self.getSockets()) > 0): #Might have left over program data but not needed if no sockets attached!
            if(self.programData is not None):
                return self.programData

class DCSource(Source):
    def __init__(self, hardware, name, vMin, vMax, prec, physConID):
        super().__init__(hardware)
        self.hardware = hardware
        self.name = name
        self.vMin = vMin
        self.vMax = vMax
        self.prec = prec
        self.paths.clear()
        self.paths.append(None)
        self.loadPacket = None
        self.physicalConnectorID = physConID

    def parsePacket(self, packetIn):
        if(isinstance(packetIn, DCWaveformPacket) is False):
            return readyCheckPacket('DC Source', DSConstants.READY_CHECK_ERROR, msg='DC Source Recieved Unknown Packet Type!')
        
        if(self.packetInSourceRange(packetIn) is False):
            return readyCheckPacket('DC Source', DSConstants.READY_CHECK_ERROR, msg='DC Waveform Out Of Range!')

        self.programData = packetIn
        self.programData.physicalConnectorID = self.physicalConnectorID
        return readyCheckPacket('DC Source', DSConstants.READY_CHECK_READY)
            
    def packetInSourceRange(self, packetIn):
        if(packetIn.waveformData is None):
            return True
        yAxis = packetIn.waveformData[:,1]
        if(yAxis.max() > self.vMax):
            return False
        if(yAxis.min() < self.vMin):
            return False

        return True

    def onSave(self):
        savePacket = dict()
        savePacket['name'] = self.name
        savePacket['uuid'] = self.uuid
        savePacket['vMin'] = self.vMin
        savePacket['vMax'] = self.vMax
        savePacket['prec'] = self.prec
        savePacket['physConID'] = self.physicalConnectorID
        savePacket['paths'] = self.savePaths()

        return savePacket

    def onLoad(self, loadPacket):
        self.loadPacket = loadPacket
        #if('name' in loadPacket):
        #    self.name = loadPacket['name']
        if('uuid' in loadPacket):
            self.uuid = loadPacket['uuid']
        #if('vMin' in loadPacket):
        #    self.vMin = loadPacket['vMin']
        #if('vMax' in loadPacket):
        #    self.vMax = loadPacket['vMax']
        #if('prec' in loadPacket):
        #    self.prec = loadPacket['prec']
        if('physConID' in loadPacket):
            self.physicalConnectorID = loadPacket['physConID']

        if('paths' in loadPacket):
            for path in loadPacket['paths']:
                if('pathNo' in path and 'data' in path):
                    if(path['data'] is not None and path['pathNo'] is not None):
                        self.paths[path['pathNo']-1] = self.hardware.hardwareManager.loadFilterFromData(self, path['data'], path['pathNo'])

class DIOSource(Source):
    def __init__(self, hardware, name, physConID):
        super().__init__(hardware)
        self.hardware = hardware
        self.name = name
        self.physicalConnectorID = physConID

    def onSave(self):
        savePacket = dict()
        savePacket['name'] = self.name
        savePacket['uuid'] = self.uuid
        savePacket['physConID'] = self.physicalConnectorID
        savePacket['paths'] = self.savePaths()

        return savePacket

    def onLoad(self, loadPacket):
        self.loadPacket = loadPacket
        if('name' in loadPacket):
            self.name = loadPacket['name']
        if('uuid' in loadPacket):
            self.uuid = loadPacket['uuid']
        if('physConID' in loadPacket):
            self.physicalConnectorID = loadPacket['physConID']

        if('paths' in loadPacket):
            for path in loadPacket['paths']:
                if('pathNo' in path and 'data' in path):
                    if(path['data'] is not None and path['pathNo'] is not None):
                        self.paths[path['pathNo']-1] = self.hardware.hardwareManager.loadFilterFromData(self, path['data'], path['pathNo'])