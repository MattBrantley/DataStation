from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import uuid
import os, sys, imp, math
from Constants import DSConstants as DSConstants
from DSWidgets.controlWidget import readyCheckPacket

class Socket(QObject):
    Socket_Attached = pyqtSignal(object)
    Socket_Unattached = pyqtSignal(object)

    name = "NULL"
    paths = list()

    def __init__(self, component):
        super().__init__()
        self.filterInputSource = None
        self.filterInputPathNo = None
        self.paths.clear()
        self.component = component
        self.instrumentManager = None
        self.uuid = str(uuid.uuid4())
        self.physicalConnectorID = ''
        self.drivingSocket = True
        self.waveFormData = None
        self.dirty = True
        self.originSocket = None
        self.loadPacket = None

    def unattach(self):
        if(self.filterInputSource is not None):
            self.onUnattach()            
            self.filterInputSource.unattach(self.filterInputPathNo) 
            self.filterInputSource = None
            self.filterInputPathNo = None
            if(self.instrumentManager is not None):
                self.instrumentManager.socketUnattached(self)
                
        if(self.loadPacket is not None):
            self.loadPacket['filterInputSource'] = None

    def walkPathsForDraw(self, curColumn, view, branchRoot):
        tempColumn, filterObject = view.addFilterObject(self, branchRoot, curColumn)
        self.filterObject = filterObject

        newRoot = False
        for path in self.paths:
            if(path is not None):
                path.walkPathsForDraw(tempColumn, view, newRoot)
            newRoot = True

    def onUnattach(self):
        self.Socket_Unattached.emit(self)
        if(self.component is not None):
            pass
            #print('unattached')

    def onAttach(self, attachedTo):
        self.Socket_Attached.emit(self)
        if(self.component is not None):
            pass
            #print('attached')

    def onSave(self):
        return self.onSaveChild()

    def onSaveChild(self):
        pass

    def onLoad(self):
        pass

    def callRemove(self):
        self.unattach()

    def getAttachedSource(self):
        if(self.filterInputSource is not None):
            return self.filterInputSource.getSource()
        else:
            return None

    def readyCheck(self):
        if(self.getAttachedSource() is not None):
            return readyCheckPacket('Socket [' + self.name + ']', DSConstants.READY_CHECK_READY)
        else:
            return readyCheckPacket('Socket [' + self.name + ']', DSConstants.READY_CHECK_ERROR, msg='Socket Has No Source!')

    def onDataToSourcesParent(self, packet):
        subs = list()
        if(self.getAttachedSource is None):
            return readyCheckPacket('Socket', DSConstants.READY_CHECK_ERROR, msg='Socket Has No Source!')
        if(self.dirty is False or self.drivingSocket is False):
            return readyCheckPacket('Socket', DSConstants.READY_CHECK_READY)

        subs.append(self.onDataToSources(packet))
        self.dirty = True #Will Experiment With THis Later

        return readyCheckPacket('Socket', DSConstants.READY_CHECK_READY, subs=subs)

    def onDataToSources(self, packet):
        if(self.filterInputSource is None or self.filterInputPathNo is None):
            return readyCheckPacket('Socket', DSConstants.READY_CHECK_ERROR, msg='Socket not attached!')

        subs = list()
        subs.append(self.filterInputSource.procReverseParent(self.filterInputPathNo, packet))
        return readyCheckPacket('Socket', DSConstants.READY_CHECK_READY, subs=subs)

    def onLink(self):
# --- Break glass in case of bug ---
        #import traceback
        #traceback.print_stack()
# ---                            ---
        if(self.loadPacket is not None):
            if('filterInputSource' in self.loadPacket):
                print(str(type(self)) + ': ' + str(self.loadPacket['filterInputSource']))
                if(self.loadPacket['filterInputSource'] is not None):
                    targetFilter = self.instrumentManager.mW.hardwareWidget.hardwareManager.objFromUUID(self.loadPacket['filterInputSource'])
                    print('--> ' + str(type(targetFilter)))
                    if(targetFilter is None): #Contigency incase objFromUUID fails
                        self.filterInputPathNo = None
                        self.filterInputSource = None
                    else:
                        self.filterInputPathNo = self.loadPacket['filterInputPathNo']
                        #print(type(targetFilter))
                        self.filterInputSource = targetFilter.reattachSocket(self, self.filterInputPathNo)
                        if(self.filterInputSource is None): #This happens if you try to attach to a filter/source on a path that is already occupied
                            self.filterInputPathNo = None
                            self.instrumentManager.mW.postLog('SOCKET ATTACHEMENT ERROR: ' + self.name + '(' + type(self).__name__ + ') Trying To Attach To Filter/Source Path That Is Occupied!!' , DSConstants.LOG_PRIORITY_MED)
                            self.callRemove()
                else:
                    self.filterInputPathNo = None
                    self.filterInputSource = None

class AOSocket(Socket):
    def __init__(self, component, name, vMin, vMax, prec):
        super().__init__(component)
        self.instrumentManager = self.component.instrumentManager
        self.name = name + ' [AO]'
        self.vMin = vMin
        self.vMax = vMax
        self.prec = prec
        self.paths.clear()

    def onSaveChild(self):
        savePacket = dict()
        savePacket['name'] = self.name
        savePacket['uuid'] = self.uuid
        savePacket['vMin'] = self.vMin
        savePacket['vMax'] = self.vMax
        savePacket['prec'] = self.prec
        if(self.filterInputSource is not None):
            savePacket['filterInputSource'] = self.filterInputSource.uuid
            savePacket['filterInputPathNo'] = self.filterInputPathNo
        else:
            savePacket['filterInputSource'] = None
            savePacket['filterInputPathNo'] = None

        return savePacket

    def onLoad(self, loadPacket):
        if(isinstance(loadPacket, dict)):
            self.loadPacket = loadPacket
            if('name' in loadPacket):
                self.name = loadPacket['name']
            if('uuid' in loadPacket):
                self.uuid = loadPacket['uuid']
            if('vMin' in loadPacket):
                self.vMin = loadPacket['vMin']
            if('vMax' in loadPacket):
                self.vMax = loadPacket['vMax']
            if('prec' in loadPacket):
                self.prec = loadPacket['prec']

class AISocket(Socket):
    def __init__(self, component, name, vMin, vMax, prec):
        super().__init__(component)
        self.instrumentManager = self.component.instrumentManager
        self.name = name + ' [AI]'
        self.vMin = vMin
        self.vMax = vMax
        self.prec = prec
        self.paths.clear()

    def onSaveChild(self):
        savePacket = dict()
        savePacket['name'] = self.name
        savePacket['uuid'] = self.uuid
        savePacket['vMin'] = self.vMin
        savePacket['vMax'] = self.vMax
        savePacket['prec'] = self.prec
        if(self.filterInputSource is not None):
            savePacket['filterInputSource'] = self.filterInputSource.uuid
            savePacket['filterInputPathNo'] = self.filterInputPathNo
        else:
            savePacket['filterInputSource'] = None
            savePacket['filterInputPathNo'] = None

        return savePacket

    def onLoad(self, loadPacket):
        if(isinstance(loadPacket, dict)):
            self.loadPacket = loadPacket
            if('name' in loadPacket):
                self.name = loadPacket['name']
            if('uuid' in loadPacket):
                self.uuid = loadPacket['uuid']
            if('vMin' in loadPacket):
                self.vMin = loadPacket['vMin']
            if('vMax' in loadPacket):
                self.vMax = loadPacket['vMax']
            if('prec' in loadPacket):
                self.prec = loadPacket['prec']

class DOSocket(Socket):
    def __init__(self, component, name):
        super().__init__(component)
        self.instrumentManager = self.component.instrumentManager
        self.name = name + ' [DIO]'
        self.paths.clear()

    def onSaveChild(self):
        savePacket = dict()
        savePacket['name'] = self.name
        savePacket['uuid'] = self.uuid
        if(self.filterInputSource is not None):
            savePacket['filterInputSource'] = self.filterInputSource.uuid
            savePacket['filterInputPathNo'] = self.filterInputPathNo
        else:
            savePacket['filterInputSource'] = None
            savePacket['filterInputPathNo'] = None

        return savePacket

    def onLoad(self, loadPacket):
        if(isinstance(loadPacket, dict)):
            self.loadPacket = loadPacket
            if('name' in loadPacket):
                self.name = loadPacket['name']
            if('uuid' in loadPacket):
                self.uuid = loadPacket['uuid']

class DISocket(Socket):
    def __init__(self, component, name):
        super().__init__(component)
        self.instrumentManager = self.component.instrumentManager
        self.name = name + ' [DIO]'
        self.paths.clear()

    def onSaveChild(self):
        savePacket = dict()
        savePacket['name'] = self.name
        savePacket['uuid'] = self.uuid
        if(self.filterInputSource is not None):
            savePacket['filterInputSource'] = self.filterInputSource.uuid
            savePacket['filterInputPathNo'] = self.filterInputPathNo
        else:
            savePacket['filterInputSource'] = None
            savePacket['filterInputPathNo'] = None

        return savePacket

    def onLoad(self, loadPacket):
        if(isinstance(loadPacket, dict)):
            self.loadPacket = loadPacket
            if('name' in loadPacket):
                self.name = loadPacket['name']
            if('uuid' in loadPacket):
                self.uuid = loadPacket['uuid']

class waveformPacket():
    def __init__(self, waveformData):
        self.waveformData = waveformData
        self.physicalConnectorID = ''

        self.waveformData = waveformData
        self.physicalConnectorID = ''