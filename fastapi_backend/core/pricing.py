"""
core/pricing.py
------------------
Shared money math so routes/cart.py and routes/checkout.py compute totals
identically — checkout re-derives the cart's numbers rather than trusting
whatever the client last saw, so there's exactly one place this logic lives.
"""

from decimal import ROUND_HALF_UP, Decimal

from core.config import settings


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_totals(subtotal: Decimal) -> tuple[Decimal, Decimal]:
    """Returns (tax, grand_total) for a given subtotal, using settings.TAX_RATE."""
    tax = money(subtotal * Decimal(str(settings.TAX_RATE)))
    grand_total = money(subtotal + tax)
    return tax, grand_total
