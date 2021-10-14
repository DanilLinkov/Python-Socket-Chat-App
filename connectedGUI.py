# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'connectedGUI.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(506, 666)
        Dialog.setMinimumSize(QtCore.QSize(0, 0))
        self.verticalLayoutWidget = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(50, 20, 389, 231))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(
            self.label, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.scrollArea = QtWidgets.QScrollArea(self.verticalLayoutWidget)
        self.scrollArea.setMinimumSize(QtCore.QSize(200, 150))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.connectedUsersScroll = QtWidgets.QWidget()
        self.connectedUsersScroll.setGeometry(QtCore.QRect(0, 0, 198, 194))
        self.connectedUsersScroll.setMinimumSize(QtCore.QSize(160, 150))
        self.connectedUsersScroll.setObjectName("connectedUsersScroll")
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(
            self.connectedUsersScroll)
        self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(0, 0, 201, 201))
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.clientsListLayout = QtWidgets.QVBoxLayout(
            self.verticalLayoutWidget_3)
        self.clientsListLayout.setContentsMargins(0, 0, 0, 0)
        self.clientsListLayout.setObjectName("clientsListLayout")
        self.scrollArea.setWidget(self.connectedUsersScroll)
        self.horizontalLayout.addWidget(
            self.scrollArea, 0, QtCore.Qt.AlignHCenter)
        self.oneOnOneChatButton = QtWidgets.QPushButton(
            self.verticalLayoutWidget)
        self.oneOnOneChatButton.setMinimumSize(QtCore.QSize(0, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.oneOnOneChatButton.setFont(font)
        self.oneOnOneChatButton.setObjectName("oneOnOneChatButton")
        self.horizontalLayout.addWidget(
            self.oneOnOneChatButton, 0, QtCore.Qt.AlignTop)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget_2.setGeometry(
            QtCore.QRect(50, 280, 389, 231))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(
            self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(
            self.label_2, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.scrollArea_2 = QtWidgets.QScrollArea(self.verticalLayoutWidget_2)
        self.scrollArea_2.setMinimumSize(QtCore.QSize(200, 150))
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.groupChatScroll = QtWidgets.QWidget()
        self.groupChatScroll.setGeometry(QtCore.QRect(0, 0, 198, 194))
        self.groupChatScroll.setMinimumSize(QtCore.QSize(160, 150))
        self.groupChatScroll.setObjectName("groupChatScroll")
        self.verticalLayoutWidget_4 = QtWidgets.QWidget(self.groupChatScroll)
        self.verticalLayoutWidget_4.setGeometry(QtCore.QRect(0, 0, 201, 201))
        self.verticalLayoutWidget_4.setObjectName("verticalLayoutWidget_4")
        self.chatRoomsListLayout = QtWidgets.QVBoxLayout(
            self.verticalLayoutWidget_4)
        self.chatRoomsListLayout.setContentsMargins(0, 0, 0, 0)
        self.chatRoomsListLayout.setObjectName("chatRoomsListLayout")
        self.scrollArea_2.setWidget(self.groupChatScroll)
        self.horizontalLayout_2.addWidget(
            self.scrollArea_2, 0, QtCore.Qt.AlignHCenter)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.createButton = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        self.createButton.setMinimumSize(QtCore.QSize(0, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.createButton.setFont(font)
        self.createButton.setObjectName("createButton")
        self.verticalLayout_3.addWidget(
            self.createButton, 0, QtCore.Qt.AlignTop)
        self.joinButton = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        self.joinButton.setMinimumSize(QtCore.QSize(0, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.joinButton.setFont(font)
        self.joinButton.setObjectName("joinButton")
        self.verticalLayout_3.addWidget(self.joinButton, 0, QtCore.Qt.AlignTop)
        self.horizontalLayout_2.addLayout(self.verticalLayout_3)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.closeButton = QtWidgets.QPushButton(Dialog)
        self.closeButton.setGeometry(QtCore.QRect(260, 580, 177, 40))
        self.closeButton.setMinimumSize(QtCore.QSize(0, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.closeButton.setFont(font)
        self.closeButton.setObjectName("closeButton")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "ConnectedWindow"))
        self.label.setText(_translate("Dialog", "Connected Clients"))
        self.oneOnOneChatButton.setText(_translate("Dialog", "1:1 Chat"))
        self.label_2.setText(_translate("Dialog", "Chat rooms (Group chat)"))
        self.createButton.setText(_translate("Dialog", "Create"))
        self.joinButton.setText(_translate("Dialog", "Join"))
        self.closeButton.setText(_translate("Dialog", "Close"))


# if __name__ == "__main__":
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     Dialog = QtWidgets.QDialog()
#     ui = Ui_Dialog()
#     ui.setupUi(Dialog)
#     Dialog.show()
#     sys.exit(app.exec_())
