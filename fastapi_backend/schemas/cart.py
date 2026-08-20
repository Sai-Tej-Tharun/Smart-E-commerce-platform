from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, default=1)


class CartItemUpdate(BaseModel):
    item_id: int
    quantity: int = Field(ge=1)


class CartItemRemove(BaseModel):
    item_id: int


class CartItemOut(BaseModel):
    """One line in the cart, with its product snapshot and computed total."""
    id: int
    product_id: int
    product_name: str
    unit_price: Decimal
    quantity: int
    item_total: Decimal

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    """The full cart, with calculations done server-side (see routes/cart.py)."""
    items: List[CartItemOut]
    total_items: int
    subtotal: Decimal
    tax_rate: float
    tax: Decimal
    grand_total: Decimal
