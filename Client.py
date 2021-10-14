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


class ConnectedGUIWindow:
    def __init__(self, mainInstance):
        self.mainInstance = mainInstance

        self.connectedDialog = QDialog()
        self.connectedDialog.ui = connectedDialog()
        self.connectedDialog.ui.setupUi(self.connectedDialog)
        self.connectedDialog.setAttribute(Qt.WA_DeleteOnClose)

        self.connectedDialog.exec_()

    def onSingleChatOpen(self):
        pass


class ConnectionGUIWindow:
    def __init__(self, mainInstance):
        self.mainInstance = mainInstance

        # Instantiate main connection window
        app = QApplication(sys.argv)
        connectionWindow = QMainWindow()
        self.mainWindowUI = Ui_ConnectionWindow()
        self.mainWindowUI.setupUi(connectionWindow)

        # Add on connect button click
        self.mainWindowUI.connectButton.clicked.connect(
            self.onConnectButtonClick)

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
        self.connectedGUIWindow = ConnectedGUIWindow(self.mainInstance)


class main():

    def __init__(self):
        self.receivedMessagesThread = None
        self.oneOnOneChatSelected = None
        self.connectedUserLabelList = []

        # Instantiate new initial connection window
        self.mainGuiWindow = ConnectionGUIWindow(self)

    def createNewClient(self, ip, port, clientName):
        pass


if __name__ == "__main__":
    main()
