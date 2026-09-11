"""Research mappings aligned with the persisted PostgreSQL tables.

The application uses asyncpg DAOs for writes; these mappings describe the same
column types for tooling and inspection. Schema creation belongs to dao/db_init.
"""

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from backend.models.base import Base


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=True, index=True)
    title = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="active", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    findings = relationship("ResearchFinding", back_populates="session", cascade="all, delete-orphan")
    citations = relationship("ResearchCitation", back_populates="session", cascade="all, delete-orphan")
    memory_messages = relationship("ResearchMemory", back_populates="session", cascade="all, delete-orphan")


class ResearchFinding(Base):
    __tablename__ = "research_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(100), nullable=False, index=True)
    source_url = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    session = relationship("ResearchSession", back_populates="findings")


class ResearchCitation(Base):
    __tablename__ = "research_citations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    authors = Column(ARRAY(Text), nullable=False)
    source_url = Column(Text, nullable=False)
    publication_year = Column(Integer, nullable=True)
    doi = Column(String(255), nullable=True)
    citation_type = Column(String(50), default="article")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    session = relationship("ResearchSession", back_populates="citations")


class ResearchMemory(Base):
    __tablename__ = "research_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    message_role = Column(String(50), nullable=False)
    message_name = Column(String(255), nullable=True)
    message_content = Column(Text, nullable=False)
    timestamp = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    session = relationship("ResearchSession", back_populates="memory_messages")
