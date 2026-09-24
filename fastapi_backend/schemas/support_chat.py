"""
schemas/support_chat.py
----------------------------
Request/response shapes for POST /api/ai-support.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SupportChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


class SupportChatResponse(BaseModel):
    reply: str
    timestamp: datetime