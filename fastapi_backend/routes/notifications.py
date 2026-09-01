"""
routes/notifications.py
---------------------------
GET  /notifications          - the current user's notifications, newest first
POST /notifications/read     - mark one notification read (pass
                                {"notification_id": N}) or all of them
                                (omit the body / pass {})
POST /internal/notifications - NOT customer-facing. django_admin calls
                                this (with a shared secret, not a user's
                                JWT) when an admin marks an order shipped
                                or delivered — see
                                django_admin/storefront/signals.py. This
                                is what lets a Django-side action still
                                produce a real-time WebSocket push, an
                                email, and an in-app row through FastAPI,
                                which is the only process holding both the
                                notifications table logic and the open
                                WebSocket connections.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.notify import notify_user
from core.security import get_current_user
from models.notification import Notification, NotificationType
from models.order import Order
from models.user import User
from schemas.notification import InternalNotifyRequest, MarkReadRequest, NotificationListOut, NotificationOut

router = APIRouter(tags=["Notifications"])


@router.get("/notifications", response_model=NotificationListOut)
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.timestamp.desc())
        .all()
    )
    unread_count = sum(1 for n in rows if not n.read_status)
    return NotificationListOut(notifications=[NotificationOut.model_validate(n) for n in rows], unread_count=unread_count)


@router.post("/notifications/read", response_model=NotificationListOut)
def mark_notifications_read(
    payload: MarkReadRequest = MarkReadRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if payload.notification_id is not None:
        notification = query.filter(Notification.id == payload.notification_id).first()
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        notification.read_status = True
    else:
        query.filter(Notification.read_status.is_(False)).update({"read_status": True})
    db.commit()
    return list_notifications(current_user=current_user, db=db)


_EVENT_TO_TYPE = {
    "order_shipped": NotificationType.ORDER_SHIPPED,
    "order_delivered": NotificationType.ORDER_DELIVERED,
}


@router.post("/internal/notifications", include_in_schema=False)
async def internal_notify(
    payload: InternalNotifyRequest,
    db: Session = Depends(get_db),
    x_internal_secret: str = Header(default=""),
):
    if x_internal_secret != settings.INTERNAL_API_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal secret")

    notif_type = _EVENT_TO_TYPE.get(payload.event)
    if not notif_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown event '{payload.event}'")

    user = db.query(User).filter(User.id == payload.user_id).first()
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not user or not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or order not found")

    await notify_user(db, user, notif_type, order_id=order.id, total=str(order.total))
    return {"status": "notified"}