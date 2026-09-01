"""
core/notify.py
------------------
notify_user() is the one function every order-event trigger calls
(the Stripe webhook in routes/checkout.py, and the internal endpoint in
routes/notifications.py that django_admin calls) — it does all three
things the milestone asks for, in one place, so no trigger point can
accidentally do one but forget another:
  1. Writes a Notification row (in-app list, GET /notifications)
  2. Sends an email (core/email.py)
  3. Pushes a real-time WebSocket event, if the user has one open (core/ws_manager.py)

`db` here is a plain, callable-scoped Session (not the get_db generator) —
notify_user is called from contexts (webhooks, background triggers) that
manage their own session lifetime rather than FastAPI's per-request one.
"""

import logging

from sqlalchemy.orm import Session

from core.email import send_email
from core.ws_manager import manager
from models.notification import Notification, NotificationType
from models.user import User

logger = logging.getLogger("notify")

# One place to keep the in-app message + email subject/body template per
# event type, so adding a new notification type later means adding one
# entry here, not touching every call site.
_TEMPLATES = {
    NotificationType.ORDER_CONFIRMED: {
        "message": "Order #{order_id} confirmed — thanks for shopping with us!",
        "subject": "Your GlowVeda order #{order_id} is confirmed",
        "body": "Hi {name},\n\nYour order #{order_id} has been confirmed. We'll email you again once it ships.\n\nTotal: ₹{total}\n\n— GlowVeda",
    },
    NotificationType.PAYMENT_SUCCESSFUL: {
        "message": "Payment of ₹{total} for order #{order_id} was successful.",
        "subject": "Payment received for order #{order_id}",
        "body": "Hi {name},\n\nWe've received your payment of ₹{total} for order #{order_id}.\n\n— GlowVeda",
    },
    NotificationType.PAYMENT_FAILED: {
        "message": "Payment for order #{order_id} failed. You can try checking out again.",
        "subject": "Payment failed for order #{order_id}",
        "body": "Hi {name},\n\nYour payment for order #{order_id} did not go through. No charge was made — feel free to try checking out again.\n\n— GlowVeda",
    },
    NotificationType.ORDER_SHIPPED: {
        "message": "Order #{order_id} has shipped!",
        "subject": "Your GlowVeda order #{order_id} has shipped",
        "body": "Hi {name},\n\nGood news — order #{order_id} is on its way.\n\n— GlowVeda",
    },
    NotificationType.ORDER_DELIVERED: {
        "message": "Order #{order_id} was delivered. Enjoy!",
        "subject": "Your GlowVeda order #{order_id} was delivered",
        "body": "Hi {name},\n\nOrder #{order_id} has been marked delivered. We hope you love it!\n\n— GlowVeda",
    },
}


async def notify_user(db: Session, user: User, notif_type: NotificationType, order_id: int, total: str = "") -> Notification:
    """
    async because step 3 (the WebSocket push) needs to run on the same
    event loop the connection lives on. Every call site is itself inside
    an async route/handler (see routes/checkout.py, routes/notifications.py)
    so this is always `await`ed, never fire-and-forgotten — a much simpler
    and more reliable approach than scheduling work onto another thread's
    event loop (an earlier version of this file tried that and deadlocked
    under real testing; see the note in core/ws_manager.py).
    """
    template = _TEMPLATES[notif_type]
    fmt_args = {"order_id": order_id, "name": user.name, "total": total}

    # 1. In-app notification row
    notification = Notification(
        user_id=user.id,
        type=notif_type,
        message=template["message"].format(**fmt_args),
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # 2. Email (logs instead of sending if SMTP isn't configured — see
    # core/email.py). send_email is a blocking smtplib call; for this
    # project's scope that's an acceptable trade-off (briefly blocks the
    # event loop rather than adding a background task queue), and it only
    # runs on the few requests that trigger a notification, not every request.
    try:
        send_email(to=user.email, subject=template["subject"].format(**fmt_args), body=template["body"].format(**fmt_args))
    except Exception:
        logger.exception("Failed to send notification email to %s", user.email)

    # 3. Real-time push, if the user has a WebSocket open right now —
    # awaited directly, same event loop as the connection.
    event = {
        "event": "order_status_updated",
        "order_id": order_id,
        "notification_type": notif_type.value,
        "message": notification.message,
    }
    await manager.send_to_user(user.id, event)

    return notification