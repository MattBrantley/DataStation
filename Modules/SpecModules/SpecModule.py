from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class SpecModule(DSModule):
    Module_Name = 'Module In A Folder'
    Module_Flags = [mfs.SHOW_ON_CREATION, mfs.FLOAT_ON_CREATION]

