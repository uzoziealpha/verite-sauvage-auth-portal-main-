# backend-python/app/routes/verify.py

from fastapi import APIRouter, HTTPException
from web3.exceptions import BadFunctionCallOutput

from app.services.web3loader import get_web3, get_contract
from app.data.seed_codes import register_code_for_product

router = APIRouter()


@router.get("/{product_id}")
def verify_product(product_id: str):
  """
  Admin / internal verification endpoint.

  - Checks the product on-chain via the smart contract
  - If found and valid -> status = 'authentic'
  - If not found -> status = 'fake'
  - When authentic, also ensures a VS Security Code is stored in codes.json
    so the customer /customer-verify flow can use it.
  """

  pid = product_id.strip()

  # --- Basic shape check for the productId ---------------------------------
  if not pid.startswith("0x") or len(pid) != 66:
    raise HTTPException(
      status_code=400,
      detail="Invalid product_id. Must be 0x + 64 hex characters.",
    )

  # --- Web3 + contract ------------------------------------------------------
  web3 = get_web3()
  contract = get_contract(web3)

  try:
    # Assumes your Solidity function is something like:
    # function getProduct(bytes32 productId) public view returns (
    #   string memory name,
    #   string memory color,
    #   string memory material,
    #   uint256 price,
    #   uint256 year
    # );
    prod = contract.functions.getProduct(pid).call()
  except BadFunctionCallOutput as e:
    # Typically: wrong contract address, ABI mismatch, or RPC issue
    raise HTTPException(
      status_code=500,
      detail="Contract call failed. Check RPC_URL and CONTRACT_ADDRESS.",
    ) from e
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Unexpected error from contract: {e}",
    ) from e

  # ---- Map tuple -> product dict ------------------------------------------
  # Be defensive about length
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

  # --- Decide verdict -------------------------------------------------------
  # "empty" product = not registered on-chain
  if name == "" and price == 0:
    verdict = {
      "status": "fake",
      "reason": "no_onchain_record — product not found on blockchain",
    }
    return {
      "success": False,
      "product": product,
      "verdict": verdict,
      # No VS code generated for fake / missing records
    }

  # --- Authentic on-chain: ensure VS code is stored -------------------------
  # This will:
  #   - generate a new 'VS****' code if none exists yet
  #   - or return the existing one from codes.json
  try:
    vs_code = register_code_for_product(pid)
  except Exception as e:
    # Do NOT fail the whole verification just because code storage failed;
    # still tell admin it's authentic, but mention storage issue in reason.
    verdict = {
      "status": "authentic",
      "reason": f"onchain_record_ok (warning: VS code storage error: {e})",
    }
    return {
      "success": True,
      "product": product,
      "verdict": verdict,
    }

  verdict = {
    "status": "authentic",
    "reason": "onchain_record_ok",
  }

  # We also return the VS code here so the admin UI can display it if needed.
  return {
    "success": True,
    "product": product,
    "verdict": verdict,
    "vsSecurityCode": vs_code,  # extra field, frontend can ignore or display
  }