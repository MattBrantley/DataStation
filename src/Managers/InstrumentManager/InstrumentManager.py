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
    Instrument_Saving = pyqtSignal(object) # Instrument
    Instrument_New = pyqtSignal(object) # Instrument
    Instrument_Config_Changed = pyqtSignal(object) # Instrument
    Instrument_Name_Changed = pyqtSignal(object) # Instrument
    
##### Signals: Components #####
    Component_Added = pyqtSignal(object, object) # Instrument, Component
    Component_Removed = pyqtSignal(object, object) # Instrument, Component
    Component_Programming_Modified = pyqtSignal(object, object) # Instrument, Component

##### Signals: Sequence #####
    Sequence_Loaded = pyqtSignal(object) # Instrument, Sequence Path
    Sequence_Saved = pyqtSignal(object) # Instrument, Sequence Path

##### Signals: Events #####
    Event_Added = pyqtSignal(object, object, object) # Instrument, Component, Event
    Event_Removed = pyqtSignal(object, object, object) # Instrument, Component, Event
    Event_Modified = pyqtSignal(object, object, object) # Instrument, Component, Event

##### Signals: Sockets #####
    Socket_Added = pyqtSignal(object, object, object) # Instrument, Component, Socket
    Socket_Attached = pyqtSignal(object, object, object) # Instrument, Component, Socket
    Socket_Detatched = pyqtSignal(object, object, object) # Instrument, Component, Socket
    Socket_Measurement_Packet_Recieved = pyqtSignal(object, object, object, object) # Instrument, Component, Socket, measurementPacket

############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

##### Functions: Component Models #####
    def Get_Component_Models_Available(self):
        return self.componentsAvailable

    def Get_Component_Model_By_Index(self, ind):
        try:
            return self.componentsAvailable[ind]
        except:
            return None

##### Functions: Instrument Management #####
    def Get_Instruments(self, name=-1, path=-1, uuid=-1):
        return self.getInstruments(name, path, uuid)

    def Load_Instrument(self, path):
        newInstrument = self.New_Instrument()
        if newInstrument is not None:
            newInstrument.Load_Instrument_File(path)

    def Close_Instrument(self, instrument):
        self.closeInstrument(instrument)

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
        self.instrumentsDir = os.path.join(self.ds.rootDir, 'Instruments')
        self.componentsDir = os.path.join(self.ds.rootDir, 'Components')
        self.sequencesDir = os.path.join(self.ds.rootDir, 'Sequences')
        self.currentSequenceURL = None
        self.componentsAvailable = list()
        self.instruments = list()

        self.loadComponents()

##### DataStation Reserved Functions #####
    def connections(self):
        self.wM = self.ds.wM
        self.hM = self.ds.hM
        self.mM = self.ds.mM
        # Called after all managers are created so they can connect to each other's signals

##### Functions Called Internally By Factoried Instruments #####
    def instrumentModified(self, instrument):
        pass

    def instrumentNameChanged(self, instrument):
        self.Instrument_Name_Changed.emit(instrument)

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

    def sequenceLoaded(self, instrument):
        self.Sequence_Loaded.emit(instrument)

    def sequenceSaved(self, instrument):
        self.Sequence_Saved.emit(instrument)

    def programmingModified(self, instrument, component):
        self.Component_Programming_Modified.emit(instrument, component)

    def measurementRecieved(self, instrument, component, socket, measurementPacket):
        self.Socket_Measurement_Packet_Recieved.emit(instrument, component, socket, measurementPacket)

    def instrumentSaved(self, instrument):
        self.Instrument_Saved.emit(instrument)

    def instrumentFileLoaded(self, instrument):
        self.Instrument_File_Loaded.emit(instrument)
        
##### Search Functions ######

    def getInstruments(self, name, path, uuid):
        outList = list()
        for instrument in self.instruments:
            if(instrument.Get_Name() != name and name != -1):
                continue
            if(instrument.Get_Path() != path and path != -1):
                continue
            if(instrument.Get_UUID() != uuid and uuid != -1):
                continue
            outList.append(instrument)
        return outList

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
    def newInstrument(self, name, rootPath): # Instrument_New
        newInstrument = Instrument(self.ds)
        if name is not None:
            newInstrument.name = name
        if rootPath is not None:
            newInstrument.directory = rootPath
        self.instruments.append(newInstrument)
        self.Instrument_New.emit(newInstrument)
        return newInstrument

    def closeInstrument(self, instrument): # Instrument_Removed
        self.instruments.remove(instrument)
        self.Instrument_Removed.emit(instrument)

##### Sequence Manipulation #####
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