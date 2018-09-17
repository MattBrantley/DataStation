import os, sys, imp, time, inspect
from src.Managers.InstrumentManager.Instrument import *
from src.Managers.InstrumentManager.Digital_Trigger_Component import Digital_Trigger_Component
from src.Constants import DSConstants as DSConstants
from src.Constants import readyCheckPacket
import json as json
from PyQt5.Qt import *

class InstrumentManager(QObject):

############################################################################################
##################################### EXTERNAL SIGNALS #####################################

##### Signals: Instrument #####
    Instrument_Loaded = pyqtSignal()
    Instrument_Unloaded = pyqtSignal()
    Instrument_Saving = pyqtSignal()
    Instrument_New = pyqtSignal()
    Instrument_Config_Changed = pyqtSignal()
    
##### Signals: Components #####
    Component_Added = pyqtSignal(object, object) # Instrument, Component
    Component_Removed = pyqtSignal(object, object) # Instrument, Component
    Component_Config_Changed = pyqtSignal()

##### Signals: Sequence #####
    Sequence_Loaded = pyqtSignal()
    Sequence_Unloaded = pyqtSignal()
    Sequence_Config_Changed = pyqtSignal()
    Sequence_Name_Changed = pyqtSignal()

##### Signals: Events #####
    Event_Added = pyqtSignal(object, object, object) # Instrument, Component, Event
    Event_Removed = pyqtSignal(object, object, object) # Instrument, Component, Event
    Event_Modified = pyqtSignal(object, object, object) # Instrument, Component, Event

##### Signals: Sockets #####
    Socket_Added = pyqtSignal(object, object, object) # Instrument, Component, Socket
    Socket_Removed = pyqtSignal()
    Socket_Attached = pyqtSignal(object, object, object) # Instrument, Component, Socket
    Socket_Detatched = pyqtSignal(object, object, object) # Instrument, Component, Socket
    Socket_Config_Changed = pyqtSignal()

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

##### Functions: Instrument Manager #####
    def Do_Ready_Check(self):
        return self.readyCheck()

    def Ready_Check_Status(self):
        return

##### Functions: Component Models #####
    def Get_Component_Models_Available(self):
        return self.componentsAvailable

    def Get_Component_Model_By_Index(self, ind):
        try:
            return self.componentsAvailable[ind]
        except:
            return None

##### Functions: Instrument Management #####
    def Load_Instrument(self, path):
        self.loadInstrument(path)

    def Close_Instrument(self):
        pass

    def Save_Instrument(self, name=None, path=None):
        if(self.currentInstrument is None):
            return False
        if(name is not None):
            self.currentInstrument.Set_Name(name)
        if(path is not None):
            self.currentInstrument.Set_Path(path)

        self.saveInstrument()

    def New_Instrument(self, name=None, path=None):
        self.newInstrument(name, path)

    def Get_Instrument(self):
        return self.currentInstrument

    def Add_Component(self, model):
        if(model is None):
            return False
        return self.addCompToInstrument(model)

##### Functions: Sequence Management #####
    #def Load_Sequence(self, path):
    #    if(self.currentInstrument is None):
    #        msg = QMessageBox()
    #        msg.setIcon(QMessageBox.Critical)
    #        msg.setText("No instrument is loaded - cannot load sequence!")
    #        msg.setWindowTitle("Sequence/Instrument Compatibability Error")
    #        msg.setStandardButtons(QMessageBox.Ok)

    #        retval = msg.exec_()
    #    else:
    #        self.openSequence(path)

    #def Save_Sequence(self, name=None, path=None):
    #    pass

############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, mW):
        super().__init__()
        self.mW = mW
        self.readyStatus = False
        self.instrumentDir = os.path.join(self.mW.rootDir, 'Instruments')
        self.componentsDir = os.path.join(self.mW.rootDir, 'Components')
        self.sequencesDir = os.path.join(self.mW.rootDir, 'Sequences')
        self.currentInstrument = None
        self.currentSequenceURL = None
        self.componentsAvailable = list()

        self.mW.DataStation_Closing.connect(self.unsavedChangesCheck)

##### DataStation Reserved Functions #####

    def connections(self, wM, hM):
        self.wM = wM
        self.hM = hM
        # Called after all managers are created so they can connect to each other's signals

    def unsavedChangesCheck(self):
        print('UNSAVED CHANGES TO INSTRUMENT')
        
    def readyCheck(self):
        subs = list()
        self.readyStatus = True
        if(self.currentInstrument is not None):
            check = self.currentInstrument.readyCheck()
            self.readyStatus = check.readyStatus
            subs.append(check)
        else:
            self.readyStatus = False
            return readyCheckPacket('Instrument Manager', DSConstants.READY_CHECK_ERROR, msg='No Instrument Loaded!')

        return readyCheckPacket('Instrument Manager', DSConstants.READY_CHECK_READY, subs=subs)

##### Functions Called Internally By Current Instrument #####

    def instrumentModified(self, instrument):
        pass

    def instrumentConfigModified(self, instrument):
        self.Instrument_Config_Changed.emit()

    def componentModified(self, instrument):
        pass

    def componentAdded(self, instrument, component):
        self.Component_Added.emit(instrument, component)

    def componentRemoved(self, instrument, component):
        self.Component_Removed.emit(instrument, component)

    def socketAttached(self, instrument, component, socket):
        self.Socket_Attached.emit(instrument, component, socket)

    def socketDetatched(self, instrument, component, socket):
        self.Socket_Detatched.emit(instrument, component, socket)

    def socketAdded(self, instrument, component, socket):
        self.Socket_Added.emit(instrument, component, socket)

    def eventAdded(self, instrument, component, event):
        self.Event_Added.emit(instrument, component, event)

    def eventRemoved(self, instrument, component, event):
        self.Event_Removed.emit(instrument, component, event)

    def eventModified(self, instrument, component, event):
        self.Event_Modified.emit(instrument, component, event)

##### Search Functions ######

    def removeCompByUUID(self, uuid):
        if(self.currentInstrument is not None):
            self.currentInstrument.removeComponent(self.getComponentByUUID(uuid))
        return True

    def getTrigCompsRefUUID(self, uuid):
        if(self.currentInstrument is not None):
            return self.currentInstrument.getTrigCompsRefUUID(uuid)
        else:
            return None

    def findCompModelByIdentifier(self, identifier):
        if(identifier == 'DigiTrigComp_mrb'):
            return Digital_Trigger_Component(self.mW)

        for comp in self.componentsAvailable:
            if(comp.componentIdentifier == identifier):
                return comp
        return None

##### Instrument Manipulations ######

    def loadPreviousInstrument(self):
        if('instrumentURL' in self.wM.userProfile):
            if(self.wM.userProfile['instrumentURL'] is not None):
                self.loadInstrument(self.wM.userProfile['instrumentURL'])

    def newInstrument(self, name, rootPath): # Instrument_Unloaded // Instrument_New
        self.Instrument_Unloaded.emit()
        self.currentInstrument = Instrument(self)
        self.currentInstrument.url = os.path.join(rootPath, name+'.dsinstrument')
        self.currentInstrument.name = name
        self.Instrument_New.emit()

    def saveInstrument(self):# Instrument_Saving
        if(self.currentInstrument is not None):
            self.mW.postLog('VI_Save', DSConstants.LOG_PRIORITY_HIGH, textKey=True)
            self.Instrument_Saving.emit()
            self.writeInstrumentToFile(self.currentInstrument.savePacket(), self.currentInstrument.url)
            self.mW.postLog(' ...Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
        else:
            self.mW.postLog('VI_Save_No_VI', DSConstants.LOG_PRIORITY_HIGH, textKey=True)

    def writeInstrumentToFile(self, saveData, url=None):
        if(url is None):
            instrumentSaveURL = self.instrumentDir  
        else:
            instrumentSaveURL = url

        self.currentInstrument.url = instrumentSaveURL

        fullPath = os.path.join(self.instrumentDir, self.currentInstrument.name + '.dsinstrument') 

        if(os.path.exists(fullPath)):
            os.remove(fullPath)
        with open(fullPath, 'w') as file:
            json.dump(saveData, file, sort_keys=True, indent=4)

    def loadInstrument(self, url): # Instrument_Unloaded // Instrument_Loaded
        self.mW.postLog('Loading User Instrument (' + url + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.exists(url) is False):
            self.mW.postLog('Path (' + url + ') does not exist! Aborting! ', DSConstants.LOG_PRIORITY_HIGH)
            return

        with open(url, 'r') as file:
            try:
                instrumentData = json.load(file)
                self.Instrument_Unloaded.emit()
                if(isinstance(instrumentData, dict)):
                    if(self.processInstrumentData(instrumentData, url) is False):
                        self.mW.postLog('Corrupted instrument at (' + url + ') - aborting! ', DSConstants.LOG_PRIORITY_MED)
            except ValueError as e:
                self.mW.postLog('Corrupted instrument at (' + url + ') - aborting! ', DSConstants.LOG_PRIORITY_MED)
                return
        self.mW.postLog('Finished Loading User Instrument!', DSConstants.LOG_PRIORITY_HIGH)

        self.Instrument_Loaded.emit()

    def processInstrumentData(self, instrumentData, url):
        self.tempInstrument = Instrument(self)
        self.tempInstrument.url = url
        if('name' in instrumentData):
            self.tempInstrument.name = instrumentData['name']
        else:
            return False

        if('compList' in instrumentData):
            for comp in instrumentData['compList']:
                if(('compIdentifier' in comp) and ('compType' in comp)):
                    compModel = self.findCompModelByIdentifier(comp['compIdentifier'])
                    if(compModel is None):
                        self.mW.postLog('Instrument contains component (' + comp['compType'] + ':' + comp['compIdentifier'] + ') that is not in the available component modules. Ignoring this component!', DSConstants.LOG_PRIORITY_MED)
                    else:
                        result = self.tempInstrument.Add_Component(compModel, loadData=comp['compSettings'])
                        #if('compSettings' in comp):
                        #    result.loadCompSettings(comp['compSettings'])
                        if('sockets' in comp):
                            if(isinstance(comp['sockets'], list)):
                                result.loadSockets(comp['sockets'])

        self.currentInstrument = self.tempInstrument
        self.currentInstrument.reattachSockets()

    def addCompToInstrument(self, compModel):
        if (self.currentInstrument is None):
            self.mW.postLog('No instrument is loaded - creating new one! ', DSConstants.LOG_PRIORITY_HIGH)
            self.currentInstrument = Instrument(self)

        result = self.currentInstrument.addComponent(compModel)
        return result

##### Sequence Manipulation #####

    def openSequenceFile(self, filePath):
        self.mW.postLog('Opening Sequence File (' + filePath + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        sequenceData = None

        if(os.path.isfile(filePath) is True):
            with open(filePath, 'r') as file:
                try:
                    sequenceData = json.load(file)
                except ValueError as e:
                    self.mW.postLog('Corrupted sequence file - aborting!', DSConstants.LOG_PRIORITY_HIGH)
                    return None
        else:
            self.mW.postLog('Sequence Path was invalid - aborting!', DSConstants.LOG_PRIORITY_HIGH)
            return None

        return sequenceData

        if(self.instrument.processSequenceData(sequenceData) is False):
            self.mW.postLog('Sequence at (' + filePath + ') not loaded - aborting! ', DSConstants.LOG_PRIORITY_HIGH)
        else:
            self.currentSequenceURL = filePath

        self.wM.userProfile['sequenceURL'] = filePath
        self.mW.postLog('Finished Loading Sequence!', DSConstants.LOG_PRIORITY_HIGH)

        if(self.currentSequenceURL is not None):
            self.Sequence_Loaded.emit()
            return True
        else:
            self.Sequence_Unloaded.emit()
            return False

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

    def saveSequenceAs(self):
        fname, ok = QInputDialog.getText(self.mW, "Sequence Name", "Sequence Name")
        if(os.path.exists(os.path.join(self.sequencesDir, self.currentInstrument.name)) is False):
            os.mkdir(os.path.join(self.sequencesDir, self.currentInstrument.name))
        saveURL = os.path.join(os.path.join(self.sequencesDir, self.currentInstrument.name), fname + '.dssequence')
        if(ok):
            pass
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

    def newSequence(self):
        result = DSNewFileDialog.newFile()

##### Components #####

    def loadComponents(self):
        self.mW.postLog('Loading Component Models... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.componentsDir):
            for name in files:
                url = os.path.join(root, name)
                compHolder = self.loadComponentFromFile(url)
                if (compHolder != None):
                    self.componentsAvailable.append(compHolder)

        self.mW.postLog('Finished Loading Component Models!', DSConstants.LOG_PRIORITY_HIGH)

    def loadComponentFromFile(self, filepath): # I think this is only for the models
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

        if (py_mod != None):
            if(hasattr(py_mod, mod_name) is True):
                class_temp = getattr(py_mod, mod_name)(self.mW)
                if issubclass(type(class_temp), Component):
                    class_inst = class_temp
                    loaded = True

        if(loaded):
            class_inst.iM = self
            self.mW.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.mW.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

        return class_inst