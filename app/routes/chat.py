from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, Set, Tuple
import json
import time

router = APIRouter()

def room_key(a: int, b: int) -> Tuple[int, int]:
    return (a, b) if a < b else (b, a)

rooms: Dict[Tuple[int, int], Set[WebSocket]] = {}

@router.websocket("/ws/chat")
async def ws_chat(
    websocket: WebSocket,
    me: int = Query(...),
    other: int = Query(...),
):
    await websocket.accept()
    key = room_key(me, other)
    rooms.setdefault(key, set()).add(websocket)

    await websocket.send_text(json.dumps({
        "type": "system",
        "text": "Conectado al chat",
        "ts": time.time(),
    }))

    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
                text = (data.get("text") or "").strip()
            except Exception:
                text = msg.strip()

            if not text:
                continue

            payload = json.dumps({
                "type": "message",
                "from": me,
                "to": other,
                "text": text,
                "ts": time.time(),
            })

            for ws in list(rooms.get(key, set())):
                try:
                    await ws.send_text(payload)
                except Exception:
                    pass

    except WebSocketDisconnect:
        pass
    finally:
        rooms.get(key, set()).discard(websocket)
        if key in rooms and not rooms[key]:
            rooms.pop(key, None)
