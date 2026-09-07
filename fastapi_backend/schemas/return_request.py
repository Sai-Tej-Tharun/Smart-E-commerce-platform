from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ReturnRequestCreate(BaseModel):
    reason: str = Field(min_length=1, max_length=200)
    comment: Optional[str] = None


class ReturnRequestOut(BaseModel):
    id: int
    order_id: int
    reason: str
    comment: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True



class ReturnRequestAdminOut(ReturnRequestOut):
    """NEW (Admin-side Refund Processing milestone). Same fields as
    ReturnRequestOut, plus a bit of extra context an admin reviewing the
    queue actually needs — who asked, and how much is on the line —
    without having to separately look up the order."""
    user_id: int
    user_email: str
    order_status: str
    order_total: Decimal


class RefundResultOut(BaseModel):
    """Response for POST /admin/returns/{id}/approve — the return request
    plus what actually happened with the refund, since "approved" and
    "refund succeeded" are two different facts worth surfacing separately."""
    return_request: ReturnRequestOut
    order_status: str
    payment_status: str
    stripe_refund_id: str