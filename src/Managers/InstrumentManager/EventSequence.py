import os, json
from src.Constants import DSConstants

class EventSequence():
############################################################################################
#################################### EXTERNAL FUNCTIONS ####################################

    def Save_Sequence(self, filepath):
        self.saveSequence(filepath)

    def Get_Sequence_Serialized(self):
        savePacket = self.getSequenceSaveData()
        return json.dumps(savePacket, sort_keys=True, indent=4)

    def Load_Sequence_File(self, filePath):
        self.loadSequence(filePath)

    def Load_Sequence_Data(self, data):
        self.loadSequenceData(data)

    def Get_File_Name(self):
        return self.filename

    def Get_Path(self):
        return self.path

    def Get_Directory(self):
        try:
            return os.path.dirname(self.path)
        except:
            return None

    def Clear_All_Events(self):
        self.clearAllEvents()

    def Get_Sequence_Length(self):
        return self.getSequenceLength()

############################################################################################
#################################### INTERNAL USER ONLY ####################################
    def __init__(self, ds, instr):
        self.ds = ds
        self.iM = ds.iM
        self.instr = instr
        self.filename = None
        self.path = None
        self.modified = False
        
    def readyCheck(self, traceIn):
        trace = traceIn.copy().append(self)

    def clearAllEvents(self):
        for comp in self.instr.Get_Components():
            comp.Clear_Events()

    #### Load Sequence ####
    def loadSequence(self, path):
        self.ds.postLog('Loading Sequence data from file: ' + str(path), DSConstants.LOG_PRIORITY_HIGH)
        try:
            self.path = path
            data = self.openSequenceFile(path)
            return self.parseSequenceData(data)
        except:
            self.ds.postLog('Error loading Sequence data from file: ' + str(path), DSConstants.LOG_PRIORITY_HIGH)
            return False

    def loadSequenceData(self, data):
        return self.parseSequenceData(json.loads(data))

    def parseSequenceData(self, data):
        self.ds.postLog('Applying sequence to instrument... ', DSConstants.LOG_PRIORITY_HIGH)

        if(data is None):
            self.ds.postLog('Sequence data was empty - aborting!', DSConstants.LOG_PRIORITY_HIGH)
            return False

        self.Clear_All_Events()

        for datum in data['eventData']:
            comp = self.instr.Get_Components(uuid=datum['uuid'])
            if(not comp):
                self.ds.postLog('Sequence data for comp with uuid (' + datum['uuid'] + ') cannot be assigned! Possibly from different instrument.', DSConstants.LOG_PRIORITY_HIGH)
            else:
                comp[0].loadSequenceData(datum['events'])

        self.ds.postLog('Sequence applied to instrument!', DSConstants.LOG_PRIORITY_HIGH)
        self.instr.sequenceLoaded()

        return True

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

        self.sequencePath = filePath
        self.sequenceName =  os.path.basename(filePath)

        return sequenceData
    
    #### Save Sequence ####    
    def saveSequence(self, path):
        self.ds.postLog('Saving Sequence (' + path + ')... ', DSConstants.LOG_PRIORITY_HIGH)

        self.filename = os.path.basename(path)
        self.path = os.path.join(os.path.join(self.ds.iM.Sequences_Save_Directory(), self.instr.Get_Name()), self.Get_File_Name())
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

        if(os.path.exists(self.Get_Path())):
            os.remove(self.Get_Path())
        with open(self.Get_Path(), 'w') as file:
            savePacket = self.getSequenceSaveData()
            json.dump(savePacket, file, sort_keys=True, indent=4)
            
        self.instr.sequenceSaved()
        self.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)
        
    def getSequenceSaveData(self):
        savePacket = dict()
        savePacket['instrument'] = self.instr.Get_Name()
        compSaveData = list()
        for comp in self.instr.Get_Components():
            compSaveData.append(comp.Serialize_Events())
        savePacket['eventData'] = compSaveData
        return savePacket

    def getSequenceLength(self):
        lengths = list()
        for comp in self.instr.Get_Components():
            for event in comp.Get_Events():
                lengths.append(event.time + event.Get_Length())
        return max(lengths)