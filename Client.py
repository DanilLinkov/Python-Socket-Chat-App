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


class SingleChatGUIWindow:
    def __init__(self, mainInstance, parent, toUserName):
        self.mainInstance = mainInstance
        self.toUserName = toUserName

        parent.singleChatGUIWindow = self

        self.oneOnOneDialog = QDialog()
        self.oneOnOneDialog.ui = oneOnOneDialog()
        self.oneOnOneDialog.ui.setupUi(self.oneOnOneDialog)
        self.oneOnOneDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.oneOnOneDialog.ui.sendButton.clicked.connect(
            self.onSendMessageButtonClick)

        self.oneOnOneDialog.exec_()

    def onSendMessageButtonClick(self):
        self.mainInstance.clientInstance.sendMessageToServer(
            (ActionType.sendMessage, self.toUserName, self.oneOnOneDialog.ui.oneOnOneMessageEdit.text()))


class ConnectedGUIWindow:
    def __init__(self, mainInstance, parent):
        self.mainInstance = mainInstance

        self.connectedDialog = QDialog()
        self.connectedDialog.ui = connectedDialog()
        self.connectedDialog.ui.setupUi(self.connectedDialog)
        self.connectedDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.connectedDialog.ui.oneOnOneChatButton.clicked.connect(
            self.onSingleChatOpen)

        parent.connectedGUIWindow = self

        self.singleChatGUIWindow = None

        self.selectedSingleChatLabel = None
        self.joinedUsersLabelList = []

        self.connectedDialog.exec_()

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
        self.clearLayout(self.connectedDialog.ui.clientsListLayout)

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
        self.joinedUsersLabelList = []
        self.selectedSingleChatLabel = None

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

        self.receivedMessagesThread.start()

    def updateUserLabels(self, newUserList):
        self.mainGuiWindow.connectedGUIWindow.updateUserLabels(newUserList)

    def gotSingleMessage(self, userFrom, message):
        # Create new Single chat popup and update messages
        if self.mainGuiWindow.connectedGUIWindow.singleChatGUIWindow is None:
            SingleChatGUIWindow(
                self, self.mainGuiWindow.connectedGUIWindow, userFrom)
            print(message+" <===")
        else:
            print("Single message instance already exists!")


if __name__ == "__main__":
    main()
