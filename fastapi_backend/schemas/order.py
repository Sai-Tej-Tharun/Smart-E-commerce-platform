from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class OrderItemOut(BaseModel):
    id: int
    product_id: Optional[int]
    product_name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    id: int
    amount: Decimal
    payment_method: str
    transaction_id: Optional[str]
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    order_status: str
    payment_status: str
    created_at: datetime
    items: List[OrderItemOut]
    payment: Optional[PaymentOut]

    class Config:
        from_attributes = True
