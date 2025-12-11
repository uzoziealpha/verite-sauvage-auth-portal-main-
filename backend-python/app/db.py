# backend-python/app/db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# In production, set DATABASE_URL to your Postgres URL.
# For local dev, SQLite is fine.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vs_auth.db")

# For SQLite we need special connect args; for Postgres we don't.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a SQLAlchemy Session."""
    from sqlalchemy.orm import Session

    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()