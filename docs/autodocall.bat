
sphinx-apidoc -o source/ ../../DataStation
sphinx-apidoc -o source/ ../src/
sphinx-apidoc -o source/HardwareManager ../src/Managers/HardwareManager
sphinx-apidoc -o source/InstrumentManager ../src/Managers/InstrumentManager
sphinx-apidoc -o source/ModuleManager ../src/Managers/ModuleManager
sphinx-apidoc -o source/WorkspaceManager ../src/Managers/WorkspaceManager

make html