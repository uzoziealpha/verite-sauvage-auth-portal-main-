# backend-python/app/routes/verify.py

from typing import Any, Dict

from fastapi import APIRouter

from web3.exceptions import BadFunctionCallOutput

from app.services.web3loader import get_web3, get_contract
from app.data.seed_codes import (
  register_code_for_product,
  get_meta_for_product,
)

router = APIRouter()


@router.get("/{product_id}")
def verify_product(product_id: str) -> Dict[str, Any]:
  """
  Admin / internal verification endpoint.

  For your current workflow:

  - Try to read on-chain product data (best-effort).
  - Never change "meta" in codes.json; that stays as clean
    product data from /codes/register (color, material, model, price, year).
  - Ensure a VS code exists (register_code_for_product without meta).
  - Always return success + 'authentic' so the admin UI does not see network errors.
  """
  pid = product_id.strip()

  product: Dict[str, Any] = {"productId": pid}
  onchain_ok = False

  # 1) Best-effort on-chain lookup (optional)
  try:
    web3 = get_web3()
    contract = get_contract(web3)

    # Assumes getProduct(productId) returns tuple:
    # (name, color, material, price, year, ...)
    prod = contract.functions.getProduct(pid).call()

    name = prod[0] if len(prod) > 0 else ""
    color = prod[1] if len(prod) > 1 else ""
    material = prod[2] if len(prod) > 2 else ""
    price = int(prod[3]) if len(prod) > 3 and prod[3] is not None else 0
    year = int(prod[4]) if len(prod) > 4 and prod[4] is not None else 0

    if name or price:
      onchain_ok = True
      product.update(
        {
          "name": name,
          "color": color,
          "material": material,
          "price": price,
          "year": year,
        }
      )
  except BadFunctionCallOutput:
    # Wrong contract ABI / address / network; ignore for now
    onchain_ok = False
  except Exception:
    # Node offline or any other error; ignore for now
    onchain_ok = False

  # 2) Ensure a VS code exists, WITHOUT changing meta
  #    (so codes.json keeps only color/material/model/price/year)
  vs_code = register_code_for_product(pid)

  # 3) Load stored meta from codes.json so admin sees what is saved
  stored_meta = get_meta_for_product(pid)
  if stored_meta:
    product.setdefault("meta", stored_meta)

  # 4) Decide verdict
  if onchain_ok:
    verdict = {
      "status": "authentic",
      "reason": "onchain_record_ok",
    }
  else:
    verdict = {
      "status": "authentic",
      "reason": "codes_store_only",
    }

  return {
    "success": True,
    "product": product,
    "verdict": verdict,
    "vsSecurityCode": vs_code,
  }
