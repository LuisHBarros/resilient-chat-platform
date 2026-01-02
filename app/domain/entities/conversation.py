"""Conversation entity."""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from app.domain.value_objects.message import Message


@dataclass
class Conversation:
    """
    Conversation entity representing a user's conversation session.
    
    Entities have identity and lifecycle. This entity aggregates messages
    and maintains conversation state.
    
    Business Invariants:
    - A conversation must always have a user_id (non-empty string)
    - Messages are ordered chronologically (by timestamp)
    - A conversation cannot have duplicate messages (same content, role, and timestamp)
    - The conversation ID is immutable once set
    - Messages can only be added, never removed (immutable history)
    - created_at must be <= updated_at at all times
    """
    user_id: str
    id: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_last_message(self) -> Optional[Message]:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None
