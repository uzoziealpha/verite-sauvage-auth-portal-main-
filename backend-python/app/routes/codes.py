# backend-python/app/routes/codes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
