"""
routes/support.py
----------------------
POST /api/ai-support - send a message, get an AI-generated (or FAQ-matched)
reply. Works for logged-out visitors too — the chat widget is meant to be
usable from any page, per the task brief — and logs the exchange with the
user attached whenever one is logged in.
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.ai_support import get_ai_reply
from core.database import get_db
from core.security import get_current_user_optional
from models.support_chat import SupportChatLog
from models.user import User
from schemas.support_chat import SupportChatRequest, SupportChatResponse

router = APIRouter(prefix="/api", tags=["AI Support"])


@router.post("/ai-support", response_model=SupportChatResponse)
def ai_support_chat(
    payload: SupportChatRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    reply = get_ai_reply(payload.message)

    log_row = SupportChatLog(
        user_id=current_user.id if current_user else None,
        question=payload.message,
        ai_response=reply,
    )
    db.add(log_row)
    db.commit()

    return SupportChatResponse(reply=reply, timestamp=datetime.utcnow())