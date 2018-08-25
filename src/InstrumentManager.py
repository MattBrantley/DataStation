import os, sys, imp, time
from Instrument import *
from Constants import DSConstants as DSConstants
import json as json
from DSWidgets.controlWidget import readyCheckPacket

class InstrumentManager():
    instrumentsURL = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'User Instruments')
    componentsURL = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'User Components')
    instrumentWidget = None

    def __init__(self, workspace, instrumentsURL, componentsURL):
        self.workspace = workspace
        self.mainWindow = self.workspace.mainWindow
        self.currentInstrument = None
        self.componentsAvailable = list()
        self.loadComponents()

    def loadComponents(self):
        self.mainWindow.postLog('Loading User Components... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.componentsURL):
            for name in files:
                url = os.path.join(root, name)
                compHolder = self.loadComponentFromFile(url)
                if (compHolder != None):
                    self.componentsAvailable.append(compHolder)

        self.mainWindow.postLog('Finished Loading User Components!', DSConstants.LOG_PRIORITY_HIGH)

    def loadComponentFromFile(self, filepath):
        class_inst = None
        expected_class = 'User_Component'
        py_mod = None
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        loaded = False

        if file_ext.lower() == '.py':
            self.mainWindow.postLog('   Found Component Script: ' + filepath, DSConstants.LOG_PRIORITY_MED)
            py_mod = imp.load_source(mod_name, filepath)
        else:
            return

        if (py_mod != None):
            if hasattr(py_mod, expected_class):  # verify that Component is a class in this file
                loaded = True
                class_temp = getattr(py_mod, expected_class)(filepath)
                if isinstance(class_temp, Component):  # verify that Component inherits the correct class
                    class_inst = class_temp

        if(loaded):
            self.mainWindow.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.mainWindow.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

        class_inst.instrumentManager = self
        class_inst.setupWidgets()
        return class_inst

    def getAvailableComponents(self):
        return self.componentsAvailable

    def newInstrument(self, name):
        self.currentInstrument = Instrument(self)
        self.currentInstrument.name = name
        self.mainWindow.instrumentWidget.instrumentView.clearComps()

    def addCompToInstrument(self, dropIndex):
        if (self.currentInstrument is None):
            self.mainWindow.postLog('No instrument is loaded - creating new one! ', DSConstants.LOG_PRIORITY_HIGH)
            self.currentInstrument = Instrument(self)

        comp = self.componentsAvailable[dropIndex]
        result = self.currentInstrument.addComponent(comp)
        self.mainWindow.sequencerDockWidget.updatePlotList()
        self.mainWindow.hardwareWidget.drawScene()
        return result

    def saveInstrument(self, url):
        if(self.currentInstrument is not None):
            self.mainWindow.postLog('VI_Save', DSConstants.LOG_PRIORITY_HIGH, textKey=True)
            saveData = self.currentInstrument.saveInstrument()
            self.writeInstrumentToFile(saveData, url)
            self.mainWindow.postLog(' ...Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

        else:
            self.mainWindow.postLog('VI_Save_No_VI', DSConstants.LOG_PRIORITY_HIGH, textKey=True)
        
    def readyCheck(self):
        subs = list()
        if(self.currentInstrument is not None):
            subs.append(self.currentInstrument.readyCheck())

        return readyCheckPacket('Instrument Manager', DSConstants.READY_CHECK_READY, subs=subs)

    def loadInstrument(self, url):
        self.mainWindow.postLog('Loading User Instrument (' + url + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        with open(url, 'r') as file:
            try:
                instrumentData = json.load(file)
                if(isinstance(instrumentData, dict)):
                    if(self.processInstrumentData(instrumentData, url) is False):
                        self.mainWindow.postLog('Corrupted instrument at (' + url + ') - aborting! ', DSConstants.LOG_PRIORITY_MED)
            except ValueError as e:
                self.mainWindow.postLog('Corrupted instrument at (' + url + ') - aborting! ', DSConstants.LOG_PRIORITY_MED)
                return
        self.mainWindow.postLog('Finished Loading User Instrument!', DSConstants.LOG_PRIORITY_HIGH)
        self.workspace.userProfile['instrumentURL'] = self.currentInstrument.url
        self.mainWindow.sequencerDockWidget.updatePlotList()
        self.mainWindow.hardwareWidget.drawScene()

    def processInstrumentData(self, instrumentData, url):
        self.tempInstrument = Instrument(self)
        self.tempInstrument.url = url
        if('name' in instrumentData):
            self.tempInstrument.name = instrumentData['name']
            self.mainWindow.instrumentWidget.instrumentView.clearComps()
        else:
            return False

        if('compList' in instrumentData):
            for comp in instrumentData['compList']:
                if(('compIdentifier' in comp) and ('compType' in comp)):
                    modelComp = self.findCompModelByIdentifier(comp['compIdentifier'])
                    if(modelComp is None):
                        self.mainWindow.postLog('Instrument contains component (' + comp['compType'] + ':' + comp['compIdentifier'] + ') that is not in the available component modules. Ignoring this component!', DSConstants.LOG_PRIORITY_MED)
                        return
                    else:
                        result = self.tempInstrument.addComponent(modelComp)
                        if('compSettings' in comp):
                            result.loadCompSettings(comp['compSettings'])
                        if('sockets' in comp):
                            if(isinstance(comp['sockets'], list)):
                                result.loadSockets(comp['sockets'])
                        if('iViewSettings' in comp):
                            ivs = comp['iViewSettings']
                            self.mainWindow.instrumentWidget.instrumentView.addComp(result, ivs['x'], ivs['y'], ivs['r'])
                            
        self.clearCurrentInstrument()
        self.currentInstrument = self.tempInstrument
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
            instrumentSaveURL = os.path.join(self.instrumentsURL, self.currentInstrument.name + '.dsinstrument')
        else:
            instrumentSaveURL = url

        self.currentInstrument.url = instrumentSaveURL

        if(os.path.exists(instrumentSaveURL)):
            os.remove(instrumentSaveURL)
        with open(instrumentSaveURL, 'w') as file:
            json.dump(saveData, file, sort_keys=True, indent=4)

    def socketUnattached(self, socket):
        self.mainWindow.hardwareWidget.iScene.connectPlugsAndSockets()
