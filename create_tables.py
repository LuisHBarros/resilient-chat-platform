"""Create initial database tables."""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.persistence.models_relational import Base
from app.infrastructure.config.settings import settings
from sqlalchemy import create_engine

# Get database URL and convert from async to sync
db_url = settings.database_url
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

print(f"Creating tables using URL: {db_url}")

# Create engine
engine = create_engine(db_url)

# Create all tables
Base.metadata.create_all(engine)

print("✅ All tables created successfully!")

