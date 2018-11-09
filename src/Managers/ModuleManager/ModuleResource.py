

#################################### MODULE RESOURCE RESOURCE ####################################
class ModuleResource():
####################################################################
######################## EXTERNAL FUNCTIONS ########################
    def Has_Tags(self, tags):
        return self.hasTags(tags)

    def Add_Tag(self, tag):
        self.tags.append(tag)

    def Remove_Tag(self, tag):
        self.tags.remove(tag)

    def Clear_Tags(self):
        self.tags = list()

    def Get_Name(self):
        return self.name

####################################################################
######################## INTERNAL USER ONLY ########################
    def __init__(self, module, name, tags):
        self.module = module
        self.name = name
        self.tags = tags

    def hasTags(self, tags):
        if set(tags) <= set(self.tags):
            return True
        else:
            return False



#################################### ARBITRARY DATA RESOURCE ####################################
class ArbitraryDataResource(ModuleResource):
####################################################################
######################## EXTERNAL FUNCTIONS ########################
    def Get_Data(self):
        return self.data

    def Set_Data(self, data):
        self.data = data

####################################################################
######################## INTERNAL USER ONLY ########################
    def __init__(self, module, name, tags, data):
        super().__init__(module, name, tags)
        self.data = data




#################################### MESUREMENT PACKET RESOURCE ####################################
class MeasurementPacketResource(ModuleResource):
####################################################################
######################## EXTERNAL FUNCTIONS ########################
    def Get_Measurement_Packet(self):
        return self.measurementPacket

    def Set_Measurement_Packet(self, measurementPacket):
        self.measurementPacket = measurementPacket

####################################################################
######################## INTERNAL USER ONLY ########################
    def __init__(self, module, name, tags, measurementPacket=None):
        super().__init__(module, name, tags)
        self.measurementPacket = measurementPacket