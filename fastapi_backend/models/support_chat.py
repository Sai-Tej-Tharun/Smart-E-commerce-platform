"""
models/support_chat.py
---------------------------
Logs every AI support chat exchange for later analysis (per the task's
"Activity Tracking" requirement). user_id is nullable — the widget works
for logged-out visitors too, per "accessible from any page."
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class SupportChatLog(Base):
    __tablename__ = "support_chat_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    question = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    def __repr__(self) -> str:
        return f"<SupportChatLog id={self.id} user_id={self.user_id}>"