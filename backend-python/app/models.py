from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func
from .database import Base


class Product(Base):
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
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
