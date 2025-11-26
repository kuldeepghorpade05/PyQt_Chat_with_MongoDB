# 📌 PyQt Chat with MongoDB

A real-time chat application built with **PyQt5**, **Python Socket.IO**, and **MongoDB Atlas**, supporting multiple users, message history, and private messaging.

---

## 🚀 Features

* Real-time chat using **Socket.IO**
* WhatsApp-style GUI made with **PyQt5 (Qt Designer)**
* Message history stored in **MongoDB Atlas**
* Private (one-to-one) messaging
* User colors, typing indicators, and timestamps
* Multiple clients can run on different machines

---

## 🛠 Technologies Used

### **Backend**

* **Python 3.8+**
* **python-socketio (aiohttp backend)**
* **aiohttp**
* **pymongo** (MongoDB driver)
* **dnspython** (MongoDB Atlas DNS support)

### **Frontend**

* **PyQt5**
* **Qt Designer (.ui file)**
* **Python Socket.IO client**

### **Database**

* **MongoDB Atlas (Cloud MongoDB)**
  *(You can also use local MongoDB if needed)*

---

## 📦 Installation

### 1️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Application

### 2️⃣ Start the server

```bash
python server.py
```

### 3️⃣ Start the client (run multiple times to simulate multiple users)

```bash
python client.py
```

Each client window represents a different user.

---

## 📁 Project Structure

```
PyQt_Chat_with_MongoDB/
│── client.py            # PyQt frontend client
│── server.py            # Socket.IO + MongoDB backend
│── message_bubble.py    # Custom chat bubble widget
│── chat.ui              # Qt Designer UI file
│── requirements.txt     # Dependencies
│── README.md
```


