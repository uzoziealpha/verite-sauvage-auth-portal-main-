from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from app.data.seed_codes_db import (
    check_short_code,
    get_short_code_for_product,
    get_meta_for_product,
    append_verification_event,
)

router = APIRouter()


class CustomerVerifyBody(BaseModel):
    product_id: str
    short_code: str


@router.post("/customer-verify")
def customer_verify(payload: CustomerVerifyBody) -> Dict[str, Any]:
    """
    Public customer verification endpoint.

    Request body:
    {
      "product_id": "0x...",
      "short_code": "VSXXXX"
    }

    Response shape (matches what your frontend already expects):
    {
      "success": true,
      "product": {
        "productId": "...",
        "vsCode": "VSXXXX",
        "meta": { ... }
      },
      "verdict": {
        "status": "authentic" | "fake",
        "reason": "vs_code_matches_for_product_id" | "vs_code_mismatch_for_product_id" | ...
      },
      "vsSecurityCode": "VSXXXX"
    }
    """
    pid = payload.product_id.strip()
    code = payload.short_code.strip()

    if not pid or not code:
        raise HTTPException(status_code=400, detail="Missing product_id or short_code")

    # Get what we know for this product from DB
    stored_code: Optional[str] = get_short_code_for_product(pid)
    meta = get_meta_for_product(pid)

    # Decide verdict
    if not stored_code:
        status = "fake"
        reason = "no_vs_code_for_product_id"
        is_authentic = False
    else:
        is_match = check_short_code(pid, code)
        if is_match:
            status = "authentic"
            reason = "vs_code_matches_for_product_id"
            is_authentic = True
        else:
            status = "fake"
            reason = "vs_code_mismatch_for_product_id"
            is_authentic = False

    # Log verification event
    append_verification_event(
        pid,
        source="customer",
        verdict=status,
        details={
            "reason": reason,
            "incomingShortCode": code,
            "storedShortCode": stored_code,
        },
    )

    # Build product block for frontend
    product_block: Dict[str, Any] = {
        "productId": pid,
        "vsCode": stored_code or "",
        "meta": meta or {},
    }

    return {
        "success": True,
        "product": product_block,
        "verdict": {
            "status": status,
            "reason": reason,
        },
        "vsSecurityCode": stored_code or "",
    }
