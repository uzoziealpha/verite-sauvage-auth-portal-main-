# backend-python/app/models.py
from sqlalchemy import Column, String, DateTime, func
from .db import Base

class SecurityCode(Base):
    __tablename__ = "security_codes"

    product_id = Column(String(66), primary_key=True, index=True)  # 0x + 64
    vs_code = Column(String(6), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
