# backend-python/app/routes/debug.py

from fastapi import APIRouter
from app.services.web3loader import get_web3, get_contract_debug_info

router = APIRouter()

@router.get("/artifact")
def artifact():
    """
    Return the compiled contract artifact (ABI + networks).
    """
    from app.services.web3loader import CONTRACT_ARTIFACT
    return CONTRACT_ARTIFACT

@router.get("/contract")
def debug_contract():
    """
    Try to inspect the contract on the configured RPC.
    In production (Railway) this may not be deployed, so we
    just return a friendly JSON instead of raising 500.
    """
    try:
        web3 = get_web3()
        info = get_contract_debug_info(web3)
        return info
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "hint": "This is expected if no contract is deployed at CONTRACT_ADDRESS on the configured RPC."
        }
