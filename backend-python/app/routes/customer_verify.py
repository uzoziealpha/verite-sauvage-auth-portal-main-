# backend-python/app/routes/customer_verify.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.data.seed_codes import (
    check_short_code,
    get_short_code_for_product,
    get_meta_for_product,
)

router = APIRouter()


class CustomerVerifyRequest(BaseModel):
    product_id: str = Field(..., description="Product ID (0x + 64 hex chars)")
    short_code: str = Field(
        ..., description="6-character VS Security Code (e.g. VS2BOF)"
    )


def _derive_size_from_name(name: str) -> str:
    """
    Very simple size heuristic based on the product name.

    Examples:
      - "Vérité Sauvage Petit (Black) ..." -> "Petit"
      - "Vérité Sauvage Mini ..."         -> "Mini"
      - "Vérité Sauvage Grand ..."        -> "Grand"
    """
    n = (name or "").lower()
    if "petit" in n:
        return "Petit"
    if "mini" in n:
        return "Mini"
    if "grand" in n or "large" in n:
        return "Grand"
    return ""


def _derive_serial_from_pid(pid: str) -> str:
    """
    Derive a deterministic serial code from the productId bytes32.

    e.g. 0x....ABC123 -> VS-ABC123
    """
    if pid.startswith("0x"):
        hex_part = pid[2:]
    else:
        hex_part = pid

    tail = hex_part[-6:].upper()
    return f"VS-{tail}"


@router.post("/customer-verify")
def customer_verify(body: CustomerVerifyRequest):
    """
    Public customer verification endpoint.

    Requirements for AUTHENTIC:

      1) VS Security Code in codes.json matches 'short_code' for this product
      2) codes.json has a record for this productId (created by admin /verify step)

    We treat codes.json as the source of truth for customer checks. On-chain
    verification still happens in the admin flow when you click "Verify Vérité
    Sauvage Product", which writes both the VS code and metadata into codes.json.

    If checks pass, we return a rich product object:

        {
          "productId": "...",
          "vsCode": "VS2Q25",
          "model": "...",
          "color": "Black",
          "material": "Crocodile",
          "price": 1809000,
          "year": 2025,
          "size": "Petit",
          "serial": "VS-ABC123"
        }
    """
    pid = body.product_id.strip()
    short_code = body.short_code.strip()

    # ---- basic validation of productId -------------------------------------
    if not pid:
        raise HTTPException(status_code=400, detail="product_id cannot be empty.")

    if not pid.startswith("0x") or len(pid) != 66:
        raise HTTPException(
            status_code=400,
            detail="Invalid product_id. Must be 0x + 64 hex characters.",
        )

    if len(short_code) < 4:
        raise HTTPException(
            status_code=400,
            detail="short_code must be at least 4 characters.",
        )

    # ---- on-disk VS code check (source of truth for customers) -------------
    code_ok = check_short_code(pid, short_code)
    if not code_ok:
        product = {
            "productId": pid,
            "vsCode": short_code,
        }
        verdict = {
            "status": "fake",
            "reason": "vs_code_mismatch_for_product_id",
        }
        return {
            "success": False,
            "product": product,
            "verdict": verdict,
        }

    # If we reach here, the code matches what we stored earlier during admin verify.
    stored_vs_code = get_short_code_for_product(pid) or short_code
    meta = get_meta_for_product(pid)

    # Build rich product payload from stored metadata (+ derived fields).
    model = meta.get("model") or meta.get("name") or ""
    color = meta.get("color") or ""
    material = meta.get("material") or ""
    price = int(meta["price"]) if "price" in meta and meta["price"] is not None else 0
    year = int(meta["year"]) if "year" in meta and meta["year"] is not None else 0

    size = meta.get("size") or _derive_size_from_name(model)
    serial = meta.get("serial") or _derive_serial_from_pid(pid)

    product = {
        "productId": pid,
        "vsCode": stored_vs_code,
    }

    # Only include fields that we actually know
    if model:
        product["model"] = model
    if color:
        product["color"] = color
    if material:
        product["material"] = material
    if price:
        product["price"] = price
    if year:
        product["year"] = year
    if size:
        product["size"] = size
    if serial:
        product["serial"] = serial

    verdict = {
        "status": "authentic",
        "reason": "vs_code_matches_for_product_id",
    }

    return {
        "success": True,
        "product": product,
        "verdict": verdict,
    }
