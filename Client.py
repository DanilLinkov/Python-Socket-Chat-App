import threading
import socket
import argparse
import os
import sys
import select
import ssl

from datetime import datetime

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
    # Seperate thread that sends signals to the main GUI thread whenever a message from the server is received

    # connected users list changed signal
    newConnectedUsersList = pyqtSignal(object)
    # one on one message received signal
    newSingleMessage = pyqtSignal(object, object)
    # group list changed signal
    newGroupsList = pyqtSignal(object)
    # user list in joined group changed signal
    newUserListInGroup = pyqtSignal(object)
    # group message received for the group the user is in signal
    newGroupMessage = pyqtSignal(object, object)
    # invite to a group received
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

                        # Go over each potential message type from ActionEnum.py and emit the signal with the message to the main GUI thread
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
    # Client class used to initialize the connection to the server as well as send messages to the server
    def __init__(self, host, port, clientName):
        self.host = host
        self.port = port
        self.clientName = clientName

        # Client ssl encryption
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        self.clientSocket = self.context.wrap_socket(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=host)

    def start(self):
        print(f'Attempting to connect to {self.host}:{self.port}...')

        # Connect to the socket given the host address and port
        self.clientSocket.connect((self.host, self.port))

        # Send the server the client's name
        self.sendMessageToServer(self.clientName)

        # Receive the clients name from the server
        self.clientName = receive(self.clientSocket)[1]

        print(f'Connected to {self.host}:{self.port} as {self.clientName}.')

    def sendMessageToServer(self, messageAsTuple):
        # Use the Utils.py send method to send the message as a tuple
        send(self.clientSocket, messageAsTuple)


class groupInvitePopup:
    def __init__(self, mainInstance, parent, fromUser, toGroup):
        self.mainInstance = mainInstance
        self.parent = parent
        self.toGroup = toGroup

        parent.groupInviteGUIWindow = self

        # Create the invite pop up dialog and set its properties
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
        # If the user accepts the invite then close all the windows except the connected one and open the new groupchat dialog
        self.groupInviteDialog.close()
        self.parent.joinGroupFromInvite(self.toGroup)

    def declineInvite(self):
        # Close the invite pop up window if they declined
        self.parent.groupInviteGUIWindow = None
        self.groupInviteDialog.close()


class InviteUserGUIWindow:
    def __init__(self, mainInstance, parent):
        self.mainInstance = mainInstance
        self.parent = parent

        parent.inviteUserGUIWindow = self

        # Create the gui screen to invite the users
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

        # Update the list of users to invite instantly to see if there are any we can invite
        self.updateUserLabels([
            x for x in self.parent.parent.connectedUsersList if x not in self.parent.usersInGroup])

        self.inviteChatDialog.exec_()

    # Closes this dialog
    def closeAllWindowsFromThis(self):
        self.parent.inviteUserGUIWindow = None
        self.inviteChatDialog.close()

    # Send a message to the server that we want to invite this user to our group
    def onInviteUserClick(self):
        self.parent.inviteUserGUIWindow = None
        self.closeAllWindowsFromThis()
        # Make client send message to server to invite toUser, groupName
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.invite, self.selectedUserToInviteLabel.text(), self.parent.groupName))

    # Set the selected label
    def onSingleUserLabelClick(self, label):
        self.selectedUserToInviteLabel = label

    # Update the GUI for the list of users to invite
    def updateUserLabels(self, newUserList):
        # Clear the list then repopulate it
        self.clearLayout(self.inviteChatDialog.ui.inviteListWidget)
        self.usersNotInTheGroupLabelList = []

        for user in newUserList:
            self.inviteChatDialog.ui.inviteListWidget.addItem(user)

        self.inviteChatDialog.ui.inviteListWidget.itemClicked.connect(
            self.onSingleUserLabelClick)

    # Clear the list widget
    def clearLayout(self, layoutToClear):
        layoutToClear.clear()


class GroupChatGUIWindow:
    # Handles the group chat GUI dialog actions
    def __init__(self, mainInstance, parent, groupName):
        self.mainInstance = mainInstance
        self.groupName = groupName

        self.groupOwner = groupName.split("by ")[1]

        self.clientIsHost = self.groupOwner == self.mainInstance.clientInstance.clientName

        self.parent = parent

        parent.groupChatGUIWindow = self

        # Create the group chat dialog and its properties
        self.groupChatDialog = QDialog()
        self.groupChatDialog.ui = groupDialog()
        self.groupChatDialog.ui.setupUi(self.groupChatDialog)
        self.groupChatDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.groupChatDialog.ui.chatTitle.setText(groupName)

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
        # Close this and all the dialogs from this point
        # and set its refference in the parent as None
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

        # Render the user name depending on wherether its us, the host or both
        for user in newUserList:
            if self.clientIsHost and user == self.mainInstance.clientInstance.clientName:
                self.groupChatDialog.ui.membersListWidget.addItem(
                    user+" (me) (host)")
            elif user == self.mainInstance.clientInstance.clientName:
                self.groupChatDialog.ui.membersListWidget.addItem(
                    user+" (me)")
            elif user == self.groupOwner:
                self.groupChatDialog.ui.membersListWidget.addItem(
                    user+" (host)")
            else:
                self.groupChatDialog.ui.membersListWidget.addItem(user)

    def onSendGroupMessageButtonClick(self):
        # Sends a message to all the users in this group
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.sendGroup, self.groupName, self.groupChatDialog.ui.groupMessageEdit.text()))

    def appendMessageLabel(self, userName, message):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        # Add the message and its timestamp and format it depending on wherether its the host, us, both or other user
        if self.clientIsHost and userName == self.mainInstance.clientInstance.clientName:
            self.groupChatDialog.ui.groupChatListWidget.addItem(
                "("+current_time+") " + "I (host) said > "+message)
        elif userName == self.mainInstance.clientInstance.clientName:
            self.groupChatDialog.ui.groupChatListWidget.addItem(
                "("+current_time+") " + " I said > "+message)
        elif userName == self.groupOwner:
            self.groupChatDialog.ui.groupChatListWidget.addItem(
                "("+current_time+") " + userName+" (host) said > "+message)
        else:
            self.groupChatDialog.ui.groupChatListWidget.addItem(
                "("+current_time+") " + userName+" said > "+message)

    def clearLayout(self, layoutToClear):
        layoutToClear.clear()


class SingleChatGUIWindow:
    # Handles one on one GUI dialog
    def __init__(self, mainInstance, parent, toUserName, newMessage=None):
        self.mainInstance = mainInstance
        self.toUserName = toUserName
        self.parent = parent

        parent.singleChatGUIWindow = self

        # Create the dialog and its properties
        self.oneOnOneDialog = QDialog()
        self.oneOnOneDialog.ui = oneOnOneDialog()
        self.oneOnOneDialog.ui.setupUi(self.oneOnOneDialog)
        self.oneOnOneDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.oneOnOneDialog.ui.chatTitle.setText("Chat with "+toUserName)

        self.oneOnOneDialog.setWindowFlag(
            Qt.WindowCloseButtonHint, False)

        self.oneOnOneDialog.ui.sendButton.clicked.connect(
            self.onSendMessageButtonClick)

        self.oneOnOneDialog.ui.closeButton.clicked.connect(
            self.onCloseClick)

        # If this was created from someone sending us a message then append the message that was received
        if newMessage is not None:
            self.appendMessageLabel(newMessage[0], newMessage[1])

        self.oneOnOneDialog.exec_()

    def onCloseClick(self):
        # Close this dialog and set its refference in the parent as None
        self.parent.singleChatGUIWindow = None
        self.oneOnOneDialog.close()

    def closeAllWindowsFromThis(self):
        self.onCloseClick()

    def onSendMessageButtonClick(self):
        # Send the message to the other user and append it to the clients messages
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.sendMessage, self.toUserName, self.oneOnOneDialog.ui.oneOnOneMessageEdit.text()))

        self.appendMessageLabel(self.mainInstance.clientInstance.clientName,
                                self.oneOnOneDialog.ui.oneOnOneMessageEdit.text())

    def appendMessageLabel(self, userName, message):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        # Append the message to the list widget and format it depending on wherether its us or the other user + timestamp
        if userName == self.mainInstance.clientInstance.clientName:
            self.oneOnOneDialog.ui.singleChatListWidget.addItem(
                "("+current_time+") " + " I said > "+message)
        else:
            self.oneOnOneDialog.ui.singleChatListWidget.addItem(
                "("+current_time+") " + userName+" said > "+message)


class ConnectedGUIWindow:
    # Handles the GUI actions for the main connected dialog
    def __init__(self, mainInstance, parent):
        self.mainInstance = mainInstance
        self.parent = parent

        # Create the dialog and its properties
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
        # Close this dialog and send a message to the server to disconnect/remove the user
        self.connectedDialog.close()
        self.parent.connectedGUIWindow = None

        self.mainInstance.clientInstance.sendMessageToServer((
            ActionType.userQuitServer, "test"))

    def joinGroupFromInvite(self, toGroup):
        # close all the other popups and make them join the group
        self.closeAllWindowsFromThis()

        # Send a message to the users in the group that we joined and open up the group chat dialog
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.groupUserJoined, toGroup))

        GroupChatGUIWindow(self.mainInstance, self, toGroup)

    def closeAllWindowsFromThis(self):
        # Closes all the dialogs and resets the refferences from the parent
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
        # If we got an invite message from the server then create a popup
        groupInvitePopup(self.mainInstance, self, fromUser, toGroup)

    def onJoinClick(self):
        if self.selectedGroupChatLabel is not None:
            # Send user joined group message to server
            self.mainInstance.clientInstance.sendMessageToServer(
                (ActionType.groupUserJoined, self.selectedGroupChatLabel.text()))

            # Create the group chat dialog
            GroupChatGUIWindow(self.mainInstance, self,
                               self.selectedGroupChatLabel.text())

    def onCreateGroupButton(self):
        # Send a message to Server that a new room was made
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.createRoom, "test"))

    def updateGroupLabels(self, newGroupsList):
        # Clear the list widget and append the new users list
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
        # If a user is selected and 1:1 chat is clicked then open the single chat
        if self.selectedSingleChatLabel is not None:
            SingleChatGUIWindow(self.mainInstance, self,
                                self.selectedSingleChatLabel.text())

    def onSingleUserLabelClick(self, item):
        if "(me)" not in item.text():
            self.selectedSingleChatLabel = item

    def updateUserLabels(self, newUserList):
        # Check if in group chat and if invite window open
        if self.groupChatGUIWindow is not None and self.groupChatGUIWindow.inviteUserGUIWindow is not None:
            # update the invite list labels of the possible users we can invite
            notInGroupUserList = [
                x for x in newUserList if x not in self.groupChatGUIWindow.usersInGroup]
            self.groupChatGUIWindow.inviteUserGUIWindow.updateUserLabels(
                notInGroupUserList)

        # Clear the list widget and update the users list
        self.clearLayout(self.connectedDialog.ui.usersListWidget)
        self.joinedUsersLabelList = []
        self.connectedUsersList = newUserList
        self.selectedSingleChatLabel = None

        for user in newUserList:
            if user == self.mainInstance.clientInstance.clientName:
                self.connectedDialog.ui.usersListWidget.addItem(user+" (me)")
            else:
                self.connectedDialog.ui.usersListWidget.addItem(user)

        self.connectedDialog.ui.usersListWidget.itemClicked.connect(
            self.onSingleUserLabelClick)

    def clearLayout(self, layoutToClear):
        layoutToClear.clear()


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
        sys.exit(0)

    def onConnectButtonClick(self):
        # Get the ip, port and client name
        ip = self.mainWindowUI.ipAddressLineEdit.text()
        port = int(self.mainWindowUI.portLineEdit.text())
        clientName = self.mainWindowUI.nickNameLineEdit.text()

        # For testing
        # ip = "localhost"
        # port = 9988

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
        # Instantiate Client and start it
        self.clientInstance = Client(ip, port, clientName)
        self.clientInstance.start()

        # Create a seperate thread to listen for any messages from the server
        self.receivedMessagesThread = Receive(self.clientInstance)

        # Connect methods to the signals
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
        # If we got a new message from someone

        # If the single chat window is not open then open it
        if self.mainGuiWindow.connectedGUIWindow.singleChatGUIWindow is None:
            SingleChatGUIWindow(
                self, self.mainGuiWindow.connectedGUIWindow, userFrom, (userFrom, message))

        # If it is open but not with the user that sent us the message then close that dialog and open a new one with the new user
        elif userFrom != self.mainGuiWindow.connectedGUIWindow.singleChatGUIWindow.toUserName:
            self.mainGuiWindow.connectedGUIWindow.singleChatGUIWindow.closeAllWindowsFromThis()
            SingleChatGUIWindow(
                self, self.mainGuiWindow.connectedGUIWindow, userFrom, (userFrom, message))

        # Otherwise just append the message that we got as its from a user we are currently talking to
        else:
            self.mainGuiWindow.connectedGUIWindow.singleChatGUIWindow.appendMessageLabel(
                userFrom, message)

    def updateGroupLabels(self, newGroupsList):
        # update the groups list UI
        self.mainGuiWindow.connectedGUIWindow.updateGroupLabels(newGroupsList)

    def updateUsersInGroupLabels(self, newUserListIngroup):
        # update the users in a group UI
        self.mainGuiWindow.connectedGUIWindow.groupChatGUIWindow.updateUsersInGroupLabels(
            newUserListIngroup)

    def gotGroupMessage(self, userFrom, message):
        # append a message we got for the group we are in
        self.mainGuiWindow.connectedGUIWindow.groupChatGUIWindow.appendMessageLabel(
            userFrom, message)

    def gotGroupInvite(self, userFrom, toGroup):
        # got a group invite so open a pop up
        self.mainGuiWindow.connectedGUIWindow.openInvitePopUp(
            userFrom, toGroup)


if __name__ == "__main__":
    main()
