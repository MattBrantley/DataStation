from PyQt5.Qt import *
import os, time
from pyqode.core import api, modes, panels
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs
from code import InteractiveConsole
from imp import new_module
from qtconsole.rich_ipython_widget import RichIPythonWidget
from qtconsole.inprocess import QtInProcessKernelManager

class Console(DSModule):
    Module_Name = 'Interactive Console'
    Module_Flags = [mfs.CAN_DELETE]
    ITEM_GUID = Qt.UserRole

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.ds = ds 


    def configureWidget(self, window):
        self.window = window
        self.interactiveConsole = DSConsole(self.ds)

        self.consoleWidget = ConsoleContainer(self.ds)
        self.setWidget(self.consoleWidget)

class ConsoleContainer(QWidget):
    def __init__(self, ds):
        super().__init__()
        self.ds = ds

        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

        self.consoleMainWidget = QWidget()
        self.put_ipy(self.consoleMainWidget)
        self.layout.addWidget(self.consoleMainWidget)

    def put_ipy(self, parent):
        kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        self.kernel = kernel_manager.kernel
        self.kernel.gui = 'qt4'

        kernel_client = kernel_manager.client()
        kernel_client.start_channels()
        kernel_client.namespace  = parent

        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()

        layout = QVBoxLayout(parent)
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)

        widget = RichIPythonWidget(parent=parent)
        layout.addWidget(widget)
        widget.kernel_manager = kernel_manager
        widget.kernel_client = kernel_client
        widget.exit_requested.connect(stop)
        ipython_widget = widget
        ipython_widget.show()
        #kernel.shell.push({'widget':widget,'kernel':kernel, 'parent':parent})
        ns = dict()
        ns['DataStation'] = self.ds
        ns['ds'] = self.ds
        ns['Hardware_Manager'] = self.ds.hM
        ns['hM'] = self.ds.hM
        ns['Instrument_Manager'] = self.ds.iM
        ns['iM'] = self.ds.iM
        ns['Module_Manager'] = self.ds.mM
        ns['mM'] = self.ds.mM
        ns['Workspace_Manager'] = self.ds.wM
        ns['wM'] = self.ds.wM
        self.kernel.shell.push(ns)

        return

class DSConsole(InteractiveConsole):
    def __init__(self, ds, names=None):
        names = names or {}
        names['console'] = self
        names['DataStation'] = ds
        names['datastation'] = ds
        names['ds'] = ds
        super().__init__(names)
        self.superspace = new_module('superspace')

    def runCodeSegment(self, code):
        code = self.preprocess(code)
        self.runcode(code)
        print()

    @staticmethod
    def preprocess(code):
        return code