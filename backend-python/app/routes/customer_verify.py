# backend-python/app/routes/customer_verify.py

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from pathlib import Path
import json
from datetime import datetime, timezone

from web3.exceptions import BadFunctionCallOutput

from app.data.seed_codes import check_short_code, get_short_code_for_product
from app.services.web3loader import get_web3, get_contract

router = APIRouter()

# ----------------- helpers for codes.json (for GET flow) --------------------

CODES_PATH = Path(__file__).resolve().parents[1] / "data" / "codes.json"


def _load_codes() -> Dict[str, Any]:
    if not CODES_PATH.exists():
        return {}
    with CODES_PATH.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _fetch_onchain_product(product_id: str) -> Dict[str, Any]:
    """
    Helper: load product fields from the Solidity contract.

    Solidity function:

        function getProduct(bytes32 id) public view returns (
            string memory name,
            string memory color,
            string memory material,
            uint256 price,
            uint256 year
        );

    If anything fails, we return an empty dict.
    """
    try:
        web3 = get_web3()
        contract = get_contract(web3)
        raw = contract.functions.getProduct(product_id).call()

        if not isinstance(raw, (list, tuple)) or len(raw) < 5:
            return {}

        name = raw[0] or ""
        color = raw[1] or ""
        material = raw[2] or ""
        price = int(raw[3]) if raw[3] is not None else 0
        year = int(raw[4]) if raw[4] is not None else 0

        # If fully empty, treat as "no record"
        if name == "" and price == 0:
            return {}

        return {
            "name": name,
            "color": color,
            "material": material,
            "price": price,
            "year": year,
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
        ..., description="VS security code (e.g.VSP9GL or 6-char code)"
    )


@router.post("/customer-verify")
def customer_verify_post(body: CustomerVerifyRequest):
    """
    Customer-facing verification used when both productId + short_code
    are provided (your current UI when both fields are filled).

    - Uses codes.json for authenticity.
    - If authentic, enriches the product with on-chain bag details.
    """

    pid = body.product_id.strip()
    code = body.short_code.strip()

    if not pid or not code:
        raise HTTPException(
            status_code=400,
            detail="product_id and short_code are required",
        )

    # 1) Check against stored VS code
    is_match = check_short_code(pid, code)
    stored = get_short_code_for_product(pid)

    if stored is None:
        verdict = {
            "status": "fake",
            "reason": "no_vs_code_stored_for_product_id",
        }
        return {
            "success": False,
            "product": {"productId": pid},
            "verdict": verdict,
        }

    if not is_match:
        verdict = {
            "status": "fake",
            "reason": "vs_code_mismatch_for_product_id",
        }
        return {
            "success": False,
            "product": {"productId": pid},
            "verdict": verdict,
        }

    # 2) Authentic → base product payload
    product: Dict[str, Any] = {
        "productId": pid,
        "vsCode": stored,
    }

    # 3) Enrich from on-chain getProduct
    onchain = _fetch_onchain_product(pid)
    if onchain:
        product.update(onchain)

    verdict = {
        "status": "authentic",
        "reason": "vs_code_matches_for_product_id",
    }

    return {
        "success": True,
        "product": product,
        "verdict": verdict,
    }


# ------------------------ GET /customer-verify?code= ------------------------


@router.get("/customer-verify")
def customer_verify_get(
    code: Optional[str] = Query(
        None, description="VS code (e.g. VSP9GL, scanned from QR)"
    ),
    productId: Optional[str] = Query(
        None, description="Internal productId (0x + 64 hex chars)"
    ),
):
    """
    QR / deep-link flow:

    - /customer-verify?code=VSP9GL
    - or /customer-verify?productId=0x...

    Looks up codes.json and enriches with on-chain product details.
    """

    if not code and not productId:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'code' or 'productId'.",
        )

    codes = _load_codes()

    record_pid: Optional[str] = None
    stored_code: Optional[str] = None

    # Lookup by short code
    if code:
        c = code.strip()
        for pid, val in codes.items():
            stored = str(val).strip()
            if stored.lower() == c.lower():
                record_pid = pid
                stored_code = stored
                break
    else:
        pid = productId.strip()
        if pid in codes:
            record_pid = pid
            stored_code = str(codes[pid]).strip()

    if not record_pid or not stored_code:
        return {
            "success": False,
            "verdict": {
                "status": "fake",
                "reason": "code_or_product_not_found_in_codes_store",
            },
        }

    # Base product payload
    product: Dict[str, Any] = {
        "productId": record_pid,
        "vsCode": stored_code,
    }

    # Enrich from on-chain getProduct
    onchain = _fetch_onchain_product(record_pid)
    if onchain:
        product.update(onchain)

    return {
        "success": True,
        "verdict": {
            "status": "authentic",
            "reason": "code_found_in_codes_store",
        },
        "product": product,
    }
