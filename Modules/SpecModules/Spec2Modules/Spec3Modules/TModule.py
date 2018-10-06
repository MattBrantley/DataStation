from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class TModule(DSModule):
    Module_Name = 'Deep MOdule'
    Module_Flags = [mfs.SHOW_ON_CREATION, mfs.FLOAT_ON_CREATION]

