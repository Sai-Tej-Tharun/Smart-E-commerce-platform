"""
core/scheduler.py
-----------------
Auto-publishes scheduled blog posts when their scheduled_at time arrives.

A background asyncio task wakes every INTERVAL seconds and flips every due
post from "scheduled" to "published" (recording published_at). The update is a
single atomic UPDATE ... WHERE, so it is safe even with several workers.
"""

import asyncio
import logging
from datetime import datetime, timezone

from core.database import SessionLocal
from models.blog import POST_PUBLISHED, POST_SCHEDULED, Post

logger = logging.getLogger("scheduler")

INTERVAL_SECONDS = 30


def publish_due_posts() -> int:
    """Publish every scheduled post whose time has come. Returns how many were published."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db = SessionLocal()
    try:
        count = (
            db.query(Post)
            .filter(Post.status == POST_SCHEDULED, Post.scheduled_at <= now)
            .update(
                {Post.status: POST_PUBLISHED, Post.published_at: now},
                synchronize_session=False,
            )
        )
        db.commit()
        return count
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def scheduler_loop(interval: int = INTERVAL_SECONDS) -> None:
    logger.info("Blog scheduler started (every %ss)", interval)
    while True:
        try:
            published = await asyncio.to_thread(publish_due_posts)
            if published:
                logger.info("Auto-published %s scheduled post(s)", published)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduler run failed")
        await asyncio.sleep(interval)