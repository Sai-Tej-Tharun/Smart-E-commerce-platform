"""
core/media.py
-----------------
Local disk storage for uploaded post images.

Files are saved under fastapi_backend/media/posts/ with a generated
filename (so two users uploading "cover.jpg" never collide), and served
back out via the /media static mount registered in main.py.
"""

import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

logger = logging.getLogger("media")

BASE_DIR = Path(__file__).resolve().parent.parent  # fastapi_backend/
MEDIA_ROOT = BASE_DIR / "media"
POSTS_SUBDIR = "posts"

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


def _posts_dir() -> Path:
    d = MEDIA_ROOT / POSTS_SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_post_image(file: UploadFile) -> str:
    """
    Validates and saves an uploaded image, returning the URL path to store
    on the Post row (e.g. "/media/posts/3f2a1c9e.jpg").
    Raises ValueError on invalid content type or oversized file.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Unsupported image type: {file.content_type}")

    contents = file.file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise ValueError("Image exceeds the 5 MB size limit")

    ext = Path(file.filename or "").suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = _posts_dir() / filename

    with open(dest, "wb") as f:
        f.write(contents)

    return f"/media/{POSTS_SUBDIR}/{filename}"


def delete_post_image(image_url: Optional[str]) -> None:
    """Best-effort delete of a previously stored image (e.g. on replace or post delete)."""
    if not image_url:
        return
    try:
        relative = image_url.removeprefix("/media/")
        path = MEDIA_ROOT / relative
        if path.exists() and path.is_file():
            path.unlink()
    except Exception:
        logger.exception("Failed to delete post image at %s", image_url)