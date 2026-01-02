"""Relational database models for persistence.

This module defines proper relational models instead of storing
messages as JSON. This provides:
- Better scalability (no JSON size limits)
- Better query performance
- Easier analytics
- Proper normalization
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class ConversationModel(Base):
    """
    SQLAlchemy model for conversations.
    
    This is the aggregate root. Messages are stored in a separate table
    with a foreign key relationship (1:N).
    """
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to messages (1:N)
    messages = relationship(
        "MessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="MessageModel.created_at"
    )
    
    # Composite index for efficient queries: "latest conversations for a user"
    # This index optimizes queries like: SELECT * FROM conversations 
    # WHERE user_id = ? ORDER BY updated_at DESC LIMIT 10
    __table_args__ = (
        Index('idx_conversations_user_updated', 'user_id', 'updated_at'),
    )


class MessageModel(Base):
    """
    SQLAlchemy model for individual messages.
    
    Each message is stored as a separate row, allowing for:
    - Efficient queries (e.g., "count messages per user")
    - Pagination
    - Indexing on specific fields
    - Analytics without loading full conversations
    """
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False, index=True)  # 'user' or 'assistant'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Sequence number within conversation (for ordering)
    sequence = Column(Integer, nullable=False, index=True)
    
    # Relationship back to conversation
    conversation = relationship("ConversationModel", back_populates="messages")
    
    # Composite index for efficient queries: "messages in a conversation ordered by sequence"
    # This index optimizes queries like: SELECT * FROM messages 
    # WHERE conversation_id = ? ORDER BY sequence ASC
    __table_args__ = (
        Index('idx_messages_conversation_sequence', 'conversation_id', 'sequence'),
    )

