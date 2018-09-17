from PyQt5.Qt import *
from PyQt5.QtGui import QStandardItemModel
import os, random, uuid, numpy as np
from decimal import Decimal
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
    mW = None
    valid = False
    isTriggerComponent = False

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

    def Get_Sockets(self):
        return self.socketList

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
        self.name = kwargs.get('name', self.componentType)
        self.socketList = list()
        self.pathDataPackets = list()
        self.pathDataPackets.append(None)
        self.sequencerEditWidget = None
        self.eventTypeList = list()
        self.eventList = list()
        self.data = None
        self.plotItem = None
        self.sequencerDrawState = False

##### Datastation Reserved Functions #####

    def readyCheck(self):
        subs = list()
        goodToContinue = True
        for socket in self.socketList:
            newSub = socket.readyCheck()
            subs.append(newSub)
            if(newSub.readyStatus == DSConstants.READY_CHECK_ERROR):
                goodToContinue = False
        
        if(goodToContinue is True):
            if(self.sequencerEditWidget is not None):
                runResults = self.onRun(self.sequencerEditWidget.getEvents())
            else:
                return readyCheckPacket('User Component [' + self.compSettings['name'] + ']', DSConstants.READY_CHECK_ERROR, subs=subs, msg='User Component Does Not Have SequencerEditWidget!!')
            if(isinstance(runResults, readyCheckPacket)):
                subs.append(runResults)
                if(runResults.readyStatus == DSConstants.READY_CHECK_ERROR):
                    goodToContinue = False
            else:
                if(runResults is not True):
                    subs.append(readyCheckPacket('User Component [' + self.compSettings['name'] + ']', DSConstants.READY_CHECK_ERROR, msg='User Component onRun() Did Not Return readyCheckPacket or True!'))
                    goodToContinue = False
        
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
        self.sequencerEditWidget = sequenceEditWidget(self.mW, self)
        self.onCreation()

    def onCreation(self): ### OVERRIDE ME!! ####
        pass

    def onCreationFinishedParent(self):
        #Walks through all appropriate objects and adds the update call.
        for widget in self.configWidget.findChildren(QLineEdit):
            widget.textChanged.connect(self.updatePlot)

        for widget in self.configWidget.findChildren(QCheckBox):
            widget.stateChanged.connect(self.updatePlot)

        for widget in self.configWidget.findChildren(QDoubleSpinBox):
            widget.valueChanged.connect(self.updatePlot)

        self.onCreationFinished()

    def onCreationFinished(self): ### OVERRIDE ME!! ####
        pass

    def onRemovalParent(self):
        self.mW.postLog('Removing Instrument Component: ' + self.componentType, DSConstants.LOG_PRIORITY_MED)
        for socket in self.socketList:
            socket.detatchInputSelf()
        self.onRemoval()

    def onRemoval(self):  ### OVERRIDE ME!! ####
        pass

    def parentPlotSequencer(self):
        if(self.sequencerEditWidget is not None):
            return self.plotSequencer(self.sequencerEditWidget.getEvents())

    def plotSequencer(self, events): ### OVERRIDE ME!! ####
        return np.array([0,0])

    def onRunParent(self, events):
        self.onRun(events)

    def onRun(self, events):  ### OVERRIDE ME!! ####
        return readyCheckPacket('Component', DSConstants.READY_CHECK_ERROR, msg='User Component Does Not Override onRun()!')

##### Component Modifications ######

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
        self.sequenceEditWidget = ComponentSequenceEditWidget(self)

##### Event Type Modifications #####

    def addEventType(self, eventType):
        self.eventTypeList.append(eventType)


##### Event Modifications #####

    def clearEvents(self):
        if(self.sequencerEditWidget is not None):
            self.sequencerEditWidget.clearEvents()

    def addEvent(self, event):
        self.eventList.append(event)
        self.iM.eventAdded(self, event)

    def removeEvent(self, event):
        self.iM.eventRemoved(self, event)
        self.eventList.remove(event)

    def loadSequenceData(self, events):
        for event in events:
            self.addEvent(event)

        #if(self.sequencerEditWidget is None): #Generates this widget the first time it is made.
        #    self.sequencerEditWidget = sequenceEditWidget(self.mW, self)

            #self.sequencerEditWidget.addEvent(event)
        #self.sequencerEditWidget.checkEventOverlaps()

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

##### Hardware Widget Interactions #####

    def registeriViewComponent(self, component):
        self.iViewComponent = component

    def ROIRemove(self, eventPos):
        self.iM.currentInstrument.removeComponent(self)

##### Sequence Editor Widget #####

    def onSequencerDoubleClick(self, eventPos):
        self.sequencerEditWidget.move(eventPos + QPoint(2, 2))
        if(self.sequencerEditWidget.isHidden()):
            self.sequencerEditWidget.updateTitle()
            self.sequencerEditWidget.show()
        else:
            self.sequencerEditWidget.hide()

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

