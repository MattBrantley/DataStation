from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, sys, imp, math, time
from src.Constants import DSConstants as DSConstants 
import filterStackWidget, hardwareListWidget, gridViewWidget
from src.Managers.InstrumentManager.Sockets import AOSocket, AISocket, DOSocket, DISocket
from src.Managers.HardwareManager.Sources import AOSource, AISource, DOSource, DISource

class hardwareListWidget(QWidget):

    def __init__(self, dockWidget, ds):
        super().__init__()
        self.dockWidget = dockWidget
        self.ds = ds
        self.hM = ds.hM
        self.iM = ds.iM
        self.wM = ds.wM

        self.mainLayout = QVBoxLayout()
        self.hardwareList = hardwareListView(self.dockWidget.Get_Window(), self.ds)
        self.setLayout(self.mainLayout)

        self.scroll = QScrollArea(self)
        self.mainLayout.addWidget(self.scroll)

        self.newButton = QPushButton("Add Hardware Object")
        self.newButton.pressed.connect(self.newButtonPressed)
        self.mainLayout.addWidget(self.newButton)

        self.mainLayout.setSpacing(2)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.hardwareList)

        self.hM.Hardware_Added.connect(self.addHardware)
        
    def newButtonPressed(self):
        menu = QMenu()

        hardwareMenuAction = hardwareSelectionWidget(self, menu, self.ds)
        menu.addAction(hardwareMenuAction)
        action = menu.exec_(QCursor().pos())

    def addHardware(self, hardwareObj):
        widgetItem = hardwareListItem(self.hardwareList, self.ds, hardwareObj)
        
        self.hardwareList.addWidget(widgetItem)

class hardwareListView(QWidget):

    def __init__(self, parent, ds):
        super().__init__()
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM
        self.parent = parent
        self.hardwareItemList = list()
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.mainLayout.addStretch()

    def addWidget(self, widget):
        self.mainLayout.insertWidget(self.mainLayout.count()-1, widget)

    def removeWidget(self, widget):
        self.mainLayout.removeWidget(widget)

class hardwareListItem(QWidget):
    heightMinimized = 200
    heightMaximized = 400
    state = 'min'

    def __init__(self, hardwareListView, ds, hardwareObj):
        super().__init__()
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM
        self.hardwareListView = hardwareListView
        self.hardwareObj = hardwareObj
        self.msgWidget = driverMessageWidget(self.ds)

        self.configButton = QPushButton()
        self.configIcon = QIcon(os.path.join(self.ds.srcDir, 'icons5\settings.png'))
        self.configButton.setIcon(self.configIcon)
        self.configButton.setIconSize(QSize(16,16))
        self.configButton.pressed.connect(self.showConfigWidget)

        self.statusButton = QPushButton()
        self.statusIconNotReady = QIcon(os.path.join(self.ds.srcDir, 'icons5\warning.png'))
        self.statusIconReady = QIcon(os.path.join(self.ds.srcDir, r'icons5\rotate.png'))
        self.statusButton.setIcon(self.statusIconNotReady)
        self.statusButton.setIconSize(QSize(16,16))
        #self.configButton.pressed.connect(self.showConfigWidget)

        self.infoSection = QWidget()
        self.infoSectionLayout = QVBoxLayout()
        self.infoSectionLayout.addWidget(QLabel(hardwareObj.Get_Standard_Field('hardwareType')))
        self.infoSectionLayout.addWidget(self.configButton)
        self.infoSectionLayout.addWidget(self.statusButton)
        self.infoSectionLayout.addStretch()

        self.infoSection.setLayout(self.infoSectionLayout)

        self.layout = QVBoxLayout()
        self.topPortion = QWidget()
        self.topPortionLayout = QHBoxLayout()
        self.topPortion.setLayout(self.topPortionLayout)
        self.topPortionLayout.addWidget(self.infoSection)
        self.topPortionLayout.addWidget(self.msgWidget)
        self.topPortionLayout.addSpacerItem(QSpacerItem(30, 1))
        self.topPortion.setMaximumHeight(self.heightMinimized-10)
        self.topPortion.setMinimumHeight(self.heightMinimized-10)
        self.closeButtonRect = QRect(0, 0, 0, 0)

        self.botPortion = QWidget()
        self.botPortionLayout = QVBoxLayout()
        self.botPortion.setLayout(self.botPortionLayout)
        self.sourceLabel = QLabel("Sources:")
        self.sourceListWidget = sourceListWidget(self.hardwareObj, self.ds)
        self.botPortionLayout.addWidget(self.sourceLabel)
        self.botPortionLayout.addWidget(self.sourceListWidget)

        self.setLayout(self.layout)
        self.setHeight()
        self.setMaximumHeight(self.heightMinimized)
        self.setMinimumHeight(self.heightMinimized)

        self.minMaxPos = QPointF(self.width()-26, self.heightMinimized-20)
        self.minMaxSize = 12

        self.layout.addWidget(self.topPortion)

        self.hM.Hardware_Scanned.connect(self.hardwareScanned)
        self.hM.Hardware_Initialized.connect(self.hardwareInitialized)
        self.hM.Hardware_Configured.connect(self.hardwareConfigured)
        self.hM.Hardware_Programmed.connect(self.hardwareProgrammed)
        self.hM.Hardware_Soft_Triggered.connect(self.hardwareSoftTriggered)

        self.hM.Hardware_Status_Message.connect(self.hardwareStatusMessage)
        self.hM.Hardware_Ready_Status_Changed.connect(self.hardwareReadyStatusChanged)

        self.hM.Hardware_Programming_Modified.connect(self.programModified)
        self.hM.Hardware_Device_Reset.connect(self.deviceReset)
        self.hM.Hardware_Device_Changed.connect(self.deviceSelectionChanged)
        self.hM.Hardware_Device_Removed.connect(self.deviceSelectionRemoved)
        self.hM.Hardware_Device_Found.connect(self.hardwareDeviceFound)
        self.hM.Source_Added.connect(self.sourceAdded)

        self.hM.Hardware_Handler_Soft_Trigger_Sent.connect(self.hardwareHandlerSoftTriggerSent)

        self.getPreloadInformation()

    def getPreloadInformation(self):
        self.addMsg('[Manager] Manager started.')
        for source in self.hardwareObj.Get_Sources():
            self.sourceAdded(self.hardwareObj, source)

    def sourceRemoved(self, hWare, source):
        if(hWare is self.hardwareObj):
            self.addMsg('[Manager] Source removed: ' + str(source.Get_Name()))

    def sourceAdded(self, hWare, source):
        if(hWare is self.hardwareObj):
            self.addMsg('[Manager] Source added: ' + str(source.Get_Name()))

    def hardwareHandlerSoftTriggerSent(self, hWare):
        if(hWare is self.hardwareObj):
            pass
            #self.addMsg('[Manager] Sent Software Trigger.')

    def hardwareScanned(self, hWare):
        if(hWare is self.hardwareObj):
            self.addMsg('[Hardware] Finished Scanning For Devices.')

    def hardwareInitialized(self, hWare):
        if(hWare is self.hardwareObj):
            self.addMsg('[Hardware] Initialization Finished.')

    def hardwareConfigured(self, hWare):
        if(hWare is self.hardwareObj):
            self.addMsg('[Hardware] Configuration Complete.')

    def hardwareProgrammed(self, hWare):
        if(hWare is self.hardwareObj):
            self.addMsg('[Hardware] Hardware Reprogrammed.')

    def hardwareSoftTriggered(self, hWare):
        if(hWare is self.hardwareObj):
            self.addMsg('[Hardware] Software Triggered.')

    def hardwareStatusMessage(self, hWare, msg):
        if(hWare is self.hardwareObj):
            self.addMsg('[Hardware] Status: ' + msg)

    def hardwareReadyStatusChanged(self, hWare, status):
        if(hWare is self.hardwareObj):
            if(status is True):
                self.statusButton.setIcon(self.statusIconReady)
            else:
                self.statusButton.setIcon(self.statusIconNotReady)
                
    def hardwareDeviceFound(self, hWare, deviceName):
        if(hWare is self.hardwareObj):
            self.addMsg('[Hardware] New Device Found: ' + deviceName)

    def deviceReset(self, hWare):
        if(hWare is self.hardwareObj):
            self.addMsg('[Manager] Device Handler Reset.')
            self.msgWidget.clear()

    def deviceSelectionChanged(self, hWare, deviceName):
        if(hWare is self.hardwareObj):
            self.addMsg('[Manager] Device selected: ' + deviceName)
        
    def deviceSelectionRemoved(self, hWare):
        if(hWare is self.hardwareObj):
            self.addMsg('[Manager] Device selection removed.')

    def programModified(self, hWare, Source):
        if(hWare is self.hardwareObj):
            self.addMsg('[Manager] Programming Data Recieved For: ' + Source.Get_Name())

    def addMsg(self, msg):
        self.msgWidget.addItem(time.strftime('[%m/%d/%Y %H:%M:%S] ') + msg)
        self.msgWidget.setCurrentRow(self.msgWidget.count()-1)

    def setHeight(self):
        if(self.state == 'min'):
            self.setMaximumHeight(self.heightMinimized)
            self.setMinimumHeight(self.heightMinimized)

        if(self.state == 'max'):
            self.setMaximumHeight(self.heightMaximized)
            self.setMinimumHeight(self.heightMaximized)

    def toggleMinMax(self):
        if(self.state == 'min'):
            self.state = 'max'
            self.layout.addWidget(self.botPortion)
        else:
            self.state = 'min'
            self.layout.removeWidget(self.botPortion)

        self.setHeight()

    def closeButton(self):
        self.hM.Remove_Hardware(self.hardwareObj)
        self.setParent(None)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.drawRoundedRect(0, 5, self.width()-5, self.height()-7, 3, 3)

        poly = QPolygonF()
        self.minMaxPos = QPointF(self.width()-26, self.heightMinimized-20)

        if(self.state == 'max'):
            poly.append(self.minMaxPos + QPointF(self.minMaxSize/2, 0))
            poly.append(self.minMaxPos + QPointF(0, self.minMaxSize))
            poly.append(self.minMaxPos + QPointF(self.minMaxSize, self.minMaxSize))
            poly.append(self.minMaxPos + QPointF(self.minMaxSize/2, 0))
        if(self.state == 'min'):
            poly.append(self.minMaxPos + QPointF(0, 0))
            poly.append(self.minMaxPos + QPointF(self.minMaxSize/2, self.minMaxSize))
            poly.append(self.minMaxPos + QPointF(self.minMaxSize, 0))
            poly.append(self.minMaxPos + QPointF(0, 0))

        painter.drawPolygon(poly)

        closeButtonSize = 12
        self.closeButtonRect = QRect(self.width()-closeButtonSize-16, closeButtonSize+6, closeButtonSize, closeButtonSize)
        painter.drawRect(self.closeButtonRect)
        painter.drawLine(self.closeButtonRect.topLeft()+QPoint(2, 2), self.closeButtonRect.bottomRight()-QPoint(1, 1))
        painter.drawLine(self.closeButtonRect.topRight()-QPoint(1, -2), self.closeButtonRect.bottomLeft()+QPoint(2, -1))

        super().paintEvent(e)

    def showConfigWidget(self):
        menu = QMenu()
        hardwareConfig = QWidgetAction(self.ds)
        hardwareConfig.setDefaultWidget(hardwareConfigWidget(self.hardwareObj))
        menu.addAction(hardwareConfig)

        action = menu.exec_(QCursor().pos())
        #self.hardwareObj.Show_Config_Widget(cursor.pos())

    def mousePressEvent(self, e):
        #check if min/max pressed
        minMaxRect = QRectF(self.minMaxPos.x(), self.minMaxPos.y(), self.minMaxSize, self.minMaxSize)
        if(minMaxRect.contains(e.pos())):
            self.toggleMinMax()
            return
        
        if(self.closeButtonRect.contains(e.pos())):
            self.closeButton()
            return

class hardwareSelectionWidget(QWidgetAction):
    def __init__(self, parent, menu, ds):
        super().__init__(None)
        self.parent = parent
        self.menu = menu
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM
        self.pWidget = QWidget()
        self.pLayout = QVBoxLayout()
        self.pSpinBox = QListWidget()
        self.pSpinBox.itemClicked.connect(self.itemClicked)
        self.pLayout.addWidget(self.pSpinBox)
        self.pWidget.setLayout(self.pLayout)

        self.setDefaultWidget(self.pWidget)

        self.populateBox()

    def itemClicked(self):
        curItem = self.pSpinBox.currentItem()
        self.parent.hM.Add_Hardware(curItem.hardwareModel)
        self.menu.close()

    def populateBox(self):
        for hardwareModel in self.parent.hM.Get_Hardware_Models_Available():
            self.pSpinBox.addItem(hardwareSelectionItem(hardwareModel.hardwareType, hardwareModel))

class hardwareSelectionItem(QListWidgetItem):
    def __init__(self, name, hardwareModel):
        super().__init__(name)
        self.name = name
        self.hardwareModel = hardwareModel

class sourceListWidget(QListWidget):
    def __init__(self, hardwareObj, ds):
        super().__init__()
        self.hardwareObj = hardwareObj
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM

        self.hM.Source_Added.connect(self.addSource)
        self.hM.Source_Removed.connect(self.removeSource)
        self.getPreLoadedSources()

    def getPreLoadedSources(self):
        for source in self.hardwareObj.Get_Sources():
            self.addSource(self.hardwareObj, source)

    def addSource(self, hardwareObj, source):
        if(hardwareObj is self.hardwareObj):
            self.addItem(sourceListItem(source, self.ds))

    def removeSource(self, hardwareObj, source):
        removeRow = None
        for i in range(self.count()):
            rowItem = self.item(i)
            if(rowItem.source is source):
                removeRow = i
        if(removeRow is not None):
            self.takeItem(removeRow)

class sourceListItem(QListWidgetItem):
    def __init__(self, source, ds):
        super().__init__()
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM
        self.source = source
        self.setText(self.source.Get_Name())
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

class driverMessageWidget(QListWidget):
    def __init__(self, ds):
        super().__init__()
        self.ds = ds
        self.iM = ds.iM
        self.hM = ds.hM
        self.wM = ds.wM
        self.maximumHeight = 150

class hardwareConfigWidget(QWidget):
    def __init__(self, deviceHandler):
        super().__init__()
        self.deviceHandler = deviceHandler
        configLayout = QVBoxLayout()
        self.setLayout(configLayout)
        self.setMinimumWidth(200)

        hardwareConfig = QWidget()

        layout = QFormLayout()
        hardwareConfig.setLayout(layout)

        deviceSelection = QComboBox()
        deviceSelection.addItem('')
        index = 0
        for item in self.deviceHandler.Get_Available_Devices():
            index = index + 1
            deviceSelection.addItem(item)
            if(item == deviceHandler.Get_Standard_Field('deviceName')):
                deviceSelection.setCurrentIndex(index)
        #Doing this after solved the issue of rebuilding the instrument every time widget was shown
        deviceSelection.currentTextChanged.connect(self.deviceSelectionChanged)
        layout.addRow("Device:", deviceSelection)

        configLayout.addWidget(hardwareConfig)

    def deviceSelectionChanged(self, newSelection):
        self.deviceHandler.Load_Device(newSelection)

