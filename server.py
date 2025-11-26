import asyncio
import socketio
from aiohttp import web
from datetime import datetime, timezone
from pymongo import MongoClient

sio = socketio.AsyncServer(cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

mongo = MongoClient(
    "mongodb+srv://kuldeepghorpade05:t1AKIvdPddARgzCp@flask-project-01.owcxazv.mongodb.net/pyqt_chat_db?retryWrites=true&w=majority"
)
db = mongo["pyqt_chat_db"]
messages_coll = db["messages"]

users = {}      # sid -> username
sid_map = {}    # username -> sid

# ----------------- Unique colors -----------------
USER_COLORS = {}
COLOR_LIST = [
    "#FFD700", "#87CEEB", "#FFB6C1", "#98FB98", "#FFA07A",
    "#DDA0DD", "#00CED1", "#FF6347", "#40E0D0", "#F08080"
]
color_index = 0

# ----------------- Socket Events -----------------
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def register(sid, data):
    global color_index
    username = data.get('username', f'User_{sid[:5]}')
    users[sid] = username
    sid_map[username] = sid

    # Assign unique color
    if username not in USER_COLORS:
        USER_COLORS[username] = COLOR_LIST[color_index % len(COLOR_LIST)]
        color_index += 1

    print(f"{username} registered with sid {sid}")

    # Send user list and color mapping to all clients
    await broadcast_userlist()
    await sio.emit('user_colors', {'colors': USER_COLORS})

    # Send recent messages
    recent = list(messages_coll.find().sort('timestamp', -1).limit(100))
    recent.reverse()
    history = [
        {
            'username': m.get('username'),
            'text': m.get('text'),
            'timestamp': m.get('timestamp').isoformat(),
            'to': m.get('to')
        } for m in recent
    ]
    await sio.emit('history', {'messages': history}, room=sid)

@sio.event
async def message(sid, data):
    username = users.get(sid, 'Unknown')
    text = data.get('text', '')
    ts = datetime.now(timezone.utc)
    private_to = data.get('to', None)

    # Save to DB
    messages_coll.insert_one({
        'username': username,
        'text': text,
        'timestamp': ts,
        'to': private_to
    })

    msg_data = {
        'username': username,
        'text': text,
        'timestamp': ts.isoformat(),
        'to': private_to
    }

    if private_to:
        target_sid = sid_map.get(private_to)
        if target_sid:
            await sio.emit('message', msg_data, room=target_sid)
        await sio.emit('message', msg_data, room=sid)
    else:
        await sio.emit('message', msg_data)

@sio.event
async def typing(sid, data):
    username = users.get(sid, 'Unknown')
    await sio.emit('typing', {'username': username}, skip_sid=sid)

@sio.event
async def disconnect(sid):
    username = users.pop(sid, None)
    sid_map.pop(username, None)
    print(f"Client disconnected: {sid} ({username})")
    await broadcast_userlist()

# ----------------- Helper -----------------
async def broadcast_userlist():
    user_list = list(users.values())
    await sio.emit('user_list', {'users': user_list})

# ----------------- Run -----------------
if __name__ == '__main__':
    web.run_app(app, port=5000)
