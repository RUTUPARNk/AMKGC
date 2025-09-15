from datetime import datetime
from .websocket import broadcast

async def session_created(session_id: str, metadata: dict):
    event = {
        "type": "SESSION_CREATED",
        "session_id": session_id,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        **metadata
    }
    await broadcast(event)

async def session_updated(session_id: str, metadata: dict):
    event = {
        "type": "SESSION_UPDATED",
        "session_id": session_id,
        **metadata
    }
    await broadcast(event)

async def session_deleted(session_id: str):
    event = {
        "type": "SESSION_DELETED",
        "session_id": session_id
    }
    await broadcast(event)
