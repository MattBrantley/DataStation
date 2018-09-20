from PyQt5.Qt import *
from PyQt5.QtGui import QStandardItemModel
import os, random, uuid, numpy as np
from src.Constants import DSConstants as DSConstants, readyCheckPacket
from src.Managers.InstrumentManager.Sockets import *

class Component(QObject):
    indexMe = True
    componentType = 'Default Component'
    componentIdentifier = 'DefComp'
    componentVersion = '1.0'
    componentCreator = 'Matthew R. Brantley'
    componentVersionDate = '7/13/2018'
    iconGraphicSrc = 'default.png' # Not adjustable like layoutGraphicSrc is.

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Get_Standard_Field(self, field):
        if(field in self.compSettings):
            return self.compSettings[field]
        else:
            return None

    def Get_Custom_Field(self, field):
        if(field in self.compSettings['customFields']):
            return self.compSettings['customFields'][field]
        else:
            return None

    def Set_Custom_Field(self, field, data):
        self.compSettings['customFields'][field] = data
        return True

    def Remove_Component(self):
        self.instr.Remove_Component(self)

    def Get_Sockets(self):
        return self.socketList

    def Get_Event_Types(self):
        return self.eventTypeList

    def Add_Events(self, events):
        self.addEvents(events)
        return True

    def Remove_Events(self, events):
        self.removeEvents(events)
        return True

    def Combined_Add_Remove_Events(self, addEvents, removeEvents):
        self.combineAddRemoveEvents(addEvents, removeEvents)
        return True

    def Get_Data(self):
        return self.data

    def Get_Events(self):
        return self.eventList

    def Get_Instrument(self):
        return self.instr

############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, mW, **kwargs):
        super().__init__()
        self.allowOverlappingEvents = False
        self.compSettings = {}
        self.compSettings['name'] = ''
        self.compSettings['layoutGraphicSrc'] = self.iconGraphicSrc
        self.compSettings['uuid'] = str(uuid.uuid4())
        self.compSettings['triggerComp'] = False
        self.compSettings['customFields'] = dict()
        self.instr = None           #Factory does not write this. It's in the very next line in Instrument though.
        self.mW = mW                #Factory does not write this. It's in the very next line in Instrument though.
        self.iM = None              #Factory does not write this. It's in the very next line in Instrument though.
        self.valid = False
        self.isTriggerComponent = False
        self.name = kwargs.get('name', self.componentType)
        self.socketList = list()
        self.pathDataPackets = list()
        self.pathDataPackets.append(None)
        self.sequencerEditWidget = None
        self.eventTypeList = list()
        self.eventList = list()
        self.data = list()

##### Datastation Reserved Functions #####

    def readyCheck(self):
        subs = list()
        goodToContinue = True
        for socket in self.socketList:
            newSub = socket.readyCheck()
            subs.append(newSub)
            if(newSub.readyStatus == DSConstants.READY_CHECK_ERROR):
                goodToContinue = False
        
        #if(goodToContinue is True):
        #    if(isinstance(runResults, readyCheckPacket)):
        #        subs.append(runResults)
        #        if(runResults.readyStatus == DSConstants.READY_CHECK_ERROR):
        #            goodToContinue = False
        #    else:
        #        if(runResults is not True):
        #            subs.append(readyCheckPacket('User Component [' + self.compSettings['name'] + ']', DSConstants.READY_CHECK_ERROR, msg='User Component onRun() Did Not Return readyCheckPacket or True!'))
        #            goodToContinue = False
        
        if(goodToContinue is True):
            pass
            #index = 0
            #for socket in self.socketList:
            #    if(self.pathDataPackets[index] is not None):
            #        #if(self.pathDataPackets[index].waveformData is None):
            #        #    subs.append(readyCheckPacket('User Component', DSConstants.READY_CHECK_ERROR, msg='User Component onRun() populated and empty packet (no waveformData!)' + str(index+1) + '!'))
            #        #else:
            #        subs.append(socket.onDataToSourcesParent(self.pathDataPackets[index]))
            #    else:
            #        subs.append(readyCheckPacket('User Component [' + self.compSettings['name'] + ']', DSConstants.READY_CHECK_ERROR, msg='User Component onRun() Did Not Populate pathDataPackets for Path #' + str(index+1) + '!'))
            #    index = index + 1
    
        if(goodToContinue is True):
            return readyCheckPacket('Component', DSConstants.READY_CHECK_READY, subs=subs)
        else:
            return readyCheckPacket('Component', DSConstants.READY_CHECK_ERROR, subs=subs)

##### Functions Called By Factoried Sockets #####

    def socketAdded(self, socket):
        self.instr.socketAdded(self, socket)

    def socketAttached(self, socket):
        self.instr.socketAttached(socket, self)

    def socketDetatched(self, socket):
        self.instr.socketDetatched(socket, self)

##### Functions Over-Ridden By Factoried Components #####

    def onCreationParent(self):
        self.mW.postLog('Added New Component to Instrument: ' + self.componentType, DSConstants.LOG_PRIORITY_MED)
        self.onCreation()

    def onCreation(self): ### OVERRIDE ME!! ####
        pass

    def onCreationFinishedParent(self):
        #Walks through all appropriate objects and adds the update call.
        #for widget in self.configWidget.findChildren(QLineEdit):
        #    widget.textChanged.connect(self.updatePlot)

        #for widget in self.configWidget.findChildren(QCheckBox):
        #    widget.stateChanged.connect(self.updatePlot)

        #for widget in self.configWidget.findChildren(QDoubleSpinBox):
        #    widget.valueChanged.connect(self.updatePlot)

        self.onCreationFinished()

    def onCreationFinished(self): ### OVERRIDE ME!! ####
        pass

    def onRemovalParent(self):
        self.mW.postLog('Removing Instrument Component: ' + self.componentType, DSConstants.LOG_PRIORITY_MED)
        for socket in self.socketList:
            socket.Detatch_Input()
        self.onRemoval()

    def onRemoval(self):  ### OVERRIDE ME!! ####
        pass

    def onProgramParent(self):
        self.eventList.sort(key=lambda x: x.time)
        self.onProgram()
        self.pushProgramming()
        self.instr.programmingModified(self)

    def onRun(self):  ### OVERRIDE ME!! ####
        return readyCheckPacket('Component', DSConstants.READY_CHECK_ERROR, msg='User Component Does Not Override onRun()!')

##### Component Programming #####

    def pushProgramming(self):
        for socket in self.socketList:
            socket.pushProgramming()

##### Component Modifications #####

    def onSaveParent(self):
        savePacket = dict()
        savePacket['compSettings'] = self.compSettings
        savePacket['compType'] = self.componentType
        savePacket['compIdentifier'] = self.componentIdentifier
        savePacket['triggerComp'] = self.isTriggerComponent
        #if(hasattr(self, 'iViewComponent')):
        #    savePacket['iViewSettings'] = self.iViewComponent.onSave()
        savePacket['sockets'] = self.saveSockets()

        return savePacket

    def loadCompSettings(self, compSettings):
        if(compSettings is not None):
            for key, value in compSettings.items():
                self.compSettings[key] = value

    def setPathDataPacket(self, pathNo, packet):
        self.pathDataPackets[pathNo-1] = packet

    def setupWidgets(self):
        self.configWidget = ComponentConfigWidget(self)

##### Event Type Modifications #####

    def addEventType(self, eventType):
        self.eventTypeList.append(eventType)

##### Event Modifications #####

    def getEventStartEnd(self, row): ### UNCORRECTED FROM EVENTLISTWIDGET
        sequenceType = self.eventTypes[self.table.cellWidget(row, 2).stack.currentIndex()]
        params = self.table.cellWidget(row, 2).stack.currentWidget().paramList
        length = sequenceType.getLength(params)
        start = self.table.cellWidget(row, 0).value()
        end = start + length
        return start, end

    def checkEventOverlaps(self): ### UNCORRECTED FROM EVENTLISTWIDGET
        for row in range(0, self.table.rowCount()):
            start, end = self.getEventStartEnd(row)
            result = self.checkIfTimeIsValid(row, start, end)
            if(result is False):
                self.table.cellWidget(row, 0).setBackground(QColor(Qt.red))
                self.table.cellWidget(row, 0).valid = False
                #widget = self.table.verticalHeaderItem(row)
                #widget.setBackground(QColor(255, 0, 0))
                #self.table.setVerticalHeaderItem(row, widget)
                #self.table.verticalHeaderItem(row).setBackground(QBrush(Qt.red))
            else:
                self.table.cellWidget(row, 0).setBackground(QColor(Qt.white))
                self.table.cellWidget(row, 0).valid = True
                #self.table.verticalHeaderItem(row).setBackground(QBrush(Qt.white))
        
        self.comp.updatePlot()

    def checkIfTimeIsValid(self, index, startIn, endIn): ### UNCORRECTED FROM EVENTLISTWIDGET
        for row in range(0, self.table.rowCount()):
            if(row != index):
                start, end = self.getEventStartEnd(row)
                if(start > startIn and start < endIn):
                    return False
                if(end > startIn and start < endIn):
                    return False
                if(startIn > start and startIn < end):
                    return False
                if(endIn > start and endIn < end):
                    return False
        return True

    def clearEvents(self):
        for event in reversed(self.eventList):
            self.removeEvent(event)

    # At the moment, addEvents and removeEvents both force a recalculation. For
    # the sequencer widget, this means that a modify event (add and remove) will
    # force two updates. It's a minor performance loss. This can be bypassed by
    # calling combineAddRemoveEvents()
    def combineAddRemoveEvents(self, addEvents, removeEvents):
        for event in addEvents:
            self.eventList.append(event)
            self.instr.eventAdded(self, event)
        for event in removeEvents:
            self.instr.eventRemoved(self, event)
            self.eventList.remove(event)
        self.onProgramParent()

    def addEvents(self, events):
        if isinstance(events, (list,)):
            if(not events):
                return
            for event in events:
                self.eventList.append(event)
                self.instr.eventAdded(self, event)
            self.onProgramParent()
        else:
            self.eventList.append(event)
            self.instr.eventAdded(self, event)
            self.onProgramParent()

    def removeEvents(self, events):
        if isinstance(events, (list,)):
            for event in events:
                if(not events):
                    return
                self.instr.eventRemoved(self, event)
                self.eventList.remove(event)
            self.onProgramParent()
        else:
            self.instr.eventRemoved(self, event)
            self.eventList.remove(event)
            self.onProgramParent()

    def loadSequenceData(self, eventData):
        self.clearEvents()
        eventListIn = list()
        for datum in eventData:
            datumType = self.getEventTypeByName(datum)
            if(datumType is None):
                self.mW.postLog('Sequence File had an unknown event type (' + datum['type'] + ') for component type (' + self.componentType + ')... ', DSConstants.LOG_PRIORITY_HIGH)
                continue
            eventTemp = datumType()
            eventTemp.loadPacket(datum)
            eventListIn.append(eventTemp)

        self.addEvents(eventListIn)

    def saveEventsPacket(self):
        savePacket = dict()
        savePacket['compID'] = self.componentIdentifier
        savePacket['uuid'] = self.compSettings['uuid']
        savePacket['name'] = self.compSettings['name']
        savePacket['type'] = self.componentType
        eventData = list()
        for event in self.eventList:
            eventData.append(event.savePacket())
        savePacket['events'] = eventData
        return savePacket

    def getEventTypeByName(self, eventData):
        for eventType in self.eventTypeList:
            if(eventType.name == eventData['type']):
                return eventType
        return None

##### Socket Interactions #####

    def reprogramSourceTargets(self):
        for socket in self.socketList:
            source = socket.getSource()
            if(source is not None):
                source.reprogram()

    def addAOSocket(self, name):
        socket = AOSocket(self, name, 0, 10, 0.1)
        self.socketList.append(socket)
        self.socketAdded(socket)
        return socket

    def addAISocket(self, name):
        socket = AISocket(self, name, 0, 10, 0.1)
        self.socketList.append(socket)
        self.socketAdded(socket)
        return socket

    def addDOSocket(self, name):
        socket = DOSocket(self, name)
        self.socketList.append(socket)
        self.socketAdded(socket)
        return socket

    def addDISocket(self, name):
        socket = DISocket(self, name)
        self.socketList.append(socket)
        self.socketAdded(socket)
        return socket

    def saveSockets(self):
        sockets = list()
        for socket in self.socketList:
            sockets.append(socket.savePacket())
        return sockets

    def loadSockets(self, sockets):
        if(self.isTriggerComponent is True):
            self.genTriggerSocket()
        index = 0
        for socket in sockets:
            self.socketList[index].loadPacket(socket)

##### Config Widget #####

    def hideConfigWindow(self):
        self.configWidget.hide()

    def updateConfigContent(self):
        pass

    def onLeftClick(self, eventPos):
        self.configWidget.move(eventPos + QPoint(2, 2))
        if(self.configWidget.isHidden()):
            self.updateConfigContent()
            self.configWidget.show()
        else:
            self.configWidget.hide()

class ComponentConfigWidget(QDockWidget):
    doNotAutoPopulate = True

    def __init__(self, compParent):
        super().__init__('Config: ' + compParent.name)
        self.compParent = compParent
        self.setFeatures(QDockWidget.DockWidgetClosable)
        self.setFloating(True)
        self.hide()