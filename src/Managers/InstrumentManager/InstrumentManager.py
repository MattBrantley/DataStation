import os, sys, imp, time, inspect
from Managers.InstrumentManager.Instrument import *
from Constants import DSConstants as DSConstants
import json as json
from DSWidgets.controlWidget import readyCheckPacket

class InstrumentManager(QObject):
    Instrument_Modified = pyqtSignal(object)
    Instrument_Unloaded = pyqtSignal()
    Instrument_Loaded = pyqtSignal(object)
    Component_Modified = pyqtSignal(object)
    Events_Modified = pyqtSignal(object)

    instrumentWidget = None

    def __init__(self, mW):
        super().__init__()
        self.mW = mW
        self.instrumentDir = os.path.join(self.mW.rootDir, 'User Instruments')
        self.componentsDir = os.path.join(self.mW.rootDir, 'User Components')
        self.currentInstrument = None
        self.componentsAvailable = list()
        self.loadComponents()

        self.mW.DataStation_Closing.connect(self.unsavedChangesCheck)

    def unsavedChangesCheck(self):
        print('UNSAVED CHANGES TO INSTRUMENT')

    def loadComponents(self):
        self.mW.postLog('Loading User Components... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.componentsDir):
            for name in files:
                url = os.path.join(root, name)
                compHolder = self.loadComponentFromFile(url)
                if (compHolder != None):
                    self.componentsAvailable.append(compHolder)

        self.mW.postLog('Finished Loading User Components!', DSConstants.LOG_PRIORITY_HIGH)

    def loadComponentFromFile(self, filepath):
        class_inst = None
        expected_class = 'User_Component'
        py_mod = None
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        loaded = False

        if file_ext.lower() == '.py':
            self.mW.postLog('   Found Component Script: ' + filepath, DSConstants.LOG_PRIORITY_MED)
            py_mod = imp.load_source(mod_name, filepath)
        else:
            return

        #if (py_mod != None):
        #    if hasattr(py_mod, expected_class):  # verify that Component is a class in this file
        #        loaded = True
        #        class_temp = getattr(py_mod, expected_class)(filepath)
        #        if isinstance(class_temp, Component):  # verify that Component inherits the correct class
        #            class_inst = class_temp

        if (py_mod != None):
            if(hasattr(py_mod, mod_name) is True):
                class_temp = getattr(py_mod, mod_name)(filepath)
                if issubclass(type(class_temp), Component):
                    class_inst = class_temp
                    loaded = True

        if(loaded):
            class_inst.instrumentManager = self
            class_inst.setupWidgets()
            self.mW.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.mW.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

        return class_inst

    def getAvailableComponents(self):
        return self.componentsAvailable

    def newInstrument(self, name):
        self.currentInstrument = Instrument(self)
        self.currentInstrument.Instrument_Modified.connect(self.Instrument_Modified)
        self.currentInstrument.Component_Modified.connect(self.Component_Modified)
        self.currentInstrument.Events_Modified.connect(self.Events_Modified)
        self.currentInstrument.name = name
        print('Instrument_Modified.emit()')
        self.Instrument_Modified.emit()
        print('Instrument_Unloaded.emit()')
        self.Instrument_Unloaded.emit()

    def addCompToInstrument(self, dropIndex):
        if (self.currentInstrument is None):
            self.mW.postLog('No instrument is loaded - creating new one! ', DSConstants.LOG_PRIORITY_HIGH)
            self.currentInstrument = Instrument(self)
            self.currentInstrument.Instrument_Modified.connect(self.Instrument_Modified)
            self.currentInstrument.Component_Modified.connect(self.Component_Modified)
            self.currentInstrument.Events_Modified.connect(self.Events_Modified)

        comp = self.componentsAvailable[dropIndex]
        result = self.currentInstrument.addComponent(comp)
        self.mW.sequencerDockWidget.updatePlotList()
        self.mW.hardwareWidget.drawScene()
        return result

    def saveInstrument(self, url):
        if(self.currentInstrument is not None):
            self.mW.postLog('VI_Save', DSConstants.LOG_PRIORITY_HIGH, textKey=True)
            self.currentInstrument.name, ext = os.path.splitext(os.path.basename(url))
            saveData = self.currentInstrument.saveInstrument()
            self.writeInstrumentToFile(saveData, url)
            self.mW.postLog(' ...Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

        else:
            self.mW.postLog('VI_Save_No_VI', DSConstants.LOG_PRIORITY_HIGH, textKey=True)
            
        self.instrumentWidget.updateTitle()
        
    def readyCheck(self):
        subs = list()
        if(self.currentInstrument is not None):
            subs.append(self.currentInstrument.readyCheck())
        else:
            return readyCheckPacket('Instrument Manager', DSConstants.READY_CHECK_ERROR, msg='No Instrument Loaded!')

        return readyCheckPacket('Instrument Manager', DSConstants.READY_CHECK_READY, subs=subs)

    def loadInstrument(self, url):
        self.mW.postLog('Loading User Instrument (' + url + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.exists(url) is False):
            self.mW.postLog('Path (' + url + ') does not exist! Aborting! ', DSConstants.LOG_PRIORITY_HIGH)
            return

        with open(url, 'r') as file:
            try:
                instrumentData = json.load(file)        
                print('Instrument_Unloaded.emit()')
                self.Instrument_Unloaded.emit()
                if(isinstance(instrumentData, dict)):
                    if(self.processInstrumentData(instrumentData, url) is False):
                        self.mW.postLog('Corrupted instrument at (' + url + ') - aborting! ', DSConstants.LOG_PRIORITY_MED)
            except ValueError as e:
                self.mW.postLog('Corrupted instrument at (' + url + ') - aborting! ', DSConstants.LOG_PRIORITY_MED)
                return
        self.mW.postLog('Finished Loading User Instrument!', DSConstants.LOG_PRIORITY_HIGH)
        self.mW.workspaceManager.userProfile['instrumentURL'] = self.currentInstrument.url
        self.mW.sequencerDockWidget.updatePlotList()
        self.mW.hardwareWidget.drawScene()

        self.instrumentWidget.updateTitle()

        print('Instrument_Loaded.emit()')
        self.Instrument_Loaded.emit(self.currentInstrument)

    def processInstrumentData(self, instrumentData, url):
        self.tempInstrument = Instrument(self)
        self.tempInstrument.url = url
        if('name' in instrumentData):
            self.tempInstrument.name = instrumentData['name']
            self.mW.instrumentWidget.instrumentView.clearComps()
        else:
            return False

        if('compList' in instrumentData):
            for comp in instrumentData['compList']:
                if(('compIdentifier' in comp) and ('compType' in comp)):
                    modelComp = self.findCompModelByIdentifier(comp['compIdentifier'])
                    if(modelComp is None):
                        self.mW.postLog('Instrument contains component (' + comp['compType'] + ':' + comp['compIdentifier'] + ') that is not in the available component modules. Ignoring this component!', DSConstants.LOG_PRIORITY_MED)
                        break
                    else:
                        result = self.tempInstrument.addComponent(modelComp)
                        if('compSettings' in comp):
                            result.loadCompSettings(comp['compSettings'])
                        if('sockets' in comp):
                            if(isinstance(comp['sockets'], list)):
                                result.loadSockets(comp['sockets'])
                        if('iViewSettings' in comp):
                            ivs = comp['iViewSettings']
                            self.mW.instrumentWidget.instrumentView.addComp(result, ivs['x'], ivs['y'], ivs['r'])
                            
        self.clearCurrentInstrument()
        self.currentInstrument = self.tempInstrument
        self.currentInstrument.Instrument_Modified.connect(self.Instrument_Modified)
        self.currentInstrument.Component_Modified.connect(self.Component_Modified)
        self.currentInstrument.Events_Modified.connect(self.Events_Modified)
        self.currentInstrument.reattachSockets()

    def reattachSockets(self):
        if(self.currentInstrument is not None):
            self.currentInstrument.reattachSockets()

    def clearCurrentInstrument(self):
        if(self.currentInstrument is not None):
            for socket in self.currentInstrument.getSockets():
                socket.unattach()

            self.currentInstrument = None

    def findCompModelByIdentifier(self, identifier):
        for comp in self.componentsAvailable:
            if(comp.componentIdentifier == identifier):
                return comp
        return None

    def writeInstrumentToFile(self, saveData, url):
        if(url is None):
            instrumentSaveURL = os.path.join(self.instrumentDir, self.currentInstrument.name + '.dsinstrument')
        else:
            instrumentSaveURL = url

        self.currentInstrument.url = instrumentSaveURL

        if(os.path.exists(instrumentSaveURL)):
            os.remove(instrumentSaveURL)
        with open(instrumentSaveURL, 'w') as file:
            json.dump(saveData, file, sort_keys=True, indent=4)

    def socketUnattached(self, socket):
        self.mW.hardwareWidget.iScene.connectPlugsAndSockets()
