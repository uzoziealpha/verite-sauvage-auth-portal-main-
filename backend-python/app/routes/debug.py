# backend-python/app/routes/debug.py

from fastapi import APIRouter
from app.services.web3loader import get_web3, RPC_URL, CONTRACT_ADDRESS, ARTIFACT_PATH

router = APIRouter()


@router.get("/debug/contract")
def debug_contract():
    """
    Safe debug endpoint for contract + RPC wiring.
    It NEVER throws – even if RPC is down or contract is missing.
    """
    info = {
        "ok": True,
        "rpc_url": RPC_URL,
        "contract_address": CONTRACT_ADDRESS,
        "artifact_path": ARTIFACT_PATH,
        "has_code": False,
        "code_hex_prefix": None,
        "error": None,
    }

    try:
        web3 = get_web3()
    except Exception as e:
        info["error"] = f"get_web3 failed: {e}"
        return info

    try:
        code = web3.eth.get_code(CONTRACT_ADDRESS)
        has_code = bool(code and code != b"")
        info["has_code"] = has_code
        if has_code:
            info["code_hex_prefix"] = "0x" + code.hex()[:40]
    except Exception as e:
        info["error"] = f"eth_getCode failed: {e}"

    return info
