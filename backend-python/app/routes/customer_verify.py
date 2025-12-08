# backend-python/app/routes/customer_verify.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from web3.exceptions import BadFunctionCallOutput

from app.services.web3loader import get_web3, get_contract
from app.data.seed_codes import check_short_code

router = APIRouter()


class CustomerVerifyRequest(BaseModel):
    product_id: str = Field(..., description="Product ID (0x + 64 hex chars)")
    short_code: str = Field(..., description="6-character VS Security Code (e.g. VS2BOF)")


@router.post("/customer-verify")
def customer_verify(body: CustomerVerifyRequest):
    """
    Public customer verification endpoint.

    Requirements for AUTHENTIC:
      1) Product exists on-chain (non-empty record from contract)
      2) VS Security Code in codes.json matches 'short_code' for this product

    Otherwise: FAKE / cannot verify.
    """
    pid = body.product_id.strip()
    short_code = body.short_code.strip()

    # ---- basic validation of productId -------------------------------------
    if not pid.startswith("0x") or len(pid) != 66:
        raise HTTPException(
            status_code=400,
            detail="Invalid product_id. Must be 0x + 64 hex characters.",
        )

    if len(short_code) < 6:
        raise HTTPException(
            status_code=400,
            detail="short_code must be at least 6 characters.",
        )

    # ---- call contract -----------------------------------------------------
    web3 = get_web3()
    contract = get_contract(web3)

    try:
        prod = contract.functions.getProduct(pid).call()
    except BadFunctionCallOutput as e:
        raise HTTPException(
            status_code=500,
            detail="Contract call failed. Check RPC_URL and CONTRACT_ADDRESS.",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error from contract: {e}",
        ) from e

    name = prod[0] if len(prod) > 0 else ""
    color = prod[1] if len(prod) > 1 else ""
    material = prod[2] if len(prod) > 2 else ""
    price = int(prod[3]) if len(prod) > 3 and prod[3] is not None else 0
    year = int(prod[4]) if len(prod) > 4 and prod[4] is not None else 0

    product = {
        "productId": pid,
        "name": name,
        "color": color,
        "material": material,
        "price": price,
        "year": year,
    }

    # ---- if no on-chain record -> fake ------------------------------------
    if name == "" and price == 0:
        verdict = {
            "status": "fake",
            "reason": "no_onchain_record — product not found on blockchain",
        }
        return {
            "success": False,
            "product": product,
            "verdict": verdict,
        }

    # ---- on-chain OK, now check VS Security Code --------------------------
    code_ok = check_short_code(pid, short_code)
    if not code_ok:
        verdict = {
            "status": "fake",
            "reason": "security_code_mismatch — VS code does not match this product",
        }
        return {
            "success": False,
            "product": product,
            "verdict": verdict,
        }

    # ---- both checks passed: AUTHENTIC ------------------------------------
    verdict = {
        "status": "authentic",
        "reason": "onchain_and_vs_code_match",
    }

    return {
        "success": True,
        "product": product,
        "verdict": verdict,
    }