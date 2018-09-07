import os, sys, imp, time, inspect
from Managers.InstrumentManager.Instrument import *
from Managers.InstrumentManager.Digital_Trigger_Component import Digital_Trigger_Component
from Constants import DSConstants as DSConstants
import json as json
from PyQt5.Qt import *
from DSWidgets.controlWidget import readyCheckPacket

#class DSObject():
#    
#    def getMethods(self):
#        method_list = [func for func in dir(self) if callable(getattr(self, func))]
#        print("GETTTTTTTINGGGGG STOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOF")
#        for method in method_list:
#            print(str(method))
#            count = self.receivers(pyqtSignal(method)'()'))
#            print(method + ': ' + str(count))
#        print(method_list)

class InstrumentManager(QObject):
    Instrument_Modified = pyqtSignal(object)
    Instrument_Unloaded = pyqtSignal()
    Instrument_Loaded = pyqtSignal(object)

    Component_Modified = pyqtSignal(object)
    Events_Modified = pyqtSignal(object)

    Sequence_Unloaded = pyqtSignal()
    Sequence_Loading = pyqtSignal()
    Sequence_Loaded = pyqtSignal()
    Sequence_Name_Changed = pyqtSignal(str)

    instrumentWidget = None

    def __init__(self, mW):
        super().__init__()
        self.mW = mW
        self.instrumentDir = os.path.join(self.mW.rootDir, 'User Instruments')
        self.componentsDir = os.path.join(self.mW.rootDir, 'User Components')
        self.sequencesDir = os.path.join(self.mW.rootDir, 'Sequences')
        self.currentInstrument = None
        self.currentSequenceURL = None
        self.componentsAvailable = list()

        self.mW.DataStation_Closing.connect(self.unsavedChangesCheck)
        #self.Instrument_Modified.

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
                class_temp = getattr(py_mod, mod_name)(self.mW)
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

    def newInstrument(self, name, rootPath):
        self.currentInstrument = Instrument(self)
        self.currentInstrument.url = os.path.join(rootPath, name+'.dsinstrument')
        self.currentInstrument.Instrument_Modified.connect(self.Instrument_Modified)
        self.currentInstrument.Component_Modified.connect(self.Component_Modified)
        self.currentInstrument.Events_Modified.connect(self.Events_Modified)
        self.currentInstrument.name = name
        print('Instrument_Modified.emit()')
        self.Instrument_Modified.emit(self.currentInstrument)
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

    def addTriggerCompToInstrument(self, triggerComp):
        result = self.currentInstrument.addComponent(triggerComp)
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
                            if(comp['triggerComp'] is False):
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
        if(identifier == 'DigiTrigComp_mrb'):
            return Digital_Trigger_Component(self.mW)

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

###### SEQUENCE ######

    @pyqtSlot()
    def saveSequence(self):
        if(self.currentSequenceURL is None):
            self.saveAs()
            return

        fileName = os.path.basename(self.currentSequenceURL)
        if(os.path.exists(os.path.join(self.sequencesDir, self.currentInstrument.name)) is False):
            os.mkdir(os.path.join(self.sequencesDir, self.currentInstrument.name))
        saveURL = os.path.join(os.path.join(self.sequencesDir, self.currentInstrument.name), fileName)

        saveData = self.getSequenceSaveData()
        self.mW.postLog('Saving Sequence (' + saveURL + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.exists(saveURL)):
            os.remove(saveURL)
        with open(saveURL, 'w') as file:
            json.dump(saveData, file, sort_keys=True, indent=4)
        self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    @pyqtSlot()
    def saveSequenceAs(self):
        fname, ok = QInputDialog.getText(self.mW, "Sequence Name", "Sequence Name")
        if(os.path.exists(os.path.join(self.sequencesDir, self.currentInstrument.name)) is False):
            os.mkdir(os.path.join(self.sequencesDir, self.currentInstrument.name))
        saveURL = os.path.join(os.path.join(self.sequencesDir, self.currentInstrument.name), fname + '.dssequence')
        if(ok):
            pass
            #self.instrumentManager.currentInstrument.name = fname
        else:
            return

        if(os.path.exists(saveURL)):
            reply = QMessageBox.question(self.mW, 'File Warning!', 'File exists - overwrite?', QMessageBox.Yes, QMessageBox.No)
            if(reply == QMessageBox.No):
                return

        saveData = self.getSequenceSaveData()
        self.mW.postLog('Saving Sequence (' + saveURL + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.exists(saveURL)):
            os.remove(saveURL)
        with open(saveURL, 'w') as file:
            json.dump(saveData, file, sort_keys=True, indent=4)
        self.currentSequenceURL = saveURL
        self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    @pyqtSlot()
    def newSequence(self):
        result = DSNewFileDialog.newFile()

    def getSequenceSaveData(self):
        saveDataPacket = dict()
        saveDataPacket['instrument'] = self.currentInstrument.name

        saveData = list()
        for plot in self.mW.sequencerDockWidget.plots:
            if(plot.component.sequencerEditWidget is not None):
                packetItem = dict()
                packetItem['name'] = plot.component.compSettings['name']
                packetItem['type'] = plot.component.componentType
                packetItem['compID'] = plot.component.componentIdentifier
                packetItem['uuid'] = plot.component.compSettings['uuid']
                packetItem['events'] = plot.component.sequencerEditWidget.getEventsSerializable()
                saveData.append(packetItem)

        saveDataPacket['saveData'] = saveData
        return saveDataPacket

    def openSequence(self, filePath):
        if(self.currentInstrument is None):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("No instrument is loaded - cannot load sequence!")
            msg.setWindowTitle("Sequence/Instrument Compatibability Error")
            msg.setStandardButtons(QMessageBox.Ok)

            retval = msg.exec_()
            return

        self.mW.postLog('Loading Sequence (' + filePath + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        self.Sequence_Loading.emit()
        self.currentInstrument.Events_Modified.disconnect(self.Events_Modified)

        if(os.path.isfile(filePath) is True):
            with open(filePath, 'r') as file:
                try:
                    sequenceData = json.load(file)
                    if(self.processSequenceData(sequenceData) is False):
                        self.mW.postLog('Sequence at (' + filePath + ') not loaded - aborting! ', DSConstants.LOG_PRIORITY_HIGH)
                    else:
                        self.currentSequenceURL = filePath
                except ValueError as e:
                    self.mW.postLog('Corrupted sequence at (' + filePath + ') - aborting! ', DSConstants.LOG_PRIORITY_HIGH)
                    return

        self.mW.workspaceManager.userProfile['sequenceURL'] = filePath

        if(self.currentSequenceURL is not None):
            print('Sequence_Loaded.emit()')
            self.Sequence_Loaded.emit()
        else:
            print('Sequence_Unloaded.emit()')
            self.Sequence_Unloaded.emit()

        self.mW.postLog('Finished Loading Sequence!', DSConstants.LOG_PRIORITY_HIGH)
        self.currentInstrument.Events_Modified.connect(self.Events_Modified)

    def processSequenceData(self, data):
        instrument = data['instrument']
        self.currentInstrument.clearSequenceEvents()
        if(instrument != self.currentInstrument.name):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("The sequence is for a different instrument (" + instrument + ") than what is currently loaded (" + self.currentInstrument.name + "). It is unlikely this sequence will load.. Continue?")
            msg.setWindowTitle("Sequence/Instrument Compatibability Warning")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            retval = msg.exec_()
            if(retval == QMessageBox.No):
                return False

        dataSet = data['saveData']
        for datum in dataSet:
            comp = self.currentInstrument.getComponentByUUID(datum['uuid'])
            if(comp is None):
                self.mW.postLog('Sequence data for comp with uuid (' + datum['uuid'] + ') cannot be assigned! Possibly from different instrument.', DSConstants.LOG_PRIORITY_HIGH)
            else:
                comp.loadSequenceData(datum['events'])
        
        return True