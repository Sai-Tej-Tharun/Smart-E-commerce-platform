"""
services/email_service.py
------------------------------
Thin, purpose-built wrapper around core/email.send_email() for blog
activity notifications (comments and likes).

core/email.py stays the single place that knows about SMTP/.env — this
module only knows how to format a "someone liked/commented on your post"
email and hand it off. Keeping SMTP mechanics out of here means a future
switch to fastapi-mail, SES's API, etc. only touches core/email.py.
"""

import logging
from datetime import datetime

from core.email import send_email

logger = logging.getLogger("email_service")

TIMESTAMP_FORMAT = "%Y-%m-%d %I:%M %p"  # e.g. "2026-03-04 11:20 AM"


def _format_activity_email(post_title: str, actor_name: str, activity_label: str, timestamp: datetime) -> tuple[str, str]:
    """Returns (subject, body) for a like/comment notification email."""
    subject = f"New activity on your post: {post_title}"
    body = (
        f"Post: \"{post_title}\"\n"
        f"User: {actor_name}\n"
        f"Activity: {activity_label}\n"
        f"Time: {timestamp.strftime(TIMESTAMP_FORMAT)}"
    )
    return subject, body


def send_post_activity_email(
    to: str,
    post_title: str,
    actor_name: str,
    activity_label: str,
    timestamp: datetime,
) -> bool:
    """
    Sends the formatted activity email. Returns True if actually sent,
    False if only logged (SMTP not configured — see core/email.py).
    Never raises: errors are caught and logged so a failed email can
    never break the request that triggered it.
    """
    subject, body = _format_activity_email(post_title, actor_name, activity_label, timestamp)
    try:
        return send_email(to=to, subject=subject, body=body)
    except Exception:
        logger.exception("Failed to send post-activity email to %s", to)
        return False