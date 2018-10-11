from PyQt5.Qt import *
from PyQt5.QtCore import *
import pyqtgraph as pg # This library gives a bunch of FutureWarnings that are unpleasant! Fix for this is in the main .py file header.
import os
from shutil import copyfileobj
import numpy as np
import random
from src.Constants import DSConstants as DSConstants
from PyQt5.QtGui import *
from shutil import copyfile
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class instrumentEditor(DSModule):
    Module_Name = 'Instrument Editor'
    Module_Flags = []

    def __init__(self, ds):
        super().__init__(ds)
        self.ds = ds
        self.iM = ds.iM
        self.resize(1000, 800)
        self.fileSystem = DSEditorFSModel()
        self.rootPath = os.path.join(self.ds.rootDir, 'Instruments')
        self.fsIndex = self.fileSystem.setRootPath(self.rootPath)

        self.toolbar = QToolBar()
        
        self.mainContainer = QMainWindow()
        self.mainContainer.addToolBar(self.toolbar)
        self.instrumentContainer = QSplitter()
        self.toolWidgets = QTabWidget()
        
        self.instrumentNavigator = DSTreeView(self, self.fileSystem)
        self.componentList = componentsList(self, self.ds)

        self.instrumentView = iView(self)

        self.initInstrumentNavigator()
        self.initActions()
        self.initToolbar()

        self.toolWidgets.addTab(self.instrumentNavigator, "Instruments")
        self.toolWidgets.addTab(self.componentList, "Component Pallet")
        self.instrumentContainer.addWidget(self.toolWidgets)
        self.instrumentContainer.addWidget(self.instrumentView)

        self.instrumentContainer.setStretchFactor(1, 3)
        self.setWidget(self.mainContainer) 
        self.mainContainer.setCentralWidget(self.instrumentContainer)
        self.updateToolbarState()

        self.iM.Instrument_Unloaded.connect(self.updateTitle)
        self.iM.Instrument_Loaded.connect(self.updateTitle)
        self.iM.Instrument_Config_Changed.connect(self.updateTitle)

    def initToolbar(self):
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.saveAsAction)
        
        self.toolbar.addSeparator()

        self.toolbar.addWidget(self.toolToggle)
        self.toolbar.addWidget(self.lockToggle)
        
    def initInstrumentNavigator(self):
        self.instrumentNavigator.setModel(self.fileSystem)
        self.instrumentNavigator.setDragEnabled(True)
        self.instrumentNavigator.setAcceptDrops(True)
        self.instrumentNavigator.setDefaultDropAction(Qt.MoveAction)
        self.instrumentNavigator.setRootIndex(self.fsIndex)
        self.instrumentNavigator.doubleClicked.connect(self.doubleClicked)
        self.instrumentNavigator.hideColumn(1)
        self.instrumentNavigator.hideColumn(2)
        self.instrumentNavigator.hideColumn(3)

    def new(self):
        self.ds.postLog('Creating new instrument', DSConstants.LOG_PRIORITY_HIGH)
        fname, ok = QInputDialog.getText(self.ds, "Virtual Instrument Name", "Virtual Instrument Name")
        if(ok):
            self.iM.New_Instrument(name=fname, path=self.rootPath)
        else:
            return
        self.updateTitle()

    def updateTitle(self):
        if(self.iM.Get_Instrument() is not None):
            self.setWindowTitle('Instrument View (' + self.iM.Get_Instrument().Get_Name() + ')')
        else:
            self.setWindowTitle('Instrument View (None)')

    def save(self):
        savePath = None
        item = self.instrumentNavigator.selectionModel().selectedIndexes()
        if(len(item) > 0):
            savePath = self.instrumentNavigator.model.filePath(item[0])
        else:
            savePath = self.rootPath

        self.iM.Save_Instrument(path=savePath)

        if(self.iM.Get_Instrument().Get_Path is None):
            self.saveAsInstrument(savePath)
        else:
            self.saveInstrument(savePath)

    def saveAs(self):
        savePath = None
        item = self.instrumentNavigator.selectionModel().selectedIndexes()
        if(len(item) > 0):
            savePath = self.instrumentNavigator.model.filePath(item[0])
        else:
            savePath = self.rootPath
        self.saveAsInstrument(savePath)

    def saveAsInstrument(self, savePath):
        fname, ok = QInputDialog.getText(self.ds, "Virtual Instrument Name", "Virtual Instrument Name")
        checkPath = os.path.join(savePath, fname + '.dsinstrument')
        if(ok):
            pass
        else:
            return

        if(os.path.exists(checkPath)):
            reply = QMessageBox.question(self.ds, 'File Warning!', 'File exists - overwrite?', QMessageBox.Yes, QMessageBox.No)
            if(reply == QMessageBox.No):
                return

        self.iM.Save_Instrument(name=fname, path=savePath)

    def saveInstrument(self, savePath):
        if(self.iM.Get_Instrument().Get_Name() == 'Default Instrument'):
            fname, ok = QInputDialog.getText(self.ds, "Virtual Instrument Name", "Virtual Instrument Name")
            if(ok):
                self.iM.Get_Instruemnt().Set_Name(fname)
            else:
                return

        self.iM.Save_Instrument()

    def initActions(self):
        self.newAction = QAction('New', self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.setStatusTip('New')
        self.newAction.triggered.connect(self.new)

        self.saveAction = QAction('Save', self)
        self.saveAction.setStatusTip('Save')
        self.saveAction.triggered.connect(self.save)

        self.saveAsAction = QAction('Save As', self)
        self.saveAsAction.setStatusTip('Save As')
        self.saveAsAction.triggered.connect(self.saveAs)

        self.toolToggle = QToolButton(self)
        self.toolToggle.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons3\cogwheels.png')))
        self.toolToggle.setCheckable(True)
        self.toolToggle.setStatusTip('Show/Hide Tools')
        self.toolToggle.toggled.connect(self.toolsToggled)
        self.toolToggle.toggle()

        self.lockToggle = QToolButton(self)
        self.lockToggle.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons2\padlock.png')))
        self.lockToggle.setCheckable(True)
        self.lockToggle.setStatusTip('Show/Hide Tools')
        self.lockToggle.toggled.connect(self.lockToggled)
        self.lockToggle.toggle()

    def toolsToggled(self, checked):
        if(checked):
            self.toolWidgets.show()
        else:
            self.toolWidgets.hide()

    def lockToggled(self, checked):
        if(checked):
            pass
            #self.instrumentView.setDragEnabled(False)
            #self.instrumentView.setAcceptDrops(False)
        else:
            pass
            #self.instrumentView.setDragEnabled(True)
            #self.instrumentView.setAcceptDrops(True)

    def doubleClicked(self, index):
        item = self.fileSystem.fileInfo(index)
        filePath = item.filePath()
        fileExt = os.path.splitext(item.fileName())[1]
        if(fileExt == '.sqpy'):
            self.openInstrument(filePath)

    def openInstrument(self, filePath):
        self.iM.Load_Instrument(filePath)
        self.updateTitle()

    def updateToolbarState(self):
        self.saveAction.setEnabled(True)
        self.saveAsAction.setEnabled(True)

class componentsList(QListWidget):
    def __init__(self, widget, ds, parent=None):
        super(componentsList, self).__init__(None)

        self.ds = ds
        self.iM = ds.iM
        self.setDragEnabled(True)
        self.setViewMode(QListView.ListMode)
        self.setIconSize(QSize(60, 60))
        self.setSpacing(10)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(True)
        self.populateList()

    def mouseMoveEvent(self, e):
        mimeData = QMimeData()
        mimeData.setText("compDrag")
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)
        if(self.itemAt(e.pos()) is not None):
            stream.writeQString(self.itemAt(e.pos()).text())
        else:
            return
        data2 = QByteArray()
        stream2 = QDataStream(data2, QIODevice.WriteOnly)
        stream2.writeInt(self.selectedIndexes()[0].row())
        mimeData.setData("application/compName", data)
        mimeData.setData("application/compIndex", data2)
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        dropAction = drag.exec_()

    def populateList(self):
        for val in self.iM.Get_Component_Models_Available():
            tempIcon = QIcon(os.path.join(self.ds.rootDir, 'Components\img\\' + val.iconGraphicSrc))
            self.addItem(componentItem(tempIcon, val.componentType))

class componentItem(QListWidgetItem):
    def __init__(self, icon, text):
        super().__init__(None)
        self.setText(text)
        self.setIcon(icon)
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

class DSNewFileDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.scriptType = QComboBox()
        self.scriptType.setWindowTitle('New Instrument..')
        self.scriptType.addItem('Display')
        self.scriptType.addItem('Export')
        self.scriptType.addItem('Generator')
        self.scriptType.addItem('Import')
        self.scriptType.addItem('Interact')
        self.scriptType.addItem('Operation')

        self.layout.addWidget(self.scriptType)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    @staticmethod
    def newFile():
        dialog = DSNewFileDialog()
        result = dialog.exec_()
        return (result == QDialog.Accepted)

class DSEditorFSModel(QFileSystemModel):
    def __init__(self):
        super().__init__()
        self.setReadOnly(False)
        self.setNameFilters({'*.dsinstrument'})

    def headerData(self, section, orientation, role):
        if section == 0 and role == Qt.DisplayRole:
            return "Instruments"
        else:
            return super(QFileSystemModel, self).headerData(section, orientation, role)

class DSTreeView(QTreeView):
    def __init__(self, parent, model):
        super().__init__()
        self.parent = parent
        self.model = model
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.rightClick)

    def mousePressEvent(self, event):
        self.clearSelection()
        event.accept()
        QTreeView.mousePressEvent(self, event)

    def rightClick(self, point):
        idx = self.mapToGlobal(point)

        item = self.selectionModel().selectedIndexes()
        if(len(item) > 0):
            if(os.path.isdir(self.model.filePath(item[0]))):        #Show different menu on folders
                newInstrumentAction = QAction('New Instrument', self)
                newInstrumentAction.triggered.connect(lambda: self.newInstrumentAction(self.model.filePath(item[0])))

                newFolderAction = QAction('New Folder', self)
                newFolderAction.triggered.connect(lambda: self.newFolderAction(self.model.filePath(item[0])))
                
                menu = QMenu(self)
                menu.addAction(newInstrumentAction)
                menu.addAction(newFolderAction)
                menu.exec(idx)
            else:                                                   #Show this menu for non-folder items
                openInstrumentAction = QAction('Open', self)
                openInstrumentAction.triggered.connect(lambda: self.openInstrumentAction(self.model.filePath(item[0])))

                newInstrumentAction = QAction('New Instrument', self)
                newInstrumentAction.triggered.connect(lambda: self.newInstrumentAction(self.model.filePath(item[0])))

                newFolderAction = QAction('New Folder', self)
                newFolderAction.triggered.connect(lambda: self.newFolderAction(self.model.filePath(item[0])))
                
                deleteAction = QAction('Delete', self)
                deleteAction.triggered.connect(lambda: self.delete(self.model.filePath(item[0])))

                duplicateAction = QAction('Duplicate', self)
                duplicateAction.triggered.connect(lambda: self.duplicate(self.model.filePath(item[0])))

                menu = QMenu(self)
                menu.addAction(openInstrumentAction)
                menu.addSeparator()
                menu.addAction(newInstrumentAction)
                menu.addAction(newFolderAction)
                menu.addAction(deleteAction)
                #menu.addAction(duplicateAction)
                menu.exec(idx)
        else:                                                       #Show this menu for non-items
            newInstrumentAction = QAction('New Instrument', self)
            newInstrumentAction.triggered.connect(lambda: self.newInstrumentAction(self.parent.rootPath))

            newFolderAction = QAction('New Folder', self)
            newFolderAction.triggered.connect(lambda: self.newFolderAction(self.parent.rootPath))
            
            menu = QMenu(self)
            menu.addAction(newInstrumentAction)
            menu.addAction(newFolderAction)
            menu.exec(idx)

    def openInstrumentAction(self, item):
        self.parent.openInstrument(item)

    def newInstrumentAction(self, item):
        print(item)

    def newFolderAction(self, item):
        print(item)

    def delete(self, item):
        os.remove(item)

    def duplicate(self, item):
        tempPath = os.path.splitext(item)[0] + '_copy' + os.path.splitext(item)[1]
        tempNum = 1
        while(os.path.isfile(tempPath)):
            tempNum = tempNum + 1
            tempPath = os.path.splitext(item)[0] + '_copy' + str(tempNum) + os.path.splitext(item)[1]

        copyfile(item, tempPath)

class iView(pg.GraphicsWindow):
    def __init__(self, instrumentWidget, parent=None):
        super(iView, self).__init__(parent)

        self.instrumentWidget = instrumentWidget
        self.ds = instrumentWidget.ds
        self.iM = instrumentWidget.ds.iM
        self.setAcceptDrops(True)
        self.view = self.addViewBox()
        self.view.setAspectLocked()
        self.view.setRange(pg.QtCore.QRectF(0, 0, 2000, 2000))
        self.view.Antialiasing = True
        self.setBackground('w')
        self.iM.Instrument_Saving.connect(self.updateiViewState)

        self.iViewCompList = list()

        self.iM.Component_Added.connect(self.addiViewComp)
        self.iM.Component_Removed.connect(self.removeiViewComp)

    def updateiViewState(self):
        for item in self.iViewCompList:
            item.instrComp.Set_Custom_Field('iViewSettings', item.onSave())

    def dragEnterEvent(self, e):
        if(e.mimeData().text() == "compDrag"):
            e.accept()

    def dragMoveEvent(self, e):
        if(e.mimeData().text() == "compDrag"):
            e.accept()

    def dropEvent(self, e):
        windowXSize = self.viewRect().width()
        windowYSize = self.viewRect().height()
        dropXPercent = (e.pos().x()-self.viewRect().left())/windowXSize
        dropYPercent = (e.pos().y()-self.viewRect().top())/windowYSize
        dropX = (dropXPercent*self.view.viewRect().width()) + self.view.viewRect().left()
        dropY = self.view.viewRect().bottom() - (dropYPercent*self.view.viewRect().height())

        data = e.mimeData().data("application/compName")
        data2 = e.mimeData().data("application/compIndex")
        stream = QDataStream(data, QIODevice.ReadOnly)
        stream2 = QDataStream(data2, QIODevice.ReadOnly)
        text = stream.readQString()
        index = stream2.readInt()

        tempCustomFields = {'iViewSettings': {'x': dropX, 'y': dropY, 'r': 0}}

        self.iM.Add_Component(self.iM.Get_Component_Model_By_Index(index), customFields=tempCustomFields)

    def addiViewComp(self, instrument, component):
        if(component.Get_Standard_Field('triggerComp') is False):
            try:
                ivs = component.Get_Custom_Field('iViewSettings')
                m = iViewComponent(self.ds, component, self, width=1, height=1, pos=(ivs['x'], ivs['y']), angle=ivs['r'])
                self.view.addItem(m)
                self.iViewCompList.append(m)
            except:
                pass

    def removeiViewComp(self, instrument, component):
        for icomp in self.iViewCompList:
            if(icomp.instrComp is component):
                self.view.removeItem(icomp)

class ParamObj:
    # Just a helper for tracking parameters and responding to changes
    def __init__(self):
        self.__params = {}
    
    def __setitem__(self, item, val):
        self.setParam(item, val)
        
    def setParam(self, param, val):
        self.setParams(**{param:val})
        
    def setParams(self, **params):
        """Set parameters for this optic. This is a good function to override for subclasses."""
        self.__params.update(params)
        self.paramStateChanged()

    def paramStateChanged(self):
        pass

    def __getitem__(self, item):
        return self.getParam(item)

    def getParam(self, param):
        return self.__params[param]

class iViewGraphic(pg.GraphicsObject, ParamObj):
    def __init__(self, ds, src, pen=None, brush=None, **opts):
        defaults = dict(width=2, height=2)
        self.ds = ds
        defaults.update(opts)
        ParamObj.__init__(self)
        pg.GraphicsObject.__init__(self)
        
        self.pxm = QPixmap(os.path.join(self.ds.rootDir, 'Components\img\\' + src))
        self.surfaces = [iViewGraphicBound(self.pxm.width(), self.pxm.height())]
        
        if pen is None:
            self.pen = pg.mkPen((220,220,255,200), width=1, cosmetic=True)
        else:
            self.pen = pg.mkPen(pen)
        
        if brush is None: 
            self.brush = pg.mkBrush((230, 230, 255, 30))
        else:
            self.brush = pg.mkBrush(brush)

        self.setParams(**defaults)

    def paramStateChanged(self):
        self.updateSurfaces()

    def updateSurfaces(self):
        self.surfaces[0].setParams(self.pxm.width(), self.pxm.height())
        
        self.path = QPainterPath()
        self.path.connectPath(self.surfaces[0].path.translated(self.surfaces[0].pos()))
        self.path.closeSubpath()
        
    def boundingRect(self):
        return self.path.boundingRect()
        
    def shape(self):
        return self.path
    
    def paint(self, p, *args):
        p.setRenderHints(p.renderHints() | p.Antialiasing)
        p.drawPixmap(0, 0, self.path.boundingRect().width(), self.path.boundingRect().height(), self.pxm)

class iViewGraphicBound(pg.GraphicsObject, ParamObj):
    def __init__(self, width=None, height=None):
        pg.GraphicsObject.__init__(self)
        
        self.width = width 
        self.height = height
        self.mkPath()
    
    def setParams(self, width, height):
        self.width = width
        self.height = height
        self.mkPath()
    
    def mkPath(self):
        self.prepareGeometryChange()
        width = self.width
        height = self.height
        self.path = QPainterPath()
        self.path.addRect(0, 0, width, height)
        
    def boundingRect(self):
        return self.path.boundingRect()
        
    def paint(self, p, *args):
        return 

class iViewObject(pg.GraphicsObject, ParamObj):
    sigStateChanged = pyqtSignal()
    ds = None
    index = 0
    instrComp = None

    def __init__(self, gitem, iView, **params):
        ParamObj.__init__(self)
        pg.GraphicsObject.__init__(self) #, [0,0], [1,1])

        self.gitem = gitem
        self.iView = iView
        gitem.setParentItem(self)
        
        self.roi = pg.ROI([0,0], [1,1], removable=True)
        self.roi.pen = pg.mkPen((0,0,255,0), width=0, cosmetic=True)
        handle = self.roi.addRotateHandle([1, 1], [0.5, 0.5])
        handle.pen = pg.mkPen('r')
        handle.currentPen = handle.pen
        handle.update()

        self.roi.rotateSnap = True
        self.roi.translateSnap = True
        self.roi.setParentItem(self)
        
        defaults = {
            'pos': pg.Point(0,0),
            'angle': 0,
        }
        defaults.update(params)
        self.roi.sigRegionChanged.connect(self.roiChanged)
        self.roi.sigClicked.connect(self.clicked)
        self.roi.setAcceptedMouseButtons(Qt.LeftButton)
        self.roi.sigRemoveRequested.connect(self.removed)
        self.setParams(**defaults)
    
    def removed(self):
        if(self.instrComp is not None):
            self.instrComp.Remove_Component()

    def clicked(self):
        if(self.instrComp is not None):
            self.instrComp.onLeftClick(QCursor.pos())

    def updateTransform(self):
        self.resetTransform()
        self.setPos(0, 0)
        self.translate(Point(self['pos']))
        self.rotate(self['angle'])
        
    def setParam(self, param, val):
        ParamObj.setParam(self, param, val)

    def paramStateChanged(self):
        """Some parameters of the optic have changed."""
        # Move graphics item
        self.gitem.setPos(pg.Point(self['pos']))
        self.gitem.resetTransform()
        self.gitem.rotate(self['angle'])
        
        # Move ROI to match
        try:
            self.roi.sigRegionChanged.disconnect(self.roiChanged)
            br = self.gitem.boundingRect()
            o = self.gitem.mapToParent(br.topLeft())
            self.roi.setAngle(self['angle'])
            self.roi.setPos(o)
            self.roi.setSize([br.width(), br.height()])
        finally:
            self.roi.sigRegionChanged.connect(self.roiChanged)

        self.sigStateChanged.emit()

    def roiChanged(self, *args):
        pos = self.roi.pos()
        # rotate gitem temporarily so we can decide where it will need to move
        self.gitem.resetTransform()
        self.gitem.rotate(self.roi.angle())
        br = self.gitem.boundingRect()
        o1 = self.gitem.mapToParent(br.topLeft())
        self.setParams(angle=self.roi.angle(), pos=pos + (self.gitem.pos() - o1))
        
    def boundingRect(self):
        return QRectF()
        
    def paint(self, p, *args):
        pass

class iViewComponent(iViewObject):
    def __init__(self, ds, instrComp, iView, **params):
        defaults = {
            'width': 1,
            'height': 1,
            'angle' : 180
        }
        self.ds = ds
        self.instrComp = instrComp
        self.iView = iView
        defaults.update(params)
        src = instrComp.compSettings['layoutGraphicSrc']

        self.gitem = iViewGraphic(self.ds, src, brush=(100,100,100,255), **defaults)
        iViewObject.__init__(self, self.gitem, iView, **defaults)

    def onSave(self):
        iViewSaveData = dict()
        iViewSaveData['x'] = self.gitem.pos().x()
        iViewSaveData['y'] = self.gitem.pos().y()
        iViewSaveData['r'] = self.roi.angle()

        return iViewSaveData