from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class TestModule(DSModule):
    Module_Name = 'A Simple Test Module'
    Module_Flags = [mfs.SHOW_ON_CREATION, mfs.FLOAT_ON_CREATION]

