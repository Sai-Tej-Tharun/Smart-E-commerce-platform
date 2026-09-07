"""
models/notification.py
-------------------------
One row per notification event. In-app only — this table is what
GET /notifications reads and what gets marked read_status=True by
POST /notifications/read. Email delivery (core/email.py) and the
real-time WebSocket push (core/ws_manager.py) both fire alongside a
Notification row being created, from the same call site — see
routes/checkout.py and routes/notifications.py — but neither of those is
this table's job to track; this table is purely the in-app notification
list.
"""

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class NotificationType(str, enum.Enum):
    ORDER_CONFIRMED = "order_confirmed"
    PAYMENT_SUCCESSFUL = "payment_successful"
    PAYMENT_FAILED = "payment_failed"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    RETURN_APPROVED = "return_approved"
    RETURN_REJECTED = "return_rejected"
    REFUND_COMPLETED = "refund_completed"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(NotificationType), nullable=False)
    message = Column(String(500), nullable=False)
    read_status = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    def __repr__(self) -> str:
        return f"<Notification user_id={self.user_id} type={self.type} read={self.read_status}>"