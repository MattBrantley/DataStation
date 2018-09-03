from PyQt5.Qt import *
import PyQt5.QtCore as QtCore
import json as json
import os
from Constants import DSConstants as DSConstants
from pathlib import Path
import time

class loginDockWidget(QDockWidget):
    def __init__(self, mW):
        super().__init__("Select User Profile")
        self.userProfiles = []
        self.mW = mW
        self.profilePathFolder = os.path.join(str(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent), 'User Profiles')

        self.setWindowFlags(self.windowFlags() & QtCore.Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint)
        self.loginContainer = QWidget()
        self.loginLayout = QVBoxLayout()
        self.userList = QListWidget()

        self.buttonWidget = QWidget()
        self.buttonLayout = QHBoxLayout()
        self.newButton = QPushButton("New")
        self.editButton = QPushButton("Edit")
        self.acceptButton = QPushButton("Accept")
        self.mW = mW

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
        self.acceptButton.pressed.connect(self.finishModal)
        self.editButton.setEnabled(False)

        self.loginContainer.setLayout(self.loginLayout)
        self.setWidget(self.loginContainer)

        #self.userList.currentRowChanged.connect(self.profileSelectionChanged)
        self.userList.itemClicked.connect(self.profileSelectionChanged)
        self.userList.itemDoubleClicked.connect(self.profileDoubleClicked)

        self.userList.setSelectionMode(QAbstractItemView.SingleSelection)

        self.populateUserProfiles()

    def runModal(self):
        self.show()

    def finishModal(self):
        self.hide()
        self.mW.finishInitWithUser(self.userProfiles[self.userList.currentRow()])

    def showNewUserPopup(self):
        self.newUserPopup.loadSettings(None)

    def showEditUserPopup(self):
        self.newUserPopup.loadSettings(self.userProfiles[self.userList.currentRow()])

    def populateUserProfiles(self):
        self.mW.postLog('Loading User Profiles... ', DSConstants.LOG_PRIORITY_HIGH)
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
        self.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=True)
    
    def loadUserProfile(self, url): # 'First Name' and 'Last Name' are the only required fields.
        with open(url, 'r') as file:
            try:
                profileData = json.load(file)
                if(isinstance(profileData, dict)):
                    if(('First Name' in profileData) and ('Last Name' in profileData)):
                        profileData['url'] = url
                        return profileData
            except ValueError as e:
                self.mW.postLog('Corrupted user profile at (' + url + ')!! ', DSConstants.LOG_PRIORITY_MED)

        return None

    def profileDoubleClicked(self, e):
        self.profileSelectionChanged(self.userList.currentRow())
        self.finishModal()

    def profileSelectionChanged(self, row):
        if(len(self.userList.selectedItems()) > 0):
            self.acceptButton.setEnabled(True)
            self.editButton.setEnabled(True)
        else:
            self.acceptButton.setEnabled(False)
            self.editButton.setEnabled(False)

    def closeEvent(self, event):
        self.mW.postLog('No User Profile selected...', DSConstants.LOG_PRIORITY_HIGH)
        self.mW.signalClose()
        event.accept()

    def updateUserProfile(self):
        if(any(self.mW.workspaceManager.userProfile) and ('url' in self.mW.workspaceManager.userProfile)):
            self.mW.postLog('Updating User Profile... (' + self.mW.workspaceManager.userProfile['url'] + ').. ', DSConstants.LOG_PRIORITY_HIGH)        
            with open(self.mW.workspaceManager.userProfile['url'], 'w') as file:
                json.dump(self.mW.workspaceManager.userProfile, file)
                time.sleep(1) #NOT ELEGANT - NEED CROSS PLATFORM SOLUTION
        else:
            self.mW.postLog('Error Updating User Profile or No Profile Loaded.', DSConstants.LOG_PRIORITY_HIGH)        

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
        self.loginWindow.mW.postLog('Writing User Profile... (' + savePathAppend + ').. ', DSConstants.LOG_PRIORITY_HIGH)
        if(self.profileData is None):
            with open(savePathAppend, 'w') as file:
                json.dump(userProfile, file)
        else:
            if(os.path.exists(self.profileData['url'])):
                os.remove(self.profileData['url'])
            with open(savePathAppend, 'w') as file:
                json.dump(userProfile, file)
        self.loginWindow.mW.postLog('Done!', DSConstants.LOG_PRIORITY_HIGH, newline=False)

        self.loginWindow.populateUserProfiles()
        self.hide()
    
