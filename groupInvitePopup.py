# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'groupInvitePopup.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(320, 240)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(20, 20, 281, 161))
        self.label.setMinimumSize(QtCore.QSize(281, 161))
        self.label.setMaximumSize(QtCore.QSize(281, 161))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setText("")
        self.label.setTextFormat(QtCore.Qt.RichText)
        self.label.setAlignment(QtCore.Qt.AlignLeading |
                                QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.acceptButton = QtWidgets.QPushButton(Dialog)
        self.acceptButton.setGeometry(QtCore.QRect(70, 200, 75, 23))
        self.acceptButton.setObjectName("acceptButton")
        self.declineButton = QtWidgets.QPushButton(Dialog)
        self.declineButton.setGeometry(QtCore.QRect(170, 200, 75, 23))
        self.declineButton.setObjectName("declineButton")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Group Invite"))
        self.acceptButton.setText(_translate("Dialog", "Accept"))
        self.declineButton.setText(_translate("Dialog", "Decline"))


# if __name__ == "__main__":
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     Dialog = QtWidgets.QDialog()
#     ui = Ui_Dialog()
#     ui.setupUi(Dialog)
#     Dialog.show()
#     sys.exit(app.exec_())
