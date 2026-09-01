"""
core/realtime.py
--------------------
broadcast_cart_updated() is a small shared helper so routes/cart.py and
routes/checkout.py don't each reimplement the cart_updated event payload.

It's async and meant to be awaited from an async route handler — see the
note in core/notify.py for why: pushing a WebSocket message has to happen
on the same event loop the connection lives on, which means either
"await it directly from async code" (what this does) or "schedule it
thread-safely onto that loop" (more moving parts, not needed once the
handlers that need this are themselves async).
"""

from core.ws_manager import manager
from schemas.cart import CartOut


async def broadcast_cart_updated(user_id: int, cart: CartOut) -> None:
    event = {"event": "cart_updated", "total_items": cart.total_items, "grand_total": str(cart.grand_total)}
    await manager.send_to_user(user_id, event)