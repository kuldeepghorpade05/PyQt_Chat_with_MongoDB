import sys
import time
import threading
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QLineEdit, QPushButton, QScrollArea
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
import socketio
from message_bubble import MessageBubble

class ChatWindow(QMainWindow):
    new_message = pyqtSignal(dict)
    new_history = pyqtSignal(list)
    new_typing = pyqtSignal(str)
    new_user_list = pyqtSignal(list)
    new_user_colors = pyqtSignal(dict)

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle(f"PyQt Chat - {self.username}")
        self.resize(600, 800)
        self.private_target = None
        self.last_date = None
        self.user_colors = {}  # store colors received from server

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.typingLabel = QLabel("")
        main_layout.addWidget(self.typingLabel)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.addStretch()
        self.scrollAreaWidgetContents.setLayout(self.messages_layout)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        main_layout.addWidget(self.scrollArea)

        input_frame = QWidget()
        input_layout = QHBoxLayout(input_frame)
        self.messageInput = QLineEdit()
        self.messageInput.setPlaceholderText("Type a message")
        self.sendButton = QPushButton("Send")
        input_layout.addWidget(self.messageInput)
        input_layout.addWidget(self.sendButton)
        main_layout.addWidget(input_frame)

        self.userList = QListWidget()
        main_layout.addWidget(self.userList)

        self.typing_timer = QTimer()
        self.typing_timer.setSingleShot(True)
        self.typing_timer.timeout.connect(lambda: self.typingLabel.setText(''))

        self.sendButton.clicked.connect(self.send_message)
        self.messageInput.textChanged.connect(self.on_typing_trigger)
        self.userList.itemClicked.connect(self.set_private_target)

        self.new_message.connect(self.handle_new_message)
        self.new_history.connect(self.handle_new_history)
        self.new_typing.connect(self.handle_new_typing)
        self.new_user_list.connect(self.handle_new_user_list)
        self.new_user_colors.connect(self.handle_new_user_colors)

        self.socket = socketio.Client()
        self.socket.on('message', self.on_message_socket)
        self.socket.on('history', self.on_history_socket)
        self.socket.on('user_list', self.on_user_list_socket)
        self.socket.on('typing', self.on_typing_socket)
        self.socket.on('user_colors', self.on_user_colors_socket)

        threading.Thread(target=self.start_socket, daemon=True).start()

    def start_socket(self):
        try:
            # ---------------- FLEXIBLE CONNECTION ----------------
            # For local testing:
            # self.socket.connect('http://localhost:5000')
            
            # For cloud deployment on Render:
            self.socket.connect('https://pyqt-chat-with-mongodb.onrender.com')
            # ------------------------------------------------------

            self.socket.emit('register', {'username': self.username})
        except Exception as e:
            print("Socket connection error:", e)


    def add_bubble(self, username, text, is_self=False, timestamp=None):
        # Add date separator
        if timestamp:
            msg_date = datetime.fromisoformat(timestamp).date()
            if msg_date != self.last_date:
                self.add_date_separator(msg_date)
                self.last_date = msg_date

        # Assign color
        color = self.user_colors.get(username, "#EDEDED") if not is_self else "#DCF8C6"
        bubble = MessageBubble(username, text, is_self, timestamp, color)

        item_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        if is_self:
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            layout.addWidget(bubble)
            layout.addStretch()
        item_widget.setLayout(layout)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, item_widget)
        QtCore.QTimer.singleShot(100, lambda: self.scrollArea.verticalScrollBar().setValue(
            self.scrollArea.verticalScrollBar().maximum()
        ))

    def add_date_separator(self, date_obj):
        separator = QLabel(date_obj.strftime('%A, %d %B %Y'))
        separator.setAlignment(Qt.AlignCenter)
        separator.setStyleSheet("font-weight:bold; color:gray; margin:10px 0;")
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, separator)

    # ---------------- Handlers ----------------
    def handle_new_message(self, data):
        username = data.get('username')
        text = data.get('text')
        ts = data.get('timestamp')
        to = data.get('to', None)
        if to is None or to == self.username or username == self.username:
            self.add_bubble(username, text, username == self.username, ts)

    def handle_new_history(self, messages):
        for m in messages:
            username = m.get('username')
            text = m.get('text')
            ts = m.get('timestamp')
            to = m.get('to', None)
            if to is None or to == self.username or username == self.username:
                self.add_bubble(username, text, username == self.username, ts)

    def handle_new_typing(self, username):
        self.typingLabel.setText(f"{username} is typing...")
        self.typing_timer.start(1000)

    def handle_new_user_list(self, users):
        self.userList.clear()
        for u in users:
            self.userList.addItem(u)

    def handle_new_user_colors(self, colors):
        self.user_colors = colors

    # ---------------- User Actions ----------------
    def set_private_target(self, item):
        target = item.text()
        if target == self.username:
            self.private_target = None
        else:
            self.private_target = target
        self.statusBar().showMessage(f"Private target: {self.private_target or 'Everyone'}")

    def on_typing_trigger(self):
        self.socket.emit('typing', {})

    def send_message(self):
        text = self.messageInput.text().strip()
        if not text:
            return
        data = {'text': text}
        if self.private_target:
            data['to'] = self.private_target
        self.socket.emit('message', data)
        self.messageInput.clear()

    # ---------------- Socket Callbacks ----------------
    def on_message_socket(self, data): self.new_message.emit(data)
    def on_history_socket(self, data): self.new_history.emit(data.get('messages', []))
    def on_user_list_socket(self, data): self.new_user_list.emit(data.get('users', []))
    def on_typing_socket(self, data):
        username = data.get('username')
        if username != self.username: self.new_typing.emit(username)
    def on_user_colors_socket(self, data): self.new_user_colors.emit(data.get('colors', {}))


class LoginDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Enter username')
        self.setModal(True)
        self.resize(300, 80)
        layout = QVBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText('Username')
        self.btn = QPushButton('Join')
        layout.addWidget(self.input)
        layout.addWidget(self.btn)
        self.setLayout(layout)
        self.btn.clicked.connect(self.accept)

    def get_username(self):
        return self.input.text().strip() or f'User_{int(time.time() % 1000)}'


def main():
    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec_() == QtWidgets.QDialog.Accepted:
        username = login.get_username()
        window = ChatWindow(username)
        window.show()
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
