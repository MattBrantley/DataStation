from PyQt5.Qt import *
import PyQt5.QtCore as QtCore

class loginDockWidget(QDockWidget):
    def __init__(self, mainWindow):
        super().__init__("Select User Profile")
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
        self.mainWindow = mainWindow

        self.loginLayout.addWidget(self.userList)
        self.buttonLayout.addWidget(self.newButton)
        self.buttonLayout.addWidget(self.editButton)
        self.buttonLayout.addWidget(self.acceptButton)
        self.buttonWidget.setLayout(self.buttonLayout)
        self.loginLayout.addWidget(self.buttonWidget)
        self.loginLayout.setSpacing(0)

        self.newUserPopup = newProfileDockWidget("New User Profile..", None)
        self.newButton.pressed.connect(self.showNewUserPopup)
        
        self.acceptButton.setEnabled(False)
        self.editButton.setEnabled(False)

        self.show()

        self.loginContainer.setLayout(self.loginLayout)
        self.setWidget(self.loginContainer)

    def showNewUserPopup(self):
        self.newUserPopup.loadSettings(None)


class newProfileDockWidget(QDockWidget):
    def __init__(self, loginWindow, profileData):
        if(profileData is None):
            super().__init__("New User Account")
        else:
            super().__init__("Edit User Account")
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
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.pressed.connect(self.CancelButton)
        self.buttonSection.addWidget(self.cancelButton)
        self.buttonSection.addWidget(self.acceptButton)

        self.profileSettingsWidget.setLayout(self.profileSettings)
        self.firstNameBox = QLineEdit()
        self.lastNameBox = QLineEdit()

        self.profileSettings.addRow("First Name:", self.firstNameBox)
        self.profileSettings.addRow("Last Name:", self.lastNameBox)

        self.newProfileLayout.addWidget(self.profileSettingsWidget)
        self.newProfileContainer.setLayout(self.newProfileLayout)
        self.newProfileLayout.addWidget(self.buttonSectionWidget)
        self.setWidget(self.newProfileContainer)

    def loadSettings(self, profileData):
        self.show()

    def CancelButton(self):
        self.hide()

    def AcceptButton(self):
        #Do Stuff
        self.hide()
    
