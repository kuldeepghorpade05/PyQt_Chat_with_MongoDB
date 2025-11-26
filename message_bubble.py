from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from datetime import datetime


class MessageBubble(QWidget):
    def __init__(self, username, text, is_self=False, timestamp=None, bubble_color=None):
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        if is_self:
            bubble_color = "#DCF8C6"
        else:
            bubble_color = bubble_color or "#EDEDED"

        # Username label
        lbl_user = QLabel(username)
        lbl_user.setStyleSheet("font-weight: bold;")
        lbl_user.setAlignment(Qt.AlignRight if is_self else Qt.AlignLeft)
        layout.addWidget(lbl_user)

        # Message text
        lbl_msg = QLabel(text)
        lbl_msg.setWordWrap(True)
        lbl_msg.setAlignment(Qt.AlignRight if is_self else Qt.AlignLeft)
        lbl_msg.setStyleSheet(f"background-color: {bubble_color}; padding:5px; border-radius:5px;")
        layout.addWidget(lbl_msg)

        # Timestamp
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted = dt.strftime("%b %d, %I:%M %p")   # Nov 26, 03:34 PM
            except:
                formatted = timestamp

            lbl_time = QLabel(formatted)
            lbl_time.setStyleSheet("font-size: 8pt; color: gray;")
            lbl_time.setAlignment(Qt.AlignRight if is_self else Qt.AlignLeft)
            layout.addWidget(lbl_time)



        layout.setAlignment(Qt.AlignRight if is_self else Qt.AlignLeft)
        self.setLayout(layout)
