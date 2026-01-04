"""PostgreSQL repository implementation using async SQLAlchemy.

This repository uses proper relational modeling with separate tables
for conversations and messages, providing better scalability and
query performance than JSON storage.
"""
from typing import Optional, List
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.domain.entities.conversation import Conversation
from app.domain.ports.repository_port import RepositoryPort
from app.domain.exceptions import RepositoryError
from app.domain.value_objects.message import Message
from app.infrastructure.persistence.models_relational import (
    ConversationModel,
    MessageModel,
    Base
)
from app.infrastructure.config.settings import settings


class PostgresRepository(RepositoryPort):
    """
    PostgreSQL repository implementation using async SQLAlchemy.
    
    This repository stores conversations and messages in separate tables,
    providing better scalability and query performance.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize PostgreSQL repository.
        
        Args:
            database_url: Database URL. If not provided, uses settings.database_url.
        """
        self.database_url = database_url or settings.database_url
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL is required for PostgresRepository. "
                "Set it as an environment variable or in .env file."
            )
        
        # Create async engine
        self.engine = create_async_engine(
            self.database_url,
            echo=False,  # Set to True for SQL debugging
            future=True
        )
        
        # Create async session factory
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def check_health(self) -> bool:
        """
        Check repository health by testing database connectivity.
        
        This method verifies that the repository can connect to PostgreSQL
        by executing a simple query. Used for health checks and readiness probes.
        
        Returns:
            True if database connection is healthy, False otherwise.
            
        Raises:
            RepositoryError: If health check fails unexpectedly.
        """
        try:
            async with self.async_session() as session:
                # Execute a simple query to test connectivity
                await session.execute(select(1))
                return True
        except Exception:
            return False
    
    async def save(self, conversation: Conversation) -> Conversation:
        """
        Save a conversation and its messages.
        
        Args:
            conversation: The conversation entity to save.
            
        Returns:
            The saved conversation with generated ID if applicable.
        """
        async with self.async_session() as session:
            try:
                if conversation.id:
                    # Update existing conversation
                    result = await session.execute(
                        select(ConversationModel).where(
                            ConversationModel.id == conversation.id
                        )
                    )
                    conv_model = result.scalar_one_or_none()
                    
                    if conv_model is None:
                        raise RepositoryError(f"Conversation {conversation.id} not found")
                    
                    # Update timestamps
                    conv_model.updated_at = datetime.utcnow()
                else:
                    # Create new conversation
                    conversation.id = str(uuid.uuid4())
                    conv_model = ConversationModel(
                        id=conversation.id,
                        user_id=conversation.user_id,
                        created_at=conversation.created_at or datetime.utcnow(),
                        updated_at=conversation.updated_at or datetime.utcnow()
                    )
                    session.add(conv_model)
                
                # Get existing messages to avoid duplicates
                result = await session.execute(
                    select(MessageModel).where(
                        MessageModel.conversation_id == conversation.id
                    ).order_by(MessageModel.sequence.desc())
                )
                existing_messages = result.scalars().all()
                existing_sequence = max([m.sequence for m in existing_messages], default=0)
                next_sequence = existing_sequence + 1
                
                # Get existing message contents to check for duplicates
                existing_contents = {(m.content, m.role, m.created_at) for m in existing_messages}
                
                # Save only new messages
                for msg in conversation.messages:
                    msg_key = (msg.content, msg.role, msg.timestamp or datetime.utcnow())
                    
                    # Skip if message already exists
                    if msg_key in existing_contents:
                        continue
                    
                    msg_model = MessageModel(
                        id=str(uuid.uuid4()),
                        conversation_id=conversation.id,
                        content=msg.content,
                        role=msg.role,
                        created_at=msg.timestamp or datetime.utcnow(),
                        sequence=next_sequence
                    )
                    session.add(msg_model)
                    next_sequence += 1
                
                await session.commit()
                
                # Update conversation timestamps
                conversation.updated_at = datetime.utcnow()
                if conversation.created_at is None:
                    conversation.created_at = conv_model.created_at
                
                return conversation
            except Exception as e:
                await session.rollback()
                raise RepositoryError(f"Failed to save conversation: {str(e)}") from e
    
    async def find_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Find a conversation by ID with all messages.
        
        Args:
            conversation_id: The unique identifier of the conversation.
            
        Returns:
            The conversation if found, None otherwise.
        """
        async with self.async_session() as session:
            try:
                result = await session.execute(
                    select(ConversationModel)
                    .options(selectinload(ConversationModel.messages))
                    .where(ConversationModel.id == conversation_id)
                )
                conv_model = result.scalar_one_or_none()
                
                if conv_model is None:
                    return None
                
                return self._model_to_entity(conv_model)
            except Exception as e:
                raise RepositoryError(f"Failed to find conversation: {str(e)}") from e
    
    async def find_by_user_id(self, user_id: str) -> List[Conversation]:
        """
        Find all conversations for a user.
        
        Args:
            user_id: The user identifier.
            
        Returns:
            List of conversations for the user.
        """
        async with self.async_session() as session:
            try:
                result = await session.execute(
                    select(ConversationModel)
                    .options(selectinload(ConversationModel.messages))
                    .where(ConversationModel.user_id == user_id)
                    .order_by(ConversationModel.updated_at.desc())
                )
                conv_models = result.scalars().all()
                
                return [self._model_to_entity(conv_model) for conv_model in conv_models]
            except Exception as e:
                raise RepositoryError(f"Failed to find conversations: {str(e)}") from e
    
    async def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation by ID (cascade deletes messages).
        
        Args:
            conversation_id: The unique identifier of the conversation.
            
        Returns:
            True if deleted, False if not found.
        """
        async with self.async_session() as session:
            try:
                result = await session.execute(
                    select(ConversationModel).where(
                        ConversationModel.id == conversation_id
                    )
                )
                conv_model = result.scalar_one_or_none()
                
                if conv_model is None:
                    return False
                
                await session.delete(conv_model)
                await session.commit()
                return True
            except Exception as e:
                await session.rollback()
                raise RepositoryError(f"Failed to delete conversation: {str(e)}") from e
    
    def _model_to_entity(self, conv_model: ConversationModel) -> Conversation:
        """Convert a ConversationModel to a Conversation entity."""
        # Convert messages from models to Message value objects
        messages = [
            Message(
                content=msg.content,
                role=msg.role,
                timestamp=msg.created_at
            )
            for msg in sorted(conv_model.messages, key=lambda m: m.sequence)
        ]
        
        conversation = Conversation(
            user_id=conv_model.user_id,
            id=conv_model.id,
            messages=messages,
            created_at=conv_model.created_at,
            updated_at=conv_model.updated_at
        )
        
        return conversation

