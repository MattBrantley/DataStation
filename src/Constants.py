import time

class DSConstants():
    MW_STATE_NO_WORKSPACE = 0
    MW_STATE_WORKSPACE_LOADED = 1

    LOG_PRIORITY_LOW = 4
    LOG_PRIORITY_MED = 3
    LOG_PRIORITY_HIGH = 2
    LOG_PRIORITY_DEBUG = 1
    
    FILTER_OBJ_SOURCE = 100
    FILTER_OBJ_FILTER = 101
    FILTER_OBJ_PLUG = 102

    STATUS_NOT_READY = 200
    STATUS_READY = 201
    STATUS_CONFIGURING = 202
    STATUS_RUNNING = 203
    STATUS_PROCESSING = 204
    STATUS_UNKNOWN = 205
    STATUS_WAITING = 206
    STATUS_READY_CHECKING = 207

    READY_CHECK_READY = 0
    READY_CHECK_WARNING = 1
    READY_CHECK_ERROR = 2
    READY_CHECK_OTHER = 3

    def __init__(self):
        self.language = 'English'
        self.logTexts = dict()
        self.initEnglishLogText()

    def getLogText(self, key):
        if self.language in self.logTexts:
            if key.upper() in self.logTexts[self.language].text:
                return self.logTexts[self.language].text[key.upper()]
            else:
                return "LOG ERROR!: Invalid logText key used!"
        else:
            return "LOG ERROR!: Invalid language key used!"

    def initEnglishLogText(self):
        self.logTexts['English'] = DSLogTexts('English')

        self.logTexts['English'].text['VI_SAVE'] = 'Saving Virtual Instrument to file...'
        self.logTexts['English'].text['VI_SAVE_NO_VI'] = 'Attempting to write virtual instrument to file but no instrument is loaded!! Aborting...'

class moduleFlags():
    CAN_HIDE = 200
    CAN_DELETE = 201

    CAN_FLOAT = 210

    SINGLE_INSTANCE = 300
    DEFAULT_MODULE = 301

class DSLogTexts():

    def __init__(self, language):
        self.language = language
        self.text = dict()

class readyCheckPacket():

    def __init__(self, name, readyStatus, subs=None, msg=''):
        self.name = name
        self.readyStatus = readyStatus
        self.subs = subs
        self.msg = msg
        self.areSubsReady()

    def areSubsReady(self):
        if(self.subs is not None):
            for sub in self.subs:
                if(sub is not None):
                    sub.areSubsReady()
                    if(sub.readyStatus is not DSConstants.READY_CHECK_READY):
                        self.readyStatus = sub.readyStatus

    def generateMessages(self, indent):
        msgList = list()
        indent = indent + 1
        if(self.readyStatus is not DSConstants.READY_CHECK_READY):
            indentStr = ''
            for i in range(0,indent):
                indentStr = indentStr + '    '
            if(indent > 0 ):
                indentStr = indentStr + u'\u21B3'
            msg = readyCheckMsg(indentStr + self.name + ': ' + self.msg, self.readyStatus)
            msgList.append(msg)
            if(self.subs is not None):
                for sub in self.subs:
                    msgList.extend(sub.generateMessages(indent))
        
        return msgList

class readyCheckMsg():
    def __init__(self, msg, status):
        self.msg = msg
        self.status = status

class logObject():
    def __init__(self, source, text, warningLevel):
        self.source = source
        self.text = text
        self.warningLevel = warningLevel
        self.timeStamp = time.localtime()

    def timeText(self):
        return time.strftime('[%m/%d/%Y %H:%M:%S] ', self.timeStamp)