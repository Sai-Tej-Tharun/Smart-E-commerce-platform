from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0, default=0)
    images: List[str] = Field(default_factory=list)
    category: str | None = None


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: Decimal
    stock: int
    images: List[str]
    category: str | None
    popularity: int
    created_at: datetime

    class Config:
        from_attributes = True
