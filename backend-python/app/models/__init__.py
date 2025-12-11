# backend-python/app/models/__init__.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    func,
)

# Use the same Base/engine as the rest of the Postgres backend
from app.database import Base


class Product(Base):
    """
    Main product table for Vérité Sauvage / Calm Candles essential items.
    Backed by Postgres.
    """

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    collection = Column(String(255), nullable=True)
    serial = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(512), nullable=True)
    authentic = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class SecurityCode(Base):
    """
    Optional table if you ever migrate security codes from JSON to DB.

    Stores the mapping:
      product_id (0x + 64 hex) -> VS Security Code (6 chars, starts with VS)
    """

    __tablename__ = "security_codes"

    product_id = Column(String(66), primary_key=True, index=True)
    vs_code = Column(String(6), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
