# backend-python/app/routes/codes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import secrets  # 👈 NEW

from app.data.seed_codes import (
    register_code_for_product,
    get_short_code_for_product,
)

router = APIRouter()


class CodeRegisterRequest(BaseModel):
    product_id: str = Field(..., description="Product ID (0x + 64 hex)")


@router.post("/register")
def register_code(body: CodeRegisterRequest):
    """
    Admin endpoint: ensure a 6-character VS security code exists for this product.

    - If code already exists: return it.
    - If not: generate new, persist, and return it.
    """
    pid = body.product_id.strip()
    try:
        short_code = register_code_for_product(pid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "success": True,
        "productId": pid,
        "shortCode": short_code,
    }


@router.get("/{product_id}")
def get_code(product_id: str):
    """Admin helper: fetch the stored VS security code for a product ID."""
    code = get_short_code_for_product(product_id)
    if not code:
        raise HTTPException(status_code=404, detail="No code stored for this productId")
    return {
        "success": True,
        "productId": product_id,
        "shortCode": code,
    }


# ================== NEW: auto-generate productId + code =====================


class CodeAutoRegisterRequest(BaseModel):
    """
    New simple admin request:
    You can pass bag metadata if you want for later use.
    For now it's just echoed back; the important part is productId + code.
    """
    serial: Optional[str] = Field(None, description="Bag serial / internal SKU")
    model: Optional[str] = Field(None, description="Bag model / name")
    color: Optional[str] = None
    size: Optional[str] = None
    year: Optional[int] = None
    material: Optional[str] = None


@router.post("/register-auto")
def register_code_auto(body: CodeAutoRegisterRequest):
    """
    New admin endpoint:

    - Generates a new random productId (0x + 64 hex)
    - Uses seed_codes.register_code_for_product to create a VS code
      and store it in codes.json
    - Returns productId + shortCode and a suggested QR path
    """

    # 32 random bytes -> 64 hex chars, plus 0x prefix
    product_id = "0x" + secrets.token_hex(32)

    try:
        short_code = register_code_for_product(product_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register code: {e}")

    # Frontend / label can turn this into a full URL using the backend or frontend domain
    qr_path = f"/customer-verify?code={short_code}"

    return {
        "success": True,
        "productId": product_id,
        "shortCode": short_code,
        "qrPath": qr_path,
        "meta": {
            "serial": body.serial,
            "model": body.model,
            "color": body.color,
            "size": body.size,
            "year": body.year,
            "material": body.material,
        },
    }