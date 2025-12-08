# backend-python/app/models/__init__.py

from sqlalchemy import Column, String, DateTime, func
from app.db import Base


class SecurityCode(Base):
    """
    Stores the mapping:
      product_id (0x + 64 hex) -> VS Security Code (6 chars, starts with VS)
    """

    __tablename__ = "security_codes"

    product_id = Column(String(66), primary_key=True, index=True)
    vs_code = Column(String(6), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
