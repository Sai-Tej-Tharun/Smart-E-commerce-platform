"""
services/notification_service.py
-------------------------------------
Business logic for blog activity notifications: decides WHETHER to notify
(skip notifying users about their own actions) and WHAT to say, then
delegates the actual sending to services/email_service.py.

Called from routes/blog.py's add_comment and like_post, scheduled via
FastAPI BackgroundTasks so the API response isn't held up by SMTP.
"""

from datetime import datetime

from models.blog import Post
from models.user import User
from services.email_service import send_post_activity_email


def notify_post_owner_of_comment(post: Post, commenter: User) -> None:
    """No-op if the commenter is the post's own author — you don't need an
    email telling you that you commented on your own post."""
    if post.author_id == commenter.id or not post.author:
        return
    send_post_activity_email(
        to=post.author.email,
        post_title=post.title,
        actor_name=commenter.name,
        activity_label="Commented on your post",
        timestamp=datetime.utcnow(),
    )


def notify_post_owner_of_like(post: Post, liker: User) -> None:
    """No-op if the liker is the post's own author, same reasoning as above."""
    if post.author_id == liker.id or not post.author:
        return
    send_post_activity_email(
        to=post.author.email,
        post_title=post.title,
        actor_name=liker.name,
        activity_label="Liked your post",
        timestamp=datetime.utcnow(),
    )