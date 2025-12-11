from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    code: str
    name: str
    collection: Optional[str] = None
    serial: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    authentic: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    collection: Optional[str] = None
    serial: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    authentic: Optional[bool] = None


class ProductOut(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VerifyRequest(BaseModel):
    code: str


class VerifyResponse(BaseModel):
    authentic: bool
    product: Optional[ProductOut] = None
    message: str
