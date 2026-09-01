"""
core/ws_manager.py
----------------------
A simple in-memory registry of live WebSocket connections, keyed by
user_id — one user can have several (e.g. two browser tabs), so each
user_id maps to a list of sockets. This lives as a single module-level
instance (`manager`, at the bottom) shared by every request in this
process, which is exactly right for a single-server demo — it does NOT
survive a restart and does NOT work across multiple server processes
without extra work (a real multi-instance deployment would swap this for
a Redis pub/sub channel instead; noted here rather than built, since it's
outside this milestone's scope).

Every route that pushes an event through this manager is itself
`async def` and `await`s the send directly (see core/notify.py,
core/realtime.py, routes/cart.py, routes/checkout.py). This matters:
FastAPI runs plain `def` route handlers in a worker-thread pool, where
`asyncio.get_event_loop()` does not see the event loop the WebSocket
connection actually lives on — a "fire and forget" push scheduled that
way can silently deadlock instead of sending. Converting the handlers
that need to push an event to `async def` avoids that entirely; there's
no thread/loop mismatch to work around if everything just stays on one
event loop and awaits normally.

Two event types are broadcast, matching the spec:
  order_status_updated — sent whenever an order's order_status or
                          payment_status changes (checkout webhook, or
                          Django admin marking shipped/delivered)
  cart_updated          — sent whenever the user's own cart changes
                          (add/update/remove), so a second open tab stays
                          in sync without polling
"""

import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger("ws")


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)
        logger.info("WebSocket connected for user_id=%s (now %d connection(s))", user_id, len(self._connections[user_id]))

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        sockets = self._connections.get(user_id, [])
        if websocket in sockets:
            sockets.remove(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, event: dict) -> None:
        """Best-effort push — if the user has no open socket, this is a no-op.
        The Notification row / email already happened before this is called,
        so a missed real-time push never means a missed notification, only
        a missed *instant* one (the user still sees it next time they open
        GET /notifications)."""
        for websocket in list(self._connections.get(user_id, [])):
            try:
                await websocket.send_json(event)
            except Exception:
                self.disconnect(user_id, websocket)


manager = ConnectionManager()