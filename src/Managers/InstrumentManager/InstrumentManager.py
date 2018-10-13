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
    Instrument_File_Loaded = pyqtSignal(object) # Instrument
    Instrument_Removed = pyqtSignal(object) # Instrument
    Instrument_Saved = pyqtSignal(object) # Instrument
    Instrument_New = pyqtSignal(object) # Instrument
    Instrument_Config_Changed = pyqtSignal(object) # Instrument
    
##### Signals: Components #####
    Component_Added = pyqtSignal(object, object) # Instrument, Component
    Component_Removed = pyqtSignal(object, object) # Instrument, Component
    Component_Programming_Modified = pyqtSignal(object, object) # Instrument, Component

##### Signals: Sequence #####
    Sequence_Loaded = pyqtSignal(object, str) # Instrument, Sequence Path
    Sequence_Saved = pyqtSignal(object, str) # Instrument, Sequence Path

##### Signals: Events #####
    Event_Added = pyqtSignal(object, object, object) # Instrument, Component, Event
    Event_Removed = pyqtSignal(object, object, object) # Instrument, Component, Event
    Event_Modified = pyqtSignal(object, object, object) # Instrument, Component, Event

##### Signals: Sockets #####
    Socket_Added = pyqtSignal(object, object, object) # Instrument, Component, Socket
    Socket_Removed = pyqtSignal()
    Socket_Attached = pyqtSignal(object, object, object) # Instrument, Component, Socket
    Socket_Detatched = pyqtSignal(object, object, object) # Instrument, Component, Socket
    Socket_Measurement_Packet_Recieved = pyqtSignal(object, object, object, object) # Instrument, Component, Socket, measurementPacket

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
        newInstrument = self.New_Instrument()
        if newInstrument is not None:
            mewInstrument.Load_Instrument_File(path)

    def Close_Instrument(self):
        pass

    def New_Instrument(self, name=None, directory=None):
        return self.newInstrument(name, directory)

    def Instrument_Save_Directory(self):
        return self.instrumentsDir

    def Component_Save_Directory(self):
        return self.componentsDir

    def Sequences_Save_Directory(self):
        return self.sequencesDir

############################################################################################
#################################### INTERNAL USER ONLY ####################################

    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        self.readyStatus = False
        self.instrumentsDir = os.path.join(self.ds.rootDir, 'Instruments')
        self.componentsDir = os.path.join(self.ds.rootDir, 'Components')
        self.sequencesDir = os.path.join(self.ds.rootDir, 'Sequences')
        self.currentSequenceURL = None
        self.componentsAvailable = list()
        self.instruments = list()

        self.ds.DataStation_Closing.connect(self.unsavedChangesCheck)

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
        if self.instruments:
            for instrument in self.instruments:
                check = instrument.readyCheck()
                self.readyStatus = check.readyStatus
                subs.append(check)
        else:
            self.readyStatus = False
            return readyCheckPacket('Instrument Manager', DSConstants.READY_CHECK_ERROR, msg='No Instruments Loaded!')

        return readyCheckPacket('Instrument Manager', DSConstants.READY_CHECK_READY, subs=subs)

##### Functions Called Internally By Current Instrument #####

    def instrumentModified(self, instrument):
        pass

    def instrumentConfigModified(self, instrument):
        self.Instrument_Config_Changed.emit(instrument)

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

    def eventModified(self, instrument, component, event): ## Not used?
        self.Event_Modified.emit(instrument, component, event)

    def sequenceLoaded(self, instrument, sequencePath):
        self.Sequence_Loaded.emit(instrument, sequencePath)

    def programmingModified(self, instrument, component):
        self.Component_Programming_Modified.emit(instrument, component)

    def measurementRecieved(self, instrument, component, socket, measurementPacket):
        self.Socket_Measurement_Packet_Recieved.emit(instrument, component, socket, measurementPacket)

    def instrumentSaved(self, instrument):
        self.Instrument_Saved.emit(instrument)

    def instrumentFileLoaded(self, instrument):
        self.Instrument_File_Loaded.emit(instrument)
##### Search Functions ######

    def removeCompByUUID(self, uuid):
        for instrument in self.instruments:
            instrument.removeComponent(self.getComponentByUUID(uuid))
        return True

    def findCompModelByIdentifier(self, identifier):
        for comp in self.componentsAvailable:
            if(comp.componentIdentifier == identifier):
                return comp
        return None

##### Instrument Manipulations ######

    def newInstrument(self, name, rootPath): # Instrument_Unloaded // Instrument_New
        newInstrument = Instrument(self)
        newInstrument.url = os.path.join(rootPath, name+'.dsinstrument')
        newInstrument.name = name
        self.instruments.append(newInstrument)
        self.Instrument_New.emit(newInstrument)
        return newInstrument

##### Sequence Manipulation #####

    def openSequenceFile(self, filePath):
        self.ds.postLog('Opening Sequence File (' + filePath + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        sequenceData = None

        if(os.path.isfile(filePath) is True):
            with open(filePath, 'r') as file:
                try:
                    sequenceData = json.load(file)
                except ValueError as e:
                    self.ds.postLog('Corrupted sequence file - aborting!', DSConstants.LOG_PRIORITY_HIGH)
                    return None
        else:
            self.ds.postLog('Sequence Path was invalid - aborting!', DSConstants.LOG_PRIORITY_HIGH)
            return None

        self.currentInstrument.sequenceInfoUpdate(filePath, os.path.basename(filePath))
        return sequenceData

        if(self.instrument.processSequenceData(sequenceData) is False): ### self.instrument?
            self.ds.postLog('Sequence at (' + filePath + ') not loaded - aborting! ', DSConstants.LOG_PRIORITY_HIGH)
        else:
            self.currentSequenceURL = filePath

        self.ds.postLog('Finished Loading Sequence!', DSConstants.LOG_PRIORITY_HIGH)

    def getSequenceSaveData(self):
        if(self.currentInstrument is not None):
            return self.currentInstrument.getSequenceSaveData()
        else:
            return None

    def saveSequence(self):
        if(self.currentSequenceURL is None):
            self.saveSequenceAs()
            return

        fileName = os.path.basename(self.currentSequenceURL)
        if(os.path.exists(os.path.join(self.sequencesDir, self.currentInstrument.name)) is False):
            os.mkdir(os.path.join(self.sequencesDir, self.currentInstrument.name))
        saveURL = os.path.join(os.path.join(self.sequencesDir, self.currentInstrument.name), fileName)

        saveData = self.getSequenceSaveData()
        self.ds.postLog('Saving Sequence (' + saveURL + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.exists(saveURL)):
            os.remove(saveURL)
        with open(saveURL, 'w') as file:
            json.dump(saveData, file, sort_keys=True, indent=4)
            
        self.currentInstrument.sequenceInfoUpdate(saveURL, fileName)
        self.Sequence_Saved.emit(self.currentInstrument, saveURL) 
        self.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def saveSequenceAs(self):
        fname, ok = QInputDialog.getText(self.ds, "Sequence Name", "Sequence Name")
        if(os.path.exists(os.path.join(self.sequencesDir, self.currentInstrument.name)) is False):
            os.mkdir(os.path.join(self.sequencesDir, self.currentInstrument.name))
        saveURL = os.path.join(os.path.join(self.sequencesDir, self.currentInstrument.name), fname + '.dssequence')
        if(ok):
            pass
        else:
            return

        if(os.path.exists(saveURL)):
            reply = QMessageBox.question(self.ds, 'File Warning!', 'File exists - overwrite?', QMessageBox.Yes, QMessageBox.No)
            if(reply == QMessageBox.No):
                return

        saveData = self.getSequenceSaveData()
        self.ds.postLog('Saving Sequence (' + saveURL + ')... ', DSConstants.LOG_PRIORITY_HIGH)
        if(os.path.exists(saveURL)):
            os.remove(saveURL)
        with open(saveURL, 'w') as file:
            json.dump(saveData, file, sort_keys=True, indent=4)
        self.currentSequenceURL = saveURL

        self.currentInstrument.sequenceInfoUpdate(saveURL, fname+'.dssequence')
        self.Sequence_Saved.emit(self.currentInstrument) 
        self.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

    def newSequence(self):
        result = DSNewFileDialog.newFile()

##### Components #####

    def loadComponents(self):
        self.ds.postLog('Loading Component Models... ', DSConstants.LOG_PRIORITY_HIGH)

        for root, dirs, files in os.walk(self.componentsDir):
            for name in files:
                url = os.path.join(root, name)
                compHolder = self.loadComponentFromFile(url)
                if (compHolder != None):
                    self.componentsAvailable.append(compHolder)

        self.ds.postLog('Finished Loading Component Models!', DSConstants.LOG_PRIORITY_HIGH)

    def loadComponentFromFile(self, filepath): # I think this is only for the models
        class_inst = None
        py_mod = None
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        loaded = False

        if file_ext.lower() == '.py':
            self.ds.postLog('   Found Component Script: ' + filepath, DSConstants.LOG_PRIORITY_MED)
            py_mod = imp.load_source(mod_name, filepath)
        else:
            return

        if (py_mod != None):
            if(hasattr(py_mod, mod_name) is True):
                class_temp = getattr(py_mod, mod_name)(self.ds)
                if issubclass(type(class_temp), Component):
                    class_inst = class_temp
                    loaded = True

        if(loaded):
            class_inst.iM = self
            self.ds.postLog('  (Success!)', DSConstants.LOG_PRIORITY_MED, newline=False)
        else:
            self.ds.postLog(' (Failed!)', DSConstants.LOG_PRIORITY_MED, newline=False)

        return class_inst