"""add_sequence_column_to_messages

Revision ID: 1522d88b7eda
Revises: 
Create Date: 2026-01-04 10:29:51.659701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1522d88b7eda'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sequence column to messages table
    # First, add the column as nullable
    op.add_column('messages', sa.Column('sequence', sa.Integer(), nullable=True))
    
    # Create an index on the sequence column
    op.create_index('ix_messages_sequence', 'messages', ['sequence'])
    
    # Populate sequence values for existing messages
    # Order by created_at to maintain chronological order
    op.execute("""
        WITH numbered_messages AS (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY conversation_id ORDER BY created_at) as seq
            FROM messages
        )
        UPDATE messages
        SET sequence = numbered_messages.seq
        FROM numbered_messages
        WHERE messages.id = numbered_messages.id
    """)
    
    # Now make the column non-nullable
    op.alter_column('messages', 'sequence', nullable=False)
    
    # Create composite index for efficient queries
    op.create_index('idx_messages_conversation_sequence', 'messages', ['conversation_id', 'sequence'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_messages_conversation_sequence', table_name='messages')
    op.drop_index('ix_messages_sequence', table_name='messages')
    
    # Remove sequence column
    op.drop_column('messages', 'sequence')

