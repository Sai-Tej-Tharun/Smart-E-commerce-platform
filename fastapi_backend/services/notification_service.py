"""
services/notification_service.py
-------------------------------------
Business logic for blog activity notifications: decides WHETHER to notify
(skip notifying users about their own actions), builds the message for
each event, and delegates to core.notify.notify_user_event — which fans
each one out to all three channels the project already supports: an
in-app Notification row (the bell dropdown), an email, and a real-time
WebSocket push. This is the same helper the order-notification flow uses,
just with blog-specific messages instead of order ones.

Called from routes/blog.py's add_comment/like_post and
routes/subscriptions.py's subscribe, scheduled via FastAPI BackgroundTasks
so none of those requests are held up waiting on this.
"""

from datetime import datetime

from core.notify import notify_user_event
from models.blog import Post
from models.notification import NotificationType
from models.user import User

TIMESTAMP_FORMAT = "%Y-%m-%d %I:%M %p"  # e.g. "2026-03-04 11:20 AM"


async def notify_post_owner_of_comment(post: Post, commenter: User) -> None:
    """No-op if the commenter is the post's own author."""
    if post.author_id == commenter.id or not post.author:
        return

    timestamp = datetime.utcnow()
    message = f'{commenter.name} commented on your post "{post.title}".'
    email_body = (
        f'Post: "{post.title}"\n'
        f"User: {commenter.name}\n"
        f"Activity: Commented on your post\n"
        f"Time: {timestamp.strftime(TIMESTAMP_FORMAT)}"
    )
    await notify_user_event(
        user_id=post.author_id,
        notif_type=NotificationType.BLOG_COMMENT_RECEIVED,
        message=message,
        email_subject=f"New comment on your post: {post.title}",
        email_body=email_body,
    )


async def notify_post_owner_of_like(post: Post, liker: User) -> None:
    """No-op if the liker is the post's own author."""
    if post.author_id == liker.id or not post.author:
        return

    timestamp = datetime.utcnow()
    message = f'{liker.name} liked your post "{post.title}".'
    email_body = (
        f'Post: "{post.title}"\n'
        f"User: {liker.name}\n"
        f"Activity: Liked your post\n"
        f"Time: {timestamp.strftime(TIMESTAMP_FORMAT)}"
    )
    await notify_user_event(
        user_id=post.author_id,
        notif_type=NotificationType.BLOG_LIKE_RECEIVED,
        message=message,
        email_subject=f"Someone liked your post: {post.title}",
        email_body=email_body,
    )


async def notify_subscription_activated(user_id: int, plan_name: str, price: str, end_date: datetime) -> None:
    message = f"Your {plan_name.capitalize()} subscription is now active."
    email_body = (
        f"Plan: {plan_name.capitalize()}\n"
        f"Price: {price}\n"
        f"Valid until: {end_date.strftime('%Y-%m-%d')}\n\n"
        f"Thanks for subscribing!"
    )
    await notify_user_event(
        user_id=user_id,
        notif_type=NotificationType.SUBSCRIPTION_ACTIVATED,
        message=message,
        email_subject="Your subscription is active",
        email_body=email_body,
    )