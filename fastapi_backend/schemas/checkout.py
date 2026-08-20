from pydantic import BaseModel

from schemas.order import OrderOut


class CheckoutResponse(BaseModel):
    order: OrderOut
    checkout_url: str
    session_id: str
