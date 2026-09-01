"""
models/payment.py
---------------------
One Payment row per Order, tracking the Stripe side of things separately
from the Order's own payment_status column (Order.payment_status is the
quick "is this order paid?" flag other queries filter on; Payment is the
detailed audit trail — which Stripe object, what method, when).
"""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class PaymentTransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True)

    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), default="stripe", nullable=False)
    # Stripe Checkout Session id at creation time; updated to the Stripe
    # PaymentIntent id once the webhook confirms payment (see routes/checkout.py).
    transaction_id = Column(String(255), nullable=True, index=True)
    status = Column(Enum(PaymentTransactionStatus), default=PaymentTransactionStatus.PENDING, nullable=False)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="payment")

    def __repr__(self) -> str:
        return f"<Payment order_id={self.order_id} amount={self.amount} status={self.status}>"
