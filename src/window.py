import asyncio
from datetime import datetime

from PyQt6 import QtCore
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget, QMenu,
)
from qasync import asyncSlot

from client import IrcClient


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.users_items = None
        self.users = None
        self.save_log_button = None
        self.encoding_line_edit = None
        self.irc_client: IrcClient = None
        self.channel_data = []
        self.channel_items = []
        self.chat_text = []
        self.current_channel = None

        self.users_view = None
        self.leave_channel_button = None
        self.connect_channel_button = None
        self.send_message_line_edit = None
        self.send_command_line_edit = None
        self.chat_view: QTextEdit = None
        self.channel_view: QTreeWidget = None
        self.server_line_edit = None
        self.nickname_line_edit = None
        self.button_connect = None

        main_widget = QTabWidget()

        self.tab_settings(main_widget)
        self.tab_irc(main_widget)
        self.setCentralWidget(main_widget)

    def tab_settings(self, tabs):
        layout = QFormLayout()
        layout.addWidget(QLabel('ip:port Сервера:'))
        self.server_line_edit = QLineEdit('irc.ircnet.ru:6688')
        layout.addWidget(self.server_line_edit)

        layout.addWidget(QLabel('Кодировка'))
        self.encoding_line_edit = QLineEdit('utf-8')
        layout.addWidget(self.encoding_line_edit)

        layout.addWidget(QLabel('Nickname:'))
        self.nickname_line_edit = QLineEdit('pevel')
        layout.addWidget(self.nickname_line_edit)

        self.button_connect = QPushButton('Подключиться!')
        layout.addWidget(self.button_connect)
        self.button_connect.clicked.connect(self.connect_button_clicked)

        widget = QWidget()
        widget.setLayout(layout)
        tabs.addTab(widget, 'Подключение')

    def tab_irc(self, tabs):
        layout = QHBoxLayout()
        layout_left_channels = QVBoxLayout()
        layout_left_users = QVBoxLayout()
        layout_right = QVBoxLayout()

        self.channel_view = QTreeWidget()
        self.channel_view.headerItem().setText(0, "Название")
        self.channel_view.headerItem().setText(1, "Users")
        self.channel_view.headerItem().setText(2, 'Topic')
        layout_left_channels.addWidget(self.channel_view)
        self.connect_channel_button = QPushButton('Подключиться к каналу')
        layout_left_channels.addWidget(self.connect_channel_button)
        self.connect_channel_button.clicked.connect(self.connect_channel)
        self.leave_channel_button = QPushButton('Покинуть канал')
        self.leave_channel_button.clicked.connect(self.leave_channel)
        self.leave_channel_button.setDisabled(True)
        layout_left_channels.addWidget(self.leave_channel_button)

        self.save_log_button = QPushButton('Сохранить лог')
        self.save_log_button.clicked.connect(self.save_log)
        layout_left_channels.addWidget(self.save_log_button)

        self.users_view = QTreeWidget()

        self.users_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.users_view.customContextMenuRequested.connect(self.open_menu)

        self.users_view.headerItem().setText(0, "Ник")
        layout_left_users.addWidget(self.users_view)

        channel_user_tab = QTabWidget()
        channel_user_tab.setTabPosition(QTabWidget.TabPosition.West)

        layout_left_channels_widget = QWidget()
        layout_left_channels_widget.setLayout(layout_left_channels)
        channel_user_tab.addTab(layout_left_channels_widget, 'Каналы')

        layout_left_users_widget = QWidget()
        layout_left_users_widget.setLayout(layout_left_users)
        channel_user_tab.addTab(layout_left_users_widget, 'Пользователи')

        self.send_command_line_edit = QLineEdit()
        self.send_command_line_edit.setPlaceholderText('Command line')
        layout_right.addWidget(self.send_command_line_edit)
        self.send_command_line_edit.returnPressed.connect(self.command_enter_pressed)

        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        layout_right.addWidget(self.chat_view)

        self.send_message_line_edit = QLineEdit()
        self.send_message_line_edit.setPlaceholderText('Message')
        layout_right.addWidget(self.send_message_line_edit)
        self.send_message_line_edit.returnPressed.connect(self.message_enter_pressed)

        layout.addWidget(channel_user_tab, stretch=1)
        layout.addLayout(layout_right, stretch=3)

        widget = QWidget()
        widget.setLayout(layout)
        tabs.addTab(widget, "Irc")

    @asyncSlot()
    async def command_enter_pressed(self):
        command = self.send_command_line_edit.text()
        if command:
            await self.irc_client.execute_command(command)
            self.send_command_line_edit.clear()

    @asyncSlot()
    async def connect_button_clicked(self):
        addr, nickname, encoding = (
            self.server_line_edit.text().split(':'),
            self.nickname_line_edit.text(),
            self.encoding_line_edit.text(),
        )
        host, port = addr[0], addr[1]

        self.irc_client = IrcClient(
            host, port, nickname, encoding, self.change_channels_list, self.change_chat_members, self.change_chat_view
        )
        await self.irc_client.connect()
        loop = asyncio.get_event_loop()
        loop.create_task(self.irc_client.handle())

    @asyncSlot()
    async def message_enter_pressed(self):
        message = self.send_message_line_edit.text()
        if message:
            await self.irc_client.send_message(message)
            self.send_message_line_edit.clear()

    @asyncSlot()
    async def connect_channel(self):
        self.irc_client.leave_channel()
        for index, item in enumerate(self.channel_items):
            if item.isSelected():
                self.irc_client.join_channel(self.channel_data[index])
                self.irc_client.update_members()
        self.leave_channel_button.setDisabled(False)

    @asyncSlot()
    async def leave_channel(self):
        self.irc_client.leave_channel()
        self.leave_channel_button.setDisabled(True)
        self.users_view.clear()

    @asyncSlot()
    async def save_log(self):
        path = f'{datetime.now().strftime("%d-%m-%Y-%H-%M-%S")}.txt'
        with open(path, 'w', encoding=self.irc_client.encoding) as log_file:
            log_file.write(self.chat_view.toPlainText())

    @asyncSlot()
    async def kick(self):
        user = None
        for index, item in enumerate(self.users_items):
            if item.isSelected():
                user = self.users[index]
        if user:
            await self.irc_client.execute_command(f"MODE {self.irc_client.last_channel} +b {user}")

    @asyncSlot()
    async def ban(self):
        user = None
        for index, item in enumerate(self.users_items):
            if item.isSelected():
                user = self.users[index]
        if user:
            await self.irc_client.execute_command(f"KICK {self.irc_client.last_channel} {user}")

    async def change_channels_list(self, list_channels) -> None:
        self.channel_view.clear()
        self.channel_data.clear()
        self.channel_items.clear()
        for name, count, topic in list_channels:
            current_tree_item = QTreeWidgetItem(self.channel_view)
            current_tree_item.setText(0, name)
            current_tree_item.setText(1, count)
            current_tree_item.setText(2, topic)
            self.channel_items.append(current_tree_item)
        self.channel_data = list_channels.copy()
        for i in range(3):
            self.channel_view.resizeColumnToContents(i)

    async def change_chat_view(self, text: str) -> None:
        self.chat_view.append(text)

    async def change_chat_members(self, members) -> None:
        self.users_view.clear()
        self.users = []
        self.users_items = []
        for membership, nick, prefix in members:
            current_tree_item = QTreeWidgetItem(self.users_view)
            current_tree_item.setText(0, prefix + nick)
            self.users_items.append(current_tree_item)
            self.users.append(nick)

    def open_menu(self, position):
        menu = QMenu()
        addDes = QAction('Kick', menu)
        addDes.triggered.connect(self.kick)
        addDes_2 = QAction('Ban', menu)
        addDes_2.triggered.connect(self.ban)

        menu.addAction(addDes)
        menu.addAction(addDes_2)
        menu.exec(self.users_view.viewport().mapToGlobal(position))
