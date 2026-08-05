import os
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, JSON
from sqlalchemy.orm import declarative_base
from src.utils.db import engine

Base = declarative_base()


class Meeting(Base):
    __tablename__ = "meetings"
    
    meeting_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_date = Column(String, nullable=False)
    transcript_hash = Column(String, nullable=False, unique=True)
    transcript_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ActionItemDB(Base):
    __tablename__ = "action_items"
    
    item_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, nullable=False)
    action_title = Column(Text, nullable=False)
    owner_name = Column(String, nullable=False)
    raw_due_date = Column(String)
    resolved_due_date = Column(String)
    priority = Column(String, default="MEDIUM")
    confidence_score = Column(Float, default=0.0)
    quote_provenance = Column(Text, default="")
    status = Column(String, default="PENDING")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    log_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, nullable=False)
    action_hash = Column(String, nullable=False, unique=True)
    action_title = Column(Text, nullable=False)
    owner_name = Column(String, nullable=False)
    target_tool = Column(String, default="GitHub Issues")
    approved_by = Column(String, default="Human Reviewer")
    executed_at = Column(DateTime, default=datetime.utcnow)
    payload = Column(JSON)


def init_db():
    Base.metadata.create_all(bind=engine)
