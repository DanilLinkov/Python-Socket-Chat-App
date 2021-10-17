import threading
import socket
import argparse
import os
import sys
import select

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from connectionGUI import Ui_ConnectionWindow
from connectedGUI import Ui_Dialog as connectedDialog
from oneOnOneGUI import Ui_oneOnOneWindow as oneOnOneDialog
from groupChatGUI import Ui_groupChat as groupDialog
from inviteGUI import Ui_inviteWindow as inviteDialog
from groupInvitePopup import Ui_Dialog as groupInviteDialog

from Utils import *
from ActionEnum import ActionType


class Receive(QThread):
    newConnectedUsersList = pyqtSignal(object)
    newSingleMessage = pyqtSignal(object, object)
    newGroupsList = pyqtSignal(object)
    newUserListInGroup = pyqtSignal(object)
    newGroupMessage = pyqtSignal(object, object)
    newInviteToGroup = pyqtSignal(object, object)

    def __init__(self, clientInstance):
        QThread.__init__(self)

        self.clientInstance = clientInstance

    def run(self):
        while True:
            readable, writeable, exceptional = select.select(
                [self.clientInstance.clientSocket], [], [])

            # Only one socket which is the client socket so only 1 iteration ever
            for sock in readable:
                if sock == self.clientInstance.clientSocket:
                    serverMessage = receive(sock)

                    if serverMessage:
                        print(serverMessage)

                        messageType = serverMessage[0]

                        if messageType == ActionType.allUsersListUpdate:
                            self.newConnectedUsersList.emit(serverMessage[1])
                        elif messageType == ActionType.receiveMessage:
                            self.newSingleMessage.emit(
                                serverMessage[1], serverMessage[2])
                        elif messageType == ActionType.createRoom:
                            self.newGroupsList.emit(serverMessage[1])
                        elif messageType == ActionType.groupUsersListUpdate:
                            self.newUserListInGroup.emit(serverMessage[1])
                        elif messageType == ActionType.receiveGroup:
                            self.newGroupMessage.emit(
                                serverMessage[1], serverMessage[2])
                        elif messageType == ActionType.invite:
                            self.newInviteToGroup.emit(
                                serverMessage[1], serverMessage[2])

                    else:
                        print("Connection shut down.")
                        break


class Client:
    def __init__(self, host, port, clientName):
        self.host = host
        self.port = port
        self.clientName = clientName

        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        print(f'Attempting to connect to {self.host}:{self.port}...')

        # Connect to the socket given the host address and port
        self.clientSocket.connect((self.host, self.port))

        # Send the server the client's name
        self.sendMessageToServer(self.clientName)

        print(f'Connected to {self.host}:{self.port} as {self.clientName}.')

    def sendMessageToServer(self, messageAsTuple):
        send(self.clientSocket, messageAsTuple)


class groupInvitePopup:
    def __init__(self, mainInstance, parent, fromUser, toGroup):
        self.mainInstance = mainInstance
        self.parent = parent
        self.toGroup = toGroup

        parent.groupInviteGUIWindow = self

        self.groupInviteDialog = QDialog()
        self.groupInviteDialog.ui = groupInviteDialog()
        self.groupInviteDialog.ui.setupUi(self.groupInviteDialog)
        self.groupInviteDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.groupInviteDialog.setWindowFlag(
            Qt.WindowCloseButtonHint, False)

        self.groupInviteDialog.ui.label.setText(
            f"You have an invite from {fromUser}\n To group {toGroup}\n Accept to join or decline to close this popup.")

        self.groupInviteDialog.ui.acceptButton.clicked.connect(
            self.acceptInvite)

        self.groupInviteDialog.ui.declineButton.clicked.connect(
            self.declineInvite)

        self.groupInviteDialog.exec_()

    def acceptInvite(self):
        self.groupInviteDialog.close()
        self.parent.joinGroupFromInvite(self.toGroup)

    def declineInvite(self):
        self.parent.groupInviteGUIWindow = None
        self.groupInviteDialog.close()


class InviteUserGUIWindow:
    def __init__(self, mainInstance, parent):
        self.mainInstance = mainInstance
        self.parent = parent

        parent.inviteUserGUIWindow = self

        self.inviteChatDialog = QDialog()
        self.inviteChatDialog.ui = inviteDialog()
        self.inviteChatDialog.ui.setupUi(self.inviteChatDialog)
        self.inviteChatDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.inviteChatDialog.setWindowFlag(
            Qt.WindowCloseButtonHint, False)

        self.inviteChatDialog.ui.inviteButton.clicked.connect(
            self.onInviteUserClick)

        self.inviteChatDialog.ui.closeButton.clicked.connect(
            self.closeAllWindowsFromThis)

        self.selectedUserToInviteLabel = None
        self.usersNotInTheGroupLabelList = []

        self.updateUserLabels([
            x for x in self.parent.parent.connectedUsersList if x not in self.parent.usersInGroup])

        self.inviteChatDialog.exec_()

    def closeAllWindowsFromThis(self):
        self.parent.inviteUserGUIWindow = None
        self.inviteChatDialog.close()

    def onInviteUserClick(self):
        self.parent.inviteUserGUIWindow = None
        self.closeAllWindowsFromThis()
        # Make client send message to server to invite toUser, groupName
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.invite, self.selectedUserToInviteLabel.text(), self.parent.groupName))

    def onSingleUserLabelClick(self, label):
        self.selectedUserToInviteLabel = label

    def updateUserLabels(self, newUserList):
        self.clearLayout(self.inviteChatDialog.ui.inviteListWidget)
        self.usersNotInTheGroupLabelList = []

        for user in newUserList:
            self.inviteChatDialog.ui.inviteListWidget.addItem(user)

        self.inviteChatDialog.ui.inviteListWidget.itemClicked.connect(
            self.onSingleUserLabelClick)

    def clearLayout(self, layoutToClear):
        layoutToClear.clear()


class GroupChatGUIWindow:
    def __init__(self, mainInstance, parent, groupName):
        self.mainInstance = mainInstance
        self.groupName = groupName

        self.parent = parent

        parent.groupChatGUIWindow = self

        self.groupChatDialog = QDialog()
        self.groupChatDialog.ui = groupDialog()
        self.groupChatDialog.ui.setupUi(self.groupChatDialog)
        self.groupChatDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.groupChatDialog.setWindowFlag(
            Qt.WindowCloseButtonHint, False)

        self.usersInGroupLabelList = []
        self.usersInGroup = []

        self.inviteUserGUIWindow = None

        self.groupChatDialog.ui.sendButton_2.clicked.connect(
            self.onSendGroupMessageButtonClick)

        self.groupChatDialog.ui.sendButton_3.clicked.connect(
            self.onInviteClick)

        self.groupChatDialog.ui.closeButton_2.clicked.connect(
            self.closeAllWindowsFromThis)

        self.groupChatDialog.exec_()

    def closeAllWindowsFromThis(self):
        if self.inviteUserGUIWindow is not None:
            # call its close
            self.inviteUserGUIWindow.closeAllWindowsFromThis()
            self.inviteUserGUIWindow = None

        try:
            self.groupChatDialog.close()
        except:
            print("Window already closed!")

        self.mainInstance.clientInstance.sendMessageToServer((
            ActionType.userQuitGroup, "test"))

    def onInviteClick(self):
        # Create Invite dialog
        self.inviteUserGUIWindow = None
        InviteUserGUIWindow(self.mainInstance, self)

    def updateUsersInGroupLabels(self, newUserList):
        # Check if invite window open
        if self.inviteUserGUIWindow is not None:
            # update the invite list labels
            notInGroupUserList = [
                x for x in self.parent.connectedUsersList if x not in newUserList]
            self.inviteUserGUIWindow.updateUserLabels(
                notInGroupUserList)

        self.clearLayout(self.groupChatDialog.ui.membersListWidget)
        self.usersInGroupLabelList = []
        self.usersInGroup = newUserList

        for user in newUserList:
            self.groupChatDialog.ui.membersListWidget.addItem(user)

    def onSendGroupMessageButtonClick(self):
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.sendGroup, self.groupName, self.groupChatDialog.ui.groupMessageEdit.text()))

    def appendMessageLabel(self, userName, message):
        self.groupChatDialog.ui.groupChatListWidget.addItem(
            userName+" said > "+message)

    def clearLayout(self, layoutToClear):
        layoutToClear.clear()


class SingleChatGUIWindow:
    def __init__(self, mainInstance, parent, toUserName, newMessage=None):
        self.mainInstance = mainInstance
        self.toUserName = toUserName
        self.parent = parent

        parent.singleChatGUIWindow = self

        self.oneOnOneDialog = QDialog()
        self.oneOnOneDialog.ui = oneOnOneDialog()
        self.oneOnOneDialog.ui.setupUi(self.oneOnOneDialog)
        self.oneOnOneDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.oneOnOneDialog.setWindowFlag(
            Qt.WindowCloseButtonHint, False)

        self.oneOnOneDialog.ui.sendButton.clicked.connect(
            self.onSendMessageButtonClick)

        self.oneOnOneDialog.ui.closeButton.clicked.connect(
            self.onCloseClick)

        if newMessage is not None:
            self.appendMessageLabel(newMessage[0], newMessage[1])

        self.oneOnOneDialog.exec_()

    def onCloseClick(self):
        self.parent.singleChatGUIWindow = None
        self.oneOnOneDialog.close()

    def closeAllWindowsFromThis(self):
        self.onCloseClick()

    def onSendMessageButtonClick(self):
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.sendMessage, self.toUserName, self.oneOnOneDialog.ui.oneOnOneMessageEdit.text()))

        self.appendMessageLabel(self.mainInstance.clientInstance.clientName,
                                self.oneOnOneDialog.ui.oneOnOneMessageEdit.text())

    def appendMessageLabel(self, userName, message):
        self.oneOnOneDialog.ui.singleChatListWidget.addItem(
            userName+" said > "+message)


class ConnectedGUIWindow:
    def __init__(self, mainInstance, parent):
        self.mainInstance = mainInstance
        self.parent = parent

        self.connectedDialog = QDialog()
        self.connectedDialog.ui = connectedDialog()
        self.connectedDialog.ui.setupUi(self.connectedDialog)
        self.connectedDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.connectedDialog.setWindowFlag(
            Qt.WindowCloseButtonHint, False)

        self.connectedDialog.ui.oneOnOneChatButton.clicked.connect(
            self.onSingleChatOpen)

        self.connectedDialog.ui.createButton.clicked.connect(
            self.onCreateGroupButton)

        self.connectedDialog.ui.joinButton.clicked.connect(
            self.onJoinClick)

        self.connectedDialog.ui.closeButton.clicked.connect(
            self.onCloseClick)

        parent.connectedGUIWindow = self

        self.singleChatGUIWindow = None

        self.selectedSingleChatLabel = None
        self.joinedUsersLabelList = []

        self.groupChatGUIWindow = None

        self.selectedGroupChatLabel = None
        self.groupsLabelList = []

        self.connectedUsersList = []

        self.groupInviteGUIWindow = None

        self.connectedDialog.exec_()

    def onCloseClick(self):
        self.connectedDialog.close()
        self.parent.connectedGUIWindow = None

        self.mainInstance.clientInstance.sendMessageToServer((
            ActionType.userQuitServer, "test"))

    def joinGroupFromInvite(self, toGroup):
        # close all the other popups and make them join the group
        self.closeAllWindowsFromThis()

        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.groupUserJoined, toGroup))

        GroupChatGUIWindow(self.mainInstance, self, toGroup)

    def closeAllWindowsFromThis(self):
        if self.singleChatGUIWindow is not None:
            # call its close
            self.singleChatGUIWindow.closeAllWindowsFromThis()
            self.singleChatGUIWindow = None
            self.selectedGroupChatLabel = None

        if self.groupChatGUIWindow is not None:
            # call its close
            self.groupChatGUIWindow.closeAllWindowsFromThis()
            self.groupChatGUIWindow = None
            self.selectedGroupChatLabel = None

        self.groupInviteGUIWindow = None

    def openInvitePopUp(self, fromUser, toGroup):
        groupInvitePopup(self.mainInstance, self, fromUser, toGroup)

    def onJoinClick(self):
        if self.selectedGroupChatLabel is not None:
            # Send user joined group message to server
            print("added user again")
            self.mainInstance.clientInstance.sendMessageToServer(
                (ActionType.groupUserJoined, self.selectedGroupChatLabel.text()))

            GroupChatGUIWindow(self.mainInstance, self,
                               self.selectedGroupChatLabel.text())

    def onCreateGroupButton(self):
        # Send a message to Server that a new room was made
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.createRoom, "test"))

    def updateGroupLabels(self, newGroupsList):
        self.clearLayout(self.connectedDialog.ui.groupListWidget)
        self.groupsLabelList = []
        self.selectedGroupChatLabel = None

        for group in newGroupsList:
            self.connectedDialog.ui.groupListWidget.addItem(group)

        self.connectedDialog.ui.groupListWidget.itemClicked.connect(
            self.onSingleGroupClick)

    def onSingleGroupClick(self, label):
        self.selectedGroupChatLabel = label

    def onSingleChatOpen(self):
        if self.selectedSingleChatLabel is not None:
            SingleChatGUIWindow(self.mainInstance, self,
                                self.selectedSingleChatLabel.text())

    def onSingleUserLabelClick(self, item):
        self.selectedSingleChatLabel = item

    def updateUserLabels(self, newUserList):
        # Check if in group chat and if invite window open
        if self.groupChatGUIWindow is not None and self.groupChatGUIWindow.inviteUserGUIWindow is not None:
            # update the invite list labels
            notInGroupUserList = [
                x for x in newUserList if x not in self.groupChatGUIWindow.usersInGroup]
            self.groupChatGUIWindow.inviteUserGUIWindow.updateUserLabels(
                notInGroupUserList)

        self.clearLayout(self.connectedDialog.ui.usersListWidget)
        self.joinedUsersLabelList = []
        self.connectedUsersList = newUserList
        self.selectedSingleChatLabel = None

        for user in newUserList:
            self.connectedDialog.ui.usersListWidget.addItem(user)

        self.connectedDialog.ui.usersListWidget.itemClicked.connect(
            self.onSingleUserLabelClick)

    def clearLayout(self, layoutToClear):
        layoutToClear.clear()


# Source https://wiki.python.org/moin/PyQt/Making%20non-clickable%20widgets%20clickable
# Allows for labels to emit on click events
def clickable(widget):

    class Filter(QObject):
        clicked = pyqtSignal(object)

        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit(obj)
                        return True
                return False

    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked


class ConnectionGUIWindow:
    def __init__(self, mainInstance):
        self.mainInstance = mainInstance
        self.connectedGUIWindow = None

        # Instantiate main connection window
        app = QApplication(sys.argv)
        self.connectionWindow = QMainWindow()
        self.mainWindowUI = Ui_ConnectionWindow()
        self.mainWindowUI.setupUi(self.connectionWindow)

        self.connectionWindow.setWindowFlag(
            Qt.WindowCloseButtonHint, False)

        # Add on connect button click
        self.mainWindowUI.connectButton.clicked.connect(
            self.onConnectButtonClick)

        self.mainWindowUI.cancelButton.clicked.connect(
            self.onCancelClick)

        mainInstance.mainGuiWindow = self

        # Show it
        self.connectionWindow.show()

        app.aboutToQuit.connect(self.onCancelClick)

        # Keeps it open until closed
        app.exec_()

    def onCancelClick(self):
        self.connectionWindow.close()
        # self.mainInstance.clientInstance.sendMessageToServer((
        #     ActionType.userQuitServer, "test"))
        sys.exit(0)

    def onConnectButtonClick(self):
        # Get the ip, port and client name
        # ip = self.mainWindowUI.ipAddressLineEdit.text()
        # port = int(self.mainWindowUI.portLineEdit.text())
        clientName = self.mainWindowUI.nickNameLineEdit.text()

        # For testing
        ip = "localhost"
        port = 9988

        self.mainInstance.createNewClient(ip, port, clientName)

        # Instantiate new connected user chat window
        self.connectedGUIWindow = None
        ConnectedGUIWindow(self.mainInstance, self)


class main():

    def __init__(self):
        self.receivedMessagesThread = None
        self.connectedUserLabelList = []

        self.clientInstance = None

        # Instantiate new initial connection window
        self.mainGuiWindow = None
        ConnectionGUIWindow(self)

    def createNewClient(self, ip, port, clientName):
        # Instantiate Client
        self.clientInstance = Client(ip, port, clientName)
        self.clientInstance.start()

        self.receivedMessagesThread = Receive(self.clientInstance)
        self.receivedMessagesThread.newConnectedUsersList.connect(
            self.updateUserLabels)
        self.receivedMessagesThread.newSingleMessage.connect(
            self.gotSingleMessage)
        self.receivedMessagesThread.newGroupsList.connect(
            self.updateGroupLabels)
        self.receivedMessagesThread.newUserListInGroup.connect(
            self.updateUsersInGroupLabels)

        self.receivedMessagesThread.newGroupMessage.connect(
            self.gotGroupMessage)

        self.receivedMessagesThread.newInviteToGroup.connect(
            self.gotGroupInvite)

        self.receivedMessagesThread.start()

    def updateUserLabels(self, newUserList):
        self.mainGuiWindow.connectedGUIWindow.updateUserLabels(newUserList)

    def gotSingleMessage(self, userFrom, message):
        # Create new Single chat popup and update messages
        if self.mainGuiWindow.connectedGUIWindow.singleChatGUIWindow is None:
            SingleChatGUIWindow(
                self, self.mainGuiWindow.connectedGUIWindow, userFrom, (userFrom, message))
        else:
            self.mainGuiWindow.connectedGUIWindow.singleChatGUIWindow.appendMessageLabel(
                userFrom, message)

    def updateGroupLabels(self, newGroupsList):
        self.mainGuiWindow.connectedGUIWindow.updateGroupLabels(newGroupsList)

    def updateUsersInGroupLabels(self, newUserListIngroup):
        self.mainGuiWindow.connectedGUIWindow.groupChatGUIWindow.updateUsersInGroupLabels(
            newUserListIngroup)

    def gotGroupMessage(self, userFrom, message):
        self.mainGuiWindow.connectedGUIWindow.groupChatGUIWindow.appendMessageLabel(
            userFrom, message)

    def gotGroupInvite(self, userFrom, toGroup):
        self.mainGuiWindow.connectedGUIWindow.openInvitePopUp(
            userFrom, toGroup)


if __name__ == "__main__":
    main()
