from datetime import datetime
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