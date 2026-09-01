"""
models/return_request.py
----------------------------
ReturnRequest = one customer-initiated return/refund request against a
DELIVERED order. Its own status (pending/approved/rejected) is separate
from Order.order_status — placing a request immediately flips the order
to RETURN_REQUESTED (see routes/orders.py's request_return()), but
approving or rejecting the request itself is a further step this
milestone's spec doesn't ask for yet (it's scoped to the "User-side"
request flow only) — for now, an admin can change a ReturnRequest's
status directly in the Django admin (see django_admin/storefront/admin.py),
but nothing automated happens when they do. That's a deliberate scope
boundary, not an oversight — noted here so it isn't mistaken for one.
"""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class ReturnRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    reason = Column(String(200), nullable=False)
    comment = Column(Text, nullable=True)  # optional, per the spec
    status = Column(Enum(ReturnRequestStatus), default=ReturnRequestStatus.PENDING, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<ReturnRequest order_id={self.order_id} status={self.status}>"