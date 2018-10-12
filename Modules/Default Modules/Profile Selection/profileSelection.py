from PyQt5.Qt import *
import PyQt5.QtCore as QtCore
import json as json
import os
from src.Constants import DSConstants as DSConstants
from pathlib import Path
import time
from src.Managers.ModuleManager.DSModule import DSModule
from src.Constants import moduleFlags as mfs

class profileSelection(DSModule):
    Module_Name = 'Profile Selection'
    Module_Flags = [mfs.SINGLE_INSTANCE, mfs.DEFAULT_MODULE, mfs.CAN_FLOAT]

    def __init__(self, ds, handler):
        super().__init__(ds, handler)
        self.userProfiles = []
        self.ds = ds
        self.profilePathFolder = os.path.join(self.modDataPath, 'Profiles')

        self.setWindowFlags(self.windowFlags() & QtCore.Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)
        self.loginContainer = QWidget()
        self.loginLayout = QVBoxLayout()
        self.userList = QListWidget()
        self.activeUser = None

        self.buttonWidget = QWidget()
        self.buttonLayout = QHBoxLayout()
        self.newButton = QPushButton("New")
        self.editButton = QPushButton("Edit")
        self.acceptButton = QPushButton("Accept")

        self.loginLayout.addWidget(self.userList)
        self.buttonLayout.addWidget(self.newButton)
        self.buttonLayout.addWidget(self.editButton)
        self.buttonLayout.addWidget(self.acceptButton)
        self.buttonWidget.setLayout(self.buttonLayout)
        self.loginLayout.addWidget(self.buttonWidget)
        self.loginLayout.setSpacing(0)

        self.newUserPopup = newProfileDockWidget(self, None)
        self.newButton.pressed.connect(self.showNewUserPopup)
        self.editButton.pressed.connect(self.showEditUserPopup)
        
        self.acceptButton.setEnabled(False)
        self.acceptButton.pressed.connect(self.finish)
        self.editButton.setEnabled(False)

        self.loginContainer.setLayout(self.loginLayout)
        self.setWidget(self.loginContainer)

        self.userList.itemClicked.connect(self.profileSelectionChanged)
        self.userList.itemDoubleClicked.connect(self.profileDoubleClicked)

        self.userList.setSelectionMode(QAbstractItemView.SingleSelection)

        self.populateUserProfiles()

        self.ds.DataStation_Loaded.connect(self.showWidget)
        self.ds.DataStation_Closing.connect(self.updateUserProfile)

    def configureWidget(self, window):
        self.window = window
        self.hide()

    def showWidget(self):
        self.setFloating(True)
        self.resize(400, 400)
        self.show()
        self.center()

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def showNewUserPopup(self):
        self.newUserPopup.loadSettings(None)

    def showEditUserPopup(self):
        self.newUserPopup.loadSettings(self.userProfiles[self.userList.currentRow()])

    def populateUserProfiles(self):
        self.ds.postLog('Loading User Profiles... ', DSConstants.LOG_PRIORITY_HIGH)
        self.userList.clear()
        self.userProfiles = []

        for root, dirs, files in os.walk(self.profilePathFolder):
            for name in files:
                url = os.path.join(root, name)
                userProfile = self.loadUserProfile(url)
                if (userProfile != None):
                    self.userProfiles.append(userProfile)
                    self.userList.addItem(userProfile['Last Name'] + ', ' + userProfile['First Name'])

        self.profileSelectionChanged(-1)
        self.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=True)
    
    def loadUserProfile(self, url): # 'First Name' and 'Last Name' are the only required fields.
        with open(url, 'r') as file:
            try:
                profileData = json.load(file)
                if(isinstance(profileData, dict)):
                    if(('First Name' in profileData) and ('Last Name' in profileData)):
                        profileData['url'] = url
                        return profileData
            except ValueError as e:
                self.ds.postLog('Corrupted user profile at (' + url + ')!! ', DSConstants.LOG_PRIORITY_MED)

        return None

    def profileDoubleClicked(self, e):
        self.profileSelectionChanged(self.userList.currentRow())
        self.finish()

    def profileSelectionChanged(self, row):
        if(len(self.userList.selectedItems()) > 0):
            self.acceptButton.setEnabled(True)
            self.editButton.setEnabled(True)
        else:
            self.acceptButton.setEnabled(False)
            self.editButton.setEnabled(False)

    def updateUserProfile(self):
        if(self.activeUser is not None):
            self.ds.postLog('Updating User Profile... (' + self.activeUser['url'] + ').. ', DSConstants.LOG_PRIORITY_HIGH)     
            self.activeUser['windowStates'] = self.ds.mM.Save_Window_States()    
            with open(self.activeUser['url'], 'w') as file:
                json.dump(self.activeUser, file)
                time.sleep(1) #NOT ELEGANT - NEED CROSS PLATFORM SOLUTION   

    def setActiveUser(self):
        self.activeUser = self.userProfiles[self.userList.currentRow()]
        if('windowStates' in self.activeUser):
            self.ds.mM.Load_Window_States(self.activeUser['windowStates'])
        else:
            self.ds.mM.Load_Window_States(list())

    def finish(self):
        self.setActiveUser()
        self.ds.mM.Hide_Main_Window()
        self.hide()

class newProfileDockWidget(QDockWidget):
    def __init__(self, loginWindow, profileData):
        if(profileData is None):
            super().__init__("New User Profile")
        else:
            super().__init__("Edit User Profile")
        self.loginWindow = loginWindow
        self.hide()
        self.setWindowFlags(self.windowFlags() & QtCore.Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)
        self.newProfileContainer = QWidget()
        self.newProfileLayout = QVBoxLayout()
        self.profileSettingsWidget = QWidget()
        self.profileSettings = QFormLayout()
        self.buttonSectionWidget = QWidget()
        self.buttonSection = QHBoxLayout()
        self.buttonSectionWidget.setLayout(self.buttonSection)

        self.acceptButton = QPushButton("Accept")
        self.acceptButton.pressed.connect(self.AcceptButton)
        self.acceptButton.setEnabled(False)
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.pressed.connect(self.CancelButton)
        self.buttonSection.addWidget(self.cancelButton)
        self.buttonSection.addWidget(self.acceptButton)

        self.profileSettingsWidget.setLayout(self.profileSettings)
        self.firstNameBox = QLineEdit()
        self.firstNameBox.textChanged.connect(self.validateInput)
        self.lastNameBox = QLineEdit()
        self.lastNameBox.textChanged.connect(self.validateInput)
        self.associationBox = QLineEdit()

        self.profileSettings.addRow("First Name*:", self.firstNameBox)
        self.profileSettings.addRow("Last Name*:", self.lastNameBox)
        self.profileSettings.addRow("Association:", self.associationBox)

        self.newProfileLayout.addWidget(self.profileSettingsWidget)
        self.newProfileContainer.setLayout(self.newProfileLayout)
        self.newProfileLayout.addWidget(self.buttonSectionWidget)
        self.setWidget(self.newProfileContainer)

    def loadSettings(self, profileData):
        self.profileData = profileData
        if(self.profileData is None):
            self.setWindowTitle('New User Profile')
            self.firstNameBox.setText('')
            self.lastNameBox.setText('')
            self.associationBox.setText('')
        else:
            self.setWindowTitle('Edit User Profile')
            self.firstNameBox.setText(self.profileData['First Name'])
            self.lastNameBox.setText(self.profileData['Last Name'])
            if('Association' in self.profileData):
                self.associationBox.setText(self.profileData['Association'])
            else:
                self.associationBox.setText('')
        self.show()

    def validateInput(self):
        if((len(self.firstNameBox.text()) >= 3) and (len(self.lastNameBox.text()) >= 3)):
            self.acceptButton.setEnabled(True)
            return True
        else:
            self.acceptButton.setEnabled(False)
            return False

    def CancelButton(self):
        self.hide()

    def AcceptButton(self):
        userProfile = dict([('First Name', self.firstNameBox.text()), ('Last Name', self.lastNameBox.text())])
        userProfile['Association'] = self.associationBox.text()
        savePath = os.path.join(self.loginWindow.profilePathFolder, userProfile['Last Name'] + '_' + userProfile['First Name'])
        savePathAppend = savePath + '.dsprofile'
        num = 1
        while(os.path.isfile(savePathAppend)):
            savePathAppend = savePath + str(num) + '.dsprofile'
            num = num + 1
        self.loginWindow.ds.postLog('Writing User Profile... (' + savePathAppend + ').. ', DSConstants.LOG_PRIORITY_HIGH)
        if(self.profileData is None):
            with open(savePathAppend, 'w') as file:
                json.dump(userProfile, file)
        else:
            if(os.path.exists(self.profileData['url'])):
                os.remove(self.profileData['url'])
            with open(savePathAppend, 'w') as file:
                json.dump(userProfile, file)
        self.loginWindow.ds.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

        self.loginWindow.populateUserProfiles()
        self.hide()
    
