from src.Constants import DSConstants as DSC

class ReadyCheckList(list):
    def __init__(self):
        super().__init__()

    def buildListFromDictionary(self):
        statusList = list()
        for item in self:
            statusList.append(item['Level'])
        return statusList

    def Can_Run(self):
        statusList = self.buildListFromDictionary()
        
        if DSC.READY_CHECK_ERROR in statusList:
            return False
        else:
            return True

    def Get_Status(self):
        statusList = self.buildListFromDictionary()

        if DSC.READY_CHECK_ERROR in statusList:
            return DSC.READY_CHECK_ERROR
        elif DSC.READY_CHECK_WARNING in statusList:
            return DSC.READY_CHECK_WARNING
        else:
            return DSC.READY_CHECK_READY