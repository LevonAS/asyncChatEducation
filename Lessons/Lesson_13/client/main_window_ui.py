# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'client.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainClientWindow(object):
    def setupUi(self, MainClientWindow):
        MainClientWindow.setObjectName("MainClientWindow")
        MainClientWindow.resize(756, 567)
        MainClientWindow.setMinimumSize(QtCore.QSize(756, 534))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(197, 222, 235))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(197, 222, 235))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(197, 222, 235))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(197, 222, 235))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        MainClientWindow.setPalette(palette)
        self.centralwidget = QtWidgets.QWidget(MainClientWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label_contacts = QtWidgets.QLabel(self.centralwidget)
        self.label_contacts.setGeometry(QtCore.QRect(10, 0, 141, 16))
        self.label_contacts.setObjectName("label_contacts")
        self.btn_add_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add_contact.setGeometry(QtCore.QRect(10, 450, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_add_contact.setFont(font)
        self.btn_add_contact.setObjectName("btn_add_contact")
        self.btn_remove_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_remove_contact.setGeometry(QtCore.QRect(140, 450, 121, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_remove_contact.setFont(font)
        self.btn_remove_contact.setObjectName("btn_remove_contact")
        self.label_history = QtWidgets.QLabel(self.centralwidget)
        self.label_history.setGeometry(QtCore.QRect(300, 0, 391, 21))
        self.label_history.setObjectName("label_history")
        self.text_message = QtWidgets.QTextEdit(self.centralwidget)
        self.text_message.setGeometry(QtCore.QRect(300, 360, 441, 71))
        self.text_message.setObjectName("text_message")
        self.label_new_message = QtWidgets.QLabel(self.centralwidget)
        self.label_new_message.setGeometry(QtCore.QRect(300, 330, 441, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_new_message.setFont(font)
        self.label_new_message.setObjectName("label_new_message")
        self.list_contacts = QtWidgets.QListView(self.centralwidget)
        self.list_contacts.setGeometry(QtCore.QRect(10, 20, 251, 411))
        self.list_contacts.setObjectName("list_contacts")
        self.list_messages = QtWidgets.QListView(self.centralwidget)
        self.list_messages.setGeometry(QtCore.QRect(300, 20, 441, 301))
        self.list_messages.setObjectName("list_messages")
        self.btn_send = QtWidgets.QPushButton(self.centralwidget)
        self.btn_send.setGeometry(QtCore.QRect(590, 450, 151, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_send.setFont(font)
        self.btn_send.setObjectName("btn_send")
        self.btn_clear = QtWidgets.QPushButton(self.centralwidget)
        self.btn_clear.setGeometry(QtCore.QRect(450, 450, 131, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_clear.setFont(font)
        self.btn_clear.setObjectName("btn_clear")
        self.label_status = QtWidgets.QLabel(self.centralwidget)
        self.label_status.setGeometry(QtCore.QRect(20, 500, 721, 20))
        self.label_status.setText("")
        self.label_status.setObjectName("label_status")
        MainClientWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainClientWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 756, 22))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menubar)
        self.menu_2.setObjectName("menu_2")
        MainClientWindow.setMenuBar(self.menubar)
        self.statusBar = QtWidgets.QStatusBar(MainClientWindow)
        self.statusBar.setObjectName("statusBar")
        MainClientWindow.setStatusBar(self.statusBar)
        self.menu_exit = QtWidgets.QAction(MainClientWindow)
        self.menu_exit.setObjectName("menu_exit")
        self.menu_add_contact = QtWidgets.QAction(MainClientWindow)
        self.menu_add_contact.setObjectName("menu_add_contact")
        self.menu_del_contact = QtWidgets.QAction(MainClientWindow)
        self.menu_del_contact.setObjectName("menu_del_contact")
        self.menu.addAction(self.menu_exit)
        self.menu_2.addAction(self.menu_add_contact)
        self.menu_2.addAction(self.menu_del_contact)
        self.menu_2.addSeparator()
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())

        self.retranslateUi(MainClientWindow)
        self.btn_clear.clicked.connect(self.text_message.clear) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainClientWindow)

    def retranslateUi(self, MainClientWindow):
        _translate = QtCore.QCoreApplication.translate
        MainClientWindow.setWindowTitle(_translate("MainClientWindow", "Чат Программа Auuu"))
        self.label_contacts.setText(_translate("MainClientWindow", "Список контактов:"))
        self.btn_add_contact.setText(_translate("MainClientWindow", "Добавить контакт"))
        self.btn_remove_contact.setText(_translate("MainClientWindow", "Удалить контакт"))
        self.label_history.setText(_translate("MainClientWindow", "История сообщений:"))
        self.label_new_message.setText(_translate("MainClientWindow", "Введите новое сообщение:"))
        self.btn_send.setText(_translate("MainClientWindow", "Отправить сообщение"))
        self.btn_clear.setText(_translate("MainClientWindow", "Очистить поле"))
        self.menu.setTitle(_translate("MainClientWindow", "Файл"))
        self.menu_2.setTitle(_translate("MainClientWindow", "Контакты"))
        self.menu_exit.setText(_translate("MainClientWindow", "Выход"))
        self.menu_add_contact.setText(_translate("MainClientWindow", "Добавить контакт"))
        self.menu_del_contact.setText(_translate("MainClientWindow", "Удалить контакт"))
