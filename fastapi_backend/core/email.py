"""
core/email.py
----------------
Plain SMTP email sending — deliberately not tied to any one provider's
SDK. Point SMTP_HOST/PORT/USER/PASSWORD (in .env) at:
  - a plain SMTP server, or
  - SendGrid's SMTP relay (smtp.sendgrid.net, port 587, username "apikey",
    password = your SendGrid API key), or
  - AWS SES's SMTP interface (email-smtp.<region>.amazonaws.com, port 587,
    using SES SMTP credentials, not your AWS access key directly)
...and this same code sends through any of them — only the .env values
change. For local development, point it at a free Mailtrap.io inbox
instead of a real mail account (see the Screenshot Guide).

If SMTP_HOST is left blank, send_email() logs the email instead of
sending it, so the rest of the app (and any automated test) still works
without a real mail account configured — the same graceful-degradation
pattern used for Stripe (core/stripe_client.py) and Auth0.
"""

import logging
import smtplib
from email.message import EmailMessage

from core.config import settings

logger = logging.getLogger("email")


def send_email(to: str, subject: str, body: str) -> bool:
    """Returns True if the email was actually sent, False if it was only logged."""
    if not settings.SMTP_HOST:
        logger.info("SMTP not configured — logging email instead of sending.\nTo: %s\nSubject: %s\n%s", to, subject, body)
        return False

    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)

    logger.info("Email sent to %s: %s", to, subject)
    return True