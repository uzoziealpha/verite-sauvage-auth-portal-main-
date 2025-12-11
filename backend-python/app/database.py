# backend-python/app/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# 1) Read DATABASE_URL from environment
#    - On Railway: they'll set DATABASE_URL to a Postgres URL
#    - Locally: if not set, we fall back to a local SQLite file
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Local default for development
    DATABASE_URL = "sqlite:///./veritesauvage.db"

# 2) SQLite needs special connect args; Postgres/MySQL do not
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# 3) Create engine, session, and Base
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
