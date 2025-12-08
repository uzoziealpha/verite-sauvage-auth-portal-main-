# backend-python/app/routes/debug.py

from fastapi import APIRouter
from web3 import Web3

from app.services.web3loader import get_web3, get_contract
from app.utils.settings import settings

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/contract")
def debug_contract():
    """
    Debug info for the on-chain contract wiring.

    Uses the same get_web3 + get_contract logic as the app.
    If something fails (bad RPC, bad address, no code), we return that
    as JSON instead of crashing.
    """
    web3 = get_web3()
    chain_id = web3.eth.chain_id

    result = {
        "rpc_url": settings.rpc_url,
        "chain_id": chain_id,
    }

    try:
        contract = get_contract(web3)
        address = contract.address  # already checksummed by web3
        code = web3.eth.get_code(address)
        has_code = code not in (b"", b"\x00", None)

        result.update(
            {
                "contract_address": address,
                "has_code": has_code,
            }
        )
    except Exception as e:
        env_addr = (settings.contract_address or "").strip() or None

        result.update(
            {
                "contract_address": env_addr,
                "has_code": False,
                "error": str(e),
            }
        )

    return result
