# backend-python/app/routes/customer_verify.py

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from web3.exceptions import BadFunctionCallOutput

from app.data.seed_codes import (
    check_short_code,
    get_short_code_for_product,
    get_meta_for_product,
    append_verification_event,
)
from app.services.web3loader import get_web3, get_contract

router = APIRouter()


def _fetch_onchain_product(pid: str) -> Dict[str, Any]:
    """Helper: fetch product from the smart contract, returning {} on failure."""
    try:
        web3 = get_web3()
        contract = get_contract(web3)
        (
            name,
            color,
            material,
            price,
            year,
        ) = contract.functions.getProduct(pid).call()
        if not name:
            return {}
        return {
            "productId": pid,
            "name": name,
            "color": color,
            "material": material,
            "price": int(price),
            "year": int(year),
        }
    except BadFunctionCallOutput:
        # Wrong contract / ABI / network
        return {}
    except Exception:
        return {}


# --------------------------- POST (productId + code) ------------------------


class CustomerVerifyRequest(BaseModel):
    product_id: str = Field(..., description="Product ID (0x + 64 hex chars)")
    short_code: str = Field(
        ...,
        description="VS security code (e.g. VSP9GL or 6-char code)",
    )


@router.post("/customer-verify")
def customer_verify_post(body: CustomerVerifyRequest) -> Dict[str, Any]:
    """
    Customer-facing verification used when both productId + short_code
    are provided (your current UI when both fields are filled).

    - Uses codes.json for authenticity.
    - If valid, enrich with stored meta + on-chain data.
    """
    pid = body.product_id.strip()
    code = body.short_code.strip()

    # 1) Check code
    is_match = check_short_code(pid, code)
    if not is_match:
        verdict = {
            "status": "fake",
            "reason": "vs_code_mismatch_for_product_id",
        }
        append_verification_event(pid, source="customer", verdict="fake", details=verdict)
        return {
            "success": False,
            "product": {"productId": pid},
            "verdict": verdict,
        }

    # 2) Authentic → base product payload from codes.json
    product: Dict[str, Any] = {
        "productId": pid,
        "vsCode": code,
    }
    meta = get_meta_for_product(pid)
    if meta:
        product["meta"] = meta

    # 3) Enrich from on-chain getProduct
    onchain = _fetch_onchain_product(pid)
    if onchain:
        product.update(onchain)

    verdict = {
        "status": "authentic",
        "reason": "vs_code_matches_for_product_id",
    }

    append_verification_event(pid, source="customer", verdict="authentic", details=verdict)

    return {
        "success": True,
        "product": product,
        "verdict": verdict,
    }


# ------------------------- GET variant (code or productId) ------------------

@router.get("/customer-verify")
def customer_verify_get(
    code: Optional[str] = Query(
        None,
        description="VS security code (if only code is scanned from QR)",
    ),
    productId: Optional[str] = Query(
        None,
        description="Product ID associated with that code, optional",
    ),
) -> Dict[str, Any]:
    """
    Alternate GET-based verification:

    - /customer-verify?code=VSxxxx
    - or /customer-verify?code=VSxxxx&productId=0x...

    It will try to locate the productId from codes.json if not given.
    """
    if not code and not productId:
        raise HTTPException(
            status_code=400,
            detail="Provide at least 'code' or both 'code' and 'productId'.",
        )

    codes_meta = {}
    # If productId not given, try to find a matching pid for this code
    record_pid: Optional[str] = None
    stored_code: Optional[str] = None

    if productId:
        pid = productId.strip()
        stored_code = get_short_code_for_product(pid)
        if stored_code:
            record_pid = pid
    else:
        # No productId -> we must scan all codes.json entries (for convenience)
        from app.data.seed_codes import _load_codes  # type: ignore

        codes = _load_codes()
        for pid, value in codes.items():
            sc = None
            if isinstance(value, dict):
                sc = value.get("shortCode")
            elif isinstance(value, str):
                sc = value
            if sc and sc.lower() == code.strip().lower():
                record_pid = pid
                stored_code = sc
                break

    if not record_pid or not stored_code:
        verdict = {
            "status": "fake",
            "reason": "code_or_product_not_found_in_codes_store",
        }
        append_verification_event(
            productId or "unknown",
            source="customer",
            verdict="fake",
            details=verdict,
        )
        return {
            "success": False,
            "verdict": verdict,
        }

    product: Dict[str, Any] = {
        "productId": record_pid,
        "vsCode": stored_code,
    }
    meta = get_meta_for_product(record_pid)
    if meta:
        product["meta"] = meta

    onchain = _fetch_onchain_product(record_pid)
    if onchain:
        product.update(onchain)

    verdict = {
        "status": "authentic",
        "reason": "code_found_in_codes_store",
    }

    append_verification_event(record_pid, source="customer", verdict="authentic", details=verdict)

    return {
        "success": True,
        "verdict": verdict,
        "product": product,
    }
