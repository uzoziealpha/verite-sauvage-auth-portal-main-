# backend-python/app/routes/codes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.data.seed_codes import register_code_for_product

router = APIRouter()


class CodeRegisterRequest(BaseModel):
  """
  Called from the admin UI right after uploading a product on-chain.

  We use this to:
  - ensure a VS short code exists
  - store clean product metadata in codes.json, like:

    "0x....": {
      "meta": {
        "color": "White",
        "material": "Crocodile",
        "model": "Vérité Sauvage Petit",
        "price": 18090,
        "year": 2025
      },
      "shortCode": "VSR4A9"
    }
  """
  product_id: str = Field(..., description="Product ID (0x + 64 hex)")
  model: Optional[str] = Field(None, description="Model name, e.g. 'Vérité Sauvage Petit'")
  color: Optional[str] = Field(None, description="Color")
  material: Optional[str] = Field(None, description="Material")
  price: Optional[int] = Field(None, description="Price as integer (e.g. 18090)")
  year: Optional[int] = Field(None, description="Production year")


@router.post("/register")
def register_code(body: CodeRegisterRequest) -> Dict[str, Any]:
  """
  Admin endpoint: ensure a VS security code exists and persist clean meta.

  We only store these fields in meta:
  - color
  - material
  - model
  - price
  - year
  """
  pid = body.product_id.strip()

  # Build the meta exactly like you want it in codes.json
  raw_meta = {
    "model": body.model,
    "color": body.color,
    "material": body.material,
    "price": body.price,
    "year": body.year,
  }

  # Remove None values so we do not get nulls in JSON
  meta = {k: v for k, v in raw_meta.items() if v is not None}

  try:
    short_code = register_code_for_product(pid, meta=meta)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))

  return {
    "success": True,
    "productId": pid,
    "shortCode": short_code,
    "meta": meta,
  }
