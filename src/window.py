from PyQt6.QtWidgets import QMainWindow, QTabWidget, QFormLayout, QLabel, QLineEdit, QWidget, QPushButton, QHBoxLayout, \
    QVBoxLayout, QListView, QTextEdit, QTreeWidget, QTreeWidgetItem
from qasync import asyncSlot
from loguru import logger
logger.add('log.log')


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.connect_channel_button = None
        self.channel_data = []
        self.channel_items = []

        self.password_line_edit = None
        self.send_text_line_edit = None
        self.chat_view = None
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
        self.server_line_edit = QLineEdit()
        layout.addWidget(self.server_line_edit)

        layout.addWidget(QLabel('Nickname:'))
        self.nickname_line_edit = QLineEdit()
        layout.addWidget(self.nickname_line_edit)

        layout.addWidget(QLabel('Password:'))
        self.password_line_edit = QLineEdit()
        layout.addWidget(self.password_line_edit)

        self.button_connect = QPushButton('Подключиться!')
        layout.addWidget(self.button_connect)
        self.button_connect.clicked.connect(self.connect_button_clicked)

        widget = QWidget()
        widget.setLayout(layout)
        tabs.addTab(widget, "Подключение")

    def tab_irc(self, tabs):
        layout = QHBoxLayout()
        layout_left = QVBoxLayout()
        layout_right = QVBoxLayout()

        self.channel_view = QTreeWidget()
        self.channel_view.headerItem().setText(0, "Название:")
        self.channel_view.headerItem().setText(1, "Users:")
        layout_left.addWidget(self.channel_view)
        self.connect_channel_button = QPushButton('Подключиться к каналу')
        layout_left.addWidget(self.connect_channel_button)
        self.connect_channel_button.clicked.connect(self.connect_channel)

        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        self.chat_view.setText('...')
        layout_right.addWidget(self.chat_view)
        self.send_text_line_edit = QLineEdit()
        layout_right.addWidget(self.send_text_line_edit)
        self.send_text_line_edit.returnPressed.connect(self.text_enter_pressed)

        layout.addLayout(layout_left, stretch=1)
        layout.addLayout(layout_right, stretch=3)

        widget = QWidget()
        widget.setLayout(layout)
        tabs.addTab(widget, "Irc")

    @asyncSlot()
    async def connect_button_clicked(self):
        addr, nickname, passwd = (
            self.server_line_edit.text(),
            self.nickname_line_edit.text(),
            self.password_line_edit.text()
        )

        logger.info(f'Подключаемся к {addr} | Nickname: {nickname} Password: {passwd}')
        # Вызов подключения

    @asyncSlot()
    async def text_enter_pressed(self):
        text = self.send_text_line_edit.text()
        logger.info(f'Отправляем текст {text}')
        # Вызов отправки сообщения
        self.send_text_line_edit.clear()

    @asyncSlot()
    async def connect_channel(self):
        for index, item in enumerate(self.channel_items):
            if item.isSelected():
                logger.info(f'Connect to channel {self.channel_data[i]}')
                break

    def change_channels_list(self, list_channels: list[tuple[str, int]]) -> None:
        logger.info(f'New list channels {list_channels}')
        self.channel_view.clear()
        self.channel_data.clear()
        self.channel_items.clear()
        for name, count in list_channels:
            current_tree_item = QTreeWidgetItem(self.channel_view)
            current_tree_item.setText(0, name)
            current_tree_item.setText(1, count)
            self.channel_items.append(current_tree_item)
            self.channel_data.append((name, count))

    def change_chat_view(self, text: list[str]) -> None:
        logger.info(f'New chat text: {text}')
        pass
