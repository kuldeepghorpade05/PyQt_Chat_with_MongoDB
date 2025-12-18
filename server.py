import os
import socketio
from aiohttp import web
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

# ----------------- Load environment variables -----------------
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME")

if not MONGO_URI or not DB_NAME:
    raise RuntimeError("Missing MONGODB_URI or MONGODB_DB_NAME environment variables")

# ----------------- Socket.IO setup -----------------
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode="aiohttp",
    ping_timeout=60,
    ping_interval=25
)

app = web.Application()
sio.attach(app)

# ----------------- MongoDB setup -----------------
mongo = MongoClient(MONGO_URI)
db = mongo[DB_NAME]
messages_coll = db["messages"]

# ----------------- In-memory user tracking -----------------
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

    username = data.get("username", f"User_{sid[:5]}")
    users[sid] = username
    sid_map[username] = sid

    if username not in USER_COLORS:
        USER_COLORS[username] = COLOR_LIST[color_index % len(COLOR_LIST)]
        color_index += 1

    print(f"{username} registered")

    await broadcast_userlist()
    await sio.emit("user_colors", {"colors": USER_COLORS})

    recent = list(messages_coll.find().sort("timestamp", -1).limit(100))
    recent.reverse()

    history = [
        {
            "username": m["username"],
            "text": m["text"],
            "timestamp": m["timestamp"].isoformat(),
            "to": m.get("to")
        } for m in recent
    ]

    await sio.emit("history", {"messages": history}, room=sid)

@sio.event
async def message(sid, data):
    username = users.get(sid, "Unknown")
    text = data.get("text", "")
    private_to = data.get("to")
    ts = datetime.now(timezone.utc)

    messages_coll.insert_one({
        "username": username,
        "text": text,
        "timestamp": ts,
        "to": private_to
    })

    msg = {
        "username": username,
        "text": text,
        "timestamp": ts.isoformat(),
        "to": private_to
    }

    if private_to:
        target_sid = sid_map.get(private_to)
        if target_sid:
            await sio.emit("message", msg, room=target_sid)
        await sio.emit("message", msg, room=sid)
    else:
        await sio.emit("message", msg)

@sio.event
async def typing(sid, data):
    username = users.get(sid, "Unknown")
    await sio.emit("typing", {"username": username}, skip_sid=sid)

@sio.event
async def disconnect(sid):
    username = users.pop(sid, None)
    if username:
        sid_map.pop(username, None)
    print(f"Client disconnected: {username}")
    await broadcast_userlist()

# ----------------- Helper -----------------
async def broadcast_userlist():
    await sio.emit("user_list", {"users": list(users.values())})

# ----------------- Run app -----------------
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    web.run_app(app, host="0.0.0.0", port=PORT)
