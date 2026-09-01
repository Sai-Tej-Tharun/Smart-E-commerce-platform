"""
core/config.py
----------------
Centralized, typed application settings loaded from .env via pydantic-settings.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Smart E-Commerce Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "ecommerce_db"

    # JWT
    JWT_SECRET_KEY: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Auth0 (social login)
    AUTH0_DOMAIN: str = ""
    AUTH0_AUDIENCE: str = ""
    AUTH0_CLIENT_ID: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Cart calculations — flat-rate tax applied to the cart subtotal.
    # 0.08 = 8%. Set to 0 in .env to disable tax entirely.
    TAX_RATE: float = 0.08

    # Stripe (checkout & payments)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    # Signing secret for verifying POST /webhooks/stripe came from Stripe —
    # get this from `stripe listen` (local dev) or the Dashboard (production).
    STRIPE_WEBHOOK_SECRET: str = ""
    # Where Stripe Checkout redirects the browser after payment.
    FRONTEND_URL: str = "http://localhost:5173"
    # Matches the ₹ symbol already used throughout the storefront (Cart,
    # ProductCard, etc). Stripe supports INR test payments the same way as
    # any other currency — change this if your store should charge in USD.
    CURRENCY: str = "inr"

    # Email notifications — works with plain SMTP, or SendGrid/AWS SES via
    # their SMTP relay endpoints (e.g. SMTP_HOST=smtp.sendgrid.net,
    # SMTP_HOST=email-smtp.<region>.amazonaws.com) — same code path either
    # way, only the .env values change. Left blank, emails are logged to
    # the console instead of sent (see core/email.py) so the rest of the
    # app still works without an email account configured.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "no-reply@glowveda.example"

    # Shared secret for the one internal, non-JWT endpoint
    # (POST /internal/notifications) that django_admin calls when an admin
    # marks an order shipped/delivered — see routes/notifications.py.
    INTERNAL_API_SECRET: str = "insecure-dev-internal-secret-change-me"

        # Refund & Return milestone: how many days after delivery a customer
    # can still request a return. See routes/orders.py's request_return().
    RETURN_WINDOW_DAYS: int = 7

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def AUTH0_JWKS_URL(self) -> str:
        return f"https://{self.AUTH0_DOMAIN}/.well-known/jwks.json"

    @property
    def AUTH0_ISSUER(self) -> str:
        return f"https://{self.AUTH0_DOMAIN}/"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
