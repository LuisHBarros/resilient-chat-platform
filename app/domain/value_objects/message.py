"""Message value object."""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class Message:
    """
    Value object representing a message in the conversation.
    
    Value objects are immutable and represent concepts from the domain.
    
    Business Invariants:
    - Message content cannot be empty or only whitespace
    - Role must be either 'user' or 'assistant' (no other values allowed)
    - Timestamp is automatically set if not provided (current time)
    - Once created, a message cannot be modified (immutability)
    - Content must be a non-empty string with at least one non-whitespace character
    """
    content: str
    role: str = "user"  # 'user' or 'assistant'
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate message content."""
        if not self.content or not self.content.strip():
            raise ValueError("Message content cannot be empty")
        if self.role not in ["user", "assistant"]:
            raise ValueError("Message role must be 'user' or 'assistant'")
        
        # Set timestamp if not provided (using object.__setattr__ for frozen dataclass)
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', datetime.now())

