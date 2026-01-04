"""
Diagnostic script to check conversation history setup
"""
import asyncio
import sys
sys.path.insert(0, 'C:\\Users\\luish\\Documents\\ia-proj\\backend-ia-proj')

from app.infrastructure.persistence.postgres_repository import PostgresRepository
from app.infrastructure.config.settings import settings

async def check_database():
    print("=== Conversation History Diagnostic ===\n")
    
    # Check database URL
    print(f"Database URL: {settings.database_url}")
    print()
    
    # Initialize repository
    try:
        repo = PostgresRepository()
        print("✅ Repository initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize repository: {e}")
        return
    
    # Check database connectivity
    try:
        health = await repo.check_health()
        if health:
            print("✅ Database connection healthy")
        else:
            print("❌ Database connection failed")
            return
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return
    
    # Query conversations
    try:
        # Get a sample user_id from database
        from sqlalchemy import select, text
        async with repo.async_session() as session:
            # Check if conversations table exists
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('conversations', 'messages')
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"\n📊 Tables found: {tables}")
            
            if 'conversations' not in tables:
                print("❌ 'conversations' table doesn't exist!")
                print("   Run database migrations: alembic upgrade head")
                return
            
            if 'messages' not in tables:
                print("❌ 'messages' table doesn't exist!")
                print("   Run database migrations: alembic upgrade head")
                return
            
            # Count conversations
            result = await session.execute(text("SELECT COUNT(*) FROM conversations"))
            conv_count = result.scalar()
            print(f"\n💬 Total conversations in database: {conv_count}")
            
            # Count messages
            result = await session.execute(text("SELECT COUNT(*) FROM messages"))
            msg_count = result.scalar()
            print(f"📝 Total messages in database: {msg_count}")
            
            # Show sample conversations
            if conv_count > 0:
                result = await session.execute(text("""
                    SELECT c.id, c.user_id, c.created_at, COUNT(m.id) as msg_count
                    FROM conversations c
                    LEFT JOIN messages m ON m.conversation_id = c.id
                    GROUP BY c.id, c.user_id, c.created_at
                    ORDER BY c.updated_at DESC
                    LIMIT 5
                """))
                conversations = result.fetchall()
                print(f"\n📋 Sample conversations:")
                for conv in conversations:
                    print(f"   - ID: {conv[0][:20]}... | User: {conv[1]} | Messages: {conv[3]}")
            else:
                print("\n⚠️  No conversations found in database!")
                print("   Send a message in the chat to create your first conversation.")
    
    except Exception as e:
        print(f"\n❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_database())

