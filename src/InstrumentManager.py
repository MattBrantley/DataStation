import os, sys, imp
from Instrument import *
from Constants import DSConstants as DSConstants

class InstrumentManager():
    currentInstrument = None
    instrumentsURL = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'User Instruments')
    componentsURL = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'User Components')
    componentsAvailable = []
    instrumentWidget = None

    def __init__(self, workspace, instrumentsURL, componentsURL):
        self.workspace = workspace
        self.mainWindow = self.workspace.mainWindow
        self.loadComponents()
        self.loadInstruments()
        #self.initDefaultInstrument()

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

    def loadInstruments(self):
        self.mainWindow.postLog('Loading User Instruments... ', DSConstants.LOG_PRIORITY_HIGH)
        
        self.mainWindow.postLog('Finished Loading User Instruments!', DSConstants.LOG_PRIORITY_HIGH)

    def getAvailableComponents(self):
        return self.componentsAvailable

    def addCompToInstrument(self, dropIndex):
        if (self.currentInstrument is None):
            self.mainWindow.postLog('No instrument is loaded - creating new one! ', DSConstants.LOG_PRIORITY_HIGH)
            self.currentInstrument = Instrument(self)

        comp = self.componentsAvailable[dropIndex]
        return self.currentInstrument.addComponent(comp)

    def initDefaultInstrument(self):
        self.currentInstrument = Instrument(self)
        #print(self.instrumentsURL)
        #print(self.componentsURL)
