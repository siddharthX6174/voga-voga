from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from db.database import Base
import datetime

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    sender = Column(String)  # 'user' or 'agent'
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
