from fastapi import APIRouter
from web3 import Web3

from app.services.web3loader import get_web3
from app.utils.settings import settings

router = APIRouter()


@router.get("/contract")
def debug_contract():
    """
    Debug endpoint to verify RPC connection and contract deployment.
    """
    web3 = get_web3()
    chain_id = web3.eth.chain_id

    address = Web3.to_checksum_address(settings.contract_address)
    code = web3.eth.get_code(address)
    has_code = code not in (b"", b"\x00", None)

    return {
        "rpc_url": settings.rpc_url,
        "chain_id": chain_id,
        "contract_address": address,
        "has_code": has_code,
    }
