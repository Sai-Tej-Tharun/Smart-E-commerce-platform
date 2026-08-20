"""
core/stripe_client.py
------------------------
Configures the Stripe SDK once, from settings, so route modules just
`import stripe` and call it — the API key is set as a module-level side
effect the first time this file is imported (see routes/checkout.py).
"""

import stripe

from core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
