"""
models/order.py
------------------
Order = one checkout attempt. OrderItem = one product line within that
order, a snapshot of product_name/unit_price at the moment of checkout —
deliberately NOT a live join to Product, so an order's history stays
accurate even if the product's price or name changes later.

Two separate status fields, on purpose:
  order_status   — the fulfillment lifecycle: pending -> paid -> shipped
                    -> delivered (or -> cancelled at any point before
                    shipped). Admins move this forward from the Django
                    admin panel as the order physically progresses.
  payment_status — just the payment side: pending -> paid / failed /
                    refunded. Driven by Stripe webhook events
                    (routes/checkout.py), not by admin action.
"""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)

    order_status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order id={self.id} user_id={self.user_id} total={self.total} status={self.order_status}>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)

    # Snapshotted at checkout time — see module docstring.
    product_name = Column(String(200), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    def __repr__(self) -> str:
        return f"<OrderItem order_id={self.order_id} product={self.product_name} qty={self.quantity}>"
