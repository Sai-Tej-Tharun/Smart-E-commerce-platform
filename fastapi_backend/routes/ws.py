"""
routes/ws.py
---------------
WS /ws/notifications?token=<access_token>

Browsers' native WebSocket API can't set an Authorization header, so the
JWT access token is passed as a query parameter instead — the same token
GET /auth/me would accept, decoded with the same core.security.decode_token
used everywhere else, just wired in manually since WebSocket auth doesn't
go through the normal Depends(get_current_user) HTTP flow.

Once connected, the client just listens — this endpoint doesn't accept
messages from the browser, it only pushes two event types (see
core/ws_manager.py's docstring):
  {"event": "order_status_updated", "order_id": ..., "notification_type": ..., "message": ...}
  {"event": "cart_updated", "total_items": ..., "grand_total": ...}
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from core.database import SessionLocal
from core.security import decode_token
from core.ws_manager import manager
from models.user import User

router = APIRouter(tags=["Real-Time"])


@router.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket, token: str = ""):
    db = SessionLocal()
    try:
        email = decode_token(token, expected_type="access")
    except (JWTError, Exception):
        await websocket.close(code=4401)  # custom close code: unauthorized
        db.close()
        return

    user = db.query(User).filter(User.email == email).first()
    if not user:
        await websocket.close(code=4401)
        db.close()
        return
    db.close()

    await manager.connect(user.id, websocket)
    try:
        while True:
            # This endpoint is push-only, but we still need to await
            # something so the server notices a client disconnect (browser
            # tab closed, network drop) promptly rather than leaking the
            # connection in the manager's registry.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)