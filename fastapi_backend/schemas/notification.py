from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    type: str
    message: str
    read_status: bool
    timestamp: datetime

    class Config:
        from_attributes = True


class NotificationListOut(BaseModel):
    notifications: List[NotificationOut]
    unread_count: int


class MarkReadRequest(BaseModel):
    # Omit notification_id to mark every one of the current user's
    # notifications as read in one call.
    notification_id: Optional[int] = None


class InternalNotifyRequest(BaseModel):
    """Body for POST /internal/notifications — called by django_admin, not
    the frontend. See core/config.py's INTERNAL_API_SECRET."""
    user_id: int
    order_id: int
    event: str  # "order_shipped" | "order_delivered"