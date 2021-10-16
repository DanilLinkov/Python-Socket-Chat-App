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

from Utils import *
from ActionEnum import ActionType


class Receive(QThread):
    newConnectedUsersList = pyqtSignal(object)
    newSingleMessage = pyqtSignal(object, object)
    newGroupsList = pyqtSignal(object)
    newUserListInGroup = pyqtSignal(object)
    newGroupMessage = pyqtSignal(object, object)

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


class InviteUserGUIWindow:
    def __init__(self, mainInstance, parent):
        self.mainInstance = mainInstance
        self.parent = parent

        parent.inviteUserGUIWindow = self

        self.inviteChatDialog = QDialog()
        self.inviteChatDialog.ui = inviteDialog()
        self.inviteChatDialog.ui.setupUi(self.inviteChatDialog)
        self.inviteChatDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.selectedUserToInviteLabel = None
        self.usersNotInTheGroupLabelList = []

        print(self.parent.usersInGroup)
        print(self.parent.parent.connectedUsersList)

        self.updateUserLabels([
            x for x in self.parent.parent.connectedUsersList if x not in self.parent.usersInGroup])

        self.inviteChatDialog.exec_()

    def onInviteUserClick(self):
        # Make client send message to server to invite toUser, groupName
        pass

    def onSingleUserLabelClick(self, label):
        for l in self.usersNotInTheGroupLabelList:
            l.setStyleSheet("background-color: white")

        label.setStyleSheet("background-color: grey")
        self.selectedUserToInviteLabel = label

    def updateUserLabels(self, newUserList):
        # Minus users in the group from the newUserList
        print(newUserList)

        self.clearLayout(self.inviteChatDialog.ui.inviteListLayout)
        self.usersNotInTheGroupLabelList = []
        self.selectedUserToInviteLabel = None

        self.inviteChatDialog.ui.inviteListLayout.setAlignment(
            Qt.AlignTop)

        for user in newUserList:
            newUserLabel = QLabel()
            font = QFont()
            font.setPointSize(15)
            newUserLabel.setFont(font)
            newUserLabel.setObjectName(user)
            newUserLabel.setText(user)

            self.usersNotInTheGroupLabelList.append(newUserLabel)

            newUserLabel.setFixedSize(200, 50)

            # Make it clickable by passing it through a custom clickable class
            clickable(newUserLabel).connect(self.onSingleUserLabelClick)

            self.inviteChatDialog.ui.inviteListLayout.addWidget(newUserLabel)

    def clearLayout(self, layoutToClear):
        for i in reversed(range(layoutToClear.count())):
            layoutToClear.itemAt(i).widget().deleteLater()


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

        self.usersInGroupLabelList = []
        self.usersInGroup = []

        self.inviteUserGUIWindow = None

        self.groupChatDialog.ui.sendButton_2.clicked.connect(
            self.onSendGroupMessageButtonClick)

        self.groupChatDialog.ui.sendButton_3.clicked.connect(
            self.onInviteClick)

        self.groupChatDialog.exec_()

    def onInviteClick(self):
        # Create Invite dialog
        self.inviteUserGUIWindow = None
        InviteUserGUIWindow(self.mainInstance, self)

    def updateUsersInGroupLabels(self, newUserList):
        self.clearLayout(self.groupChatDialog.ui.membersListLayout)
        self.usersInGroupLabelList = []
        self.usersInGroup = newUserList

        self.groupChatDialog.ui.membersListLayout.setAlignment(
            Qt.AlignTop)

        for user in newUserList:
            newUserLabel = QLabel()
            font = QFont()
            font.setPointSize(15)
            newUserLabel.setFont(font)
            newUserLabel.setObjectName(user)
            newUserLabel.setText(user)

            self.usersInGroupLabelList.append(newUserLabel)

            newUserLabel.setFixedSize(200, 50)

            self.groupChatDialog.ui.membersListLayout.addWidget(newUserLabel)

    def onSendGroupMessageButtonClick(self):
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.sendGroup, self.groupName, self.groupChatDialog.ui.groupMessageEdit.text()))

        # self.appendMessageLabel(self.mainInstance.clientInstance.clientName,
        #                         self.oneOnOneDialog.ui.groupMessageEdit.text())

    def appendMessageLabel(self, userName, message):
        self.groupChatDialog.ui.messagesScrollLayoutGroup.setAlignment(
            Qt.AlignTop)

        newMessageLabel = QLabel()
        font = QFont()
        font.setPointSize(15)
        newMessageLabel.setFont(font)
        newMessageLabel.setObjectName(userName)
        newMessageLabel.setText(userName.split(":")[0]+" => "+message)

        newMessageLabel.setFixedSize(200, 50)

        self.groupChatDialog.ui.messagesScrollLayoutGroup.addWidget(
            newMessageLabel)

    def clearLayout(self, layoutToClear):
        for i in reversed(range(layoutToClear.count())):
            layoutToClear.itemAt(i).widget().deleteLater()


class SingleChatGUIWindow:
    def __init__(self, mainInstance, parent, toUserName, newMessage=None):
        self.mainInstance = mainInstance
        self.toUserName = toUserName

        parent.singleChatGUIWindow = self

        self.oneOnOneDialog = QDialog()
        self.oneOnOneDialog.ui = oneOnOneDialog()
        self.oneOnOneDialog.ui.setupUi(self.oneOnOneDialog)
        self.oneOnOneDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.oneOnOneDialog.ui.sendButton.clicked.connect(
            self.onSendMessageButtonClick)

        if newMessage is not None:
            self.appendMessageLabel(newMessage[0], newMessage[1])

        self.oneOnOneDialog.exec_()

    def onSendMessageButtonClick(self):
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.sendMessage, self.toUserName, self.oneOnOneDialog.ui.oneOnOneMessageEdit.text()))

        self.appendMessageLabel(self.mainInstance.clientInstance.clientName,
                                self.oneOnOneDialog.ui.oneOnOneMessageEdit.text())

    def appendMessageLabel(self, userName, message):
        self.oneOnOneDialog.ui.messagesScrollLayout.setAlignment(Qt.AlignTop)

        newMessageLabel = QLabel()
        font = QFont()
        font.setPointSize(15)
        newMessageLabel.setFont(font)
        newMessageLabel.setObjectName(userName)
        newMessageLabel.setText(userName.split(":")[0]+" => "+message)

        newMessageLabel.setFixedSize(200, 50)

        self.oneOnOneDialog.ui.messagesScrollLayout.addWidget(newMessageLabel)


class ConnectedGUIWindow:
    def __init__(self, mainInstance, parent):
        self.mainInstance = mainInstance

        self.connectedDialog = QDialog()
        self.connectedDialog.ui = connectedDialog()
        self.connectedDialog.ui.setupUi(self.connectedDialog)
        self.connectedDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.connectedDialog.ui.oneOnOneChatButton.clicked.connect(
            self.onSingleChatOpen)

        self.connectedDialog.ui.createButton.clicked.connect(
            self.onCreateGroupButton)

        self.connectedDialog.ui.joinButton.clicked.connect(
            self.onJoinClick)

        parent.connectedGUIWindow = self

        self.singleChatGUIWindow = None

        self.selectedSingleChatLabel = None
        self.joinedUsersLabelList = []

        self.groupChatGUIWindow = None

        self.selectedGroupChatLabel = None
        self.groupsLabelList = []

        self.connectedUsersList = []

        self.connectedDialog.exec_()

    def onJoinClick(self):
        if self.selectedGroupChatLabel is not None:
            # Send user joined group message to server
            self.mainInstance.clientInstance.sendMessageToServer(
                (ActionType.groupUserJoined, self.selectedGroupChatLabel.text()))

            GroupChatGUIWindow(self.mainInstance, self,
                               self.selectedGroupChatLabel.text())

    def onCreateGroupButton(self):
        # Send a message to Server that a new room was made
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.createRoom, "test"))

    def updateGroupLabels(self, newGroupsList):
        self.clearLayout(self.connectedDialog.ui.chatRoomsListLayout)

        self.groupsLabelList = []
        self.selectedGroupChatLabel = None

        self.connectedDialog.ui.chatRoomsListLayout.setAlignment(
            Qt.AlignTop)

        for group in newGroupsList:
            newGroupLabel = QLabel()
            font = QFont()
            font.setPointSize(15)
            newGroupLabel.setFont(font)
            newGroupLabel.setObjectName(group)
            newGroupLabel.setText(group)

            self.groupsLabelList.append(newGroupLabel)

            newGroupLabel.setFixedSize(200, 50)

            # Make it clickable by passing it through a custom clickable class
            clickable(newGroupLabel).connect(self.onSingleGroupClick)

            self.connectedDialog.ui.chatRoomsListLayout.addWidget(
                newGroupLabel)

    def onSingleGroupClick(self, label):
        for l in self.groupsLabelList:
            l.setStyleSheet("background-color: white")

        label.setStyleSheet("background-color: grey")
        self.selectedGroupChatLabel = label

    def onSingleChatOpen(self):
        if self.selectedSingleChatLabel is not None:
            SingleChatGUIWindow(self.mainInstance, self,
                                self.selectedSingleChatLabel.text())

    def onSingleUserLabelClick(self, label):
        for l in self.joinedUsersLabelList:
            l.setStyleSheet("background-color: white")

        label.setStyleSheet("background-color: grey")
        self.selectedSingleChatLabel = label

    def updateUserLabels(self, newUserList):
        # Check if in group chat and if invite window open
        if self.groupChatGUIWindow is not None and self.groupChatGUIWindow.inviteUserGUIWindow is not None:
            # update the invite list labels
            notInGroupUserList = [
                x for x in newUserList if x not in self.groupChatGUIWindow.usersInGroup]
            self.groupChatGUIWindow.inviteUserGUIWindow.updateUserLabels(
                notInGroupUserList)

        self.clearLayout(self.connectedDialog.ui.clientsListLayout)
        self.joinedUsersLabelList = []
        self.connectedUsersList = newUserList
        self.selectedSingleChatLabel = None

        self.connectedDialog.ui.clientsListLayout.setAlignment(
            Qt.AlignTop)

        for user in newUserList:
            newUserLabel = QLabel()
            font = QFont()
            font.setPointSize(15)
            newUserLabel.setFont(font)
            newUserLabel.setObjectName(user)
            newUserLabel.setText(user)

            self.joinedUsersLabelList.append(newUserLabel)

            newUserLabel.setFixedSize(200, 50)

            # Make it clickable by passing it through a custom clickable class
            clickable(newUserLabel).connect(self.onSingleUserLabelClick)

            self.connectedDialog.ui.clientsListLayout.addWidget(newUserLabel)

    def clearLayout(self, layoutToClear):
        for i in reversed(range(layoutToClear.count())):
            layoutToClear.itemAt(i).widget().deleteLater()


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
        connectionWindow = QMainWindow()
        self.mainWindowUI = Ui_ConnectionWindow()
        self.mainWindowUI.setupUi(connectionWindow)

        # Add on connect button click
        self.mainWindowUI.connectButton.clicked.connect(
            self.onConnectButtonClick)

        mainInstance.mainGuiWindow = self

        # Show it
        connectionWindow.show()

        # Keeps it open until closed
        sys.exit(app.exec_())

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


if __name__ == "__main__":
    main()
