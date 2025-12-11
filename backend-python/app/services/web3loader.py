# backend-python/app/services/web3loader.py

from pathlib import Path
from typing import Any, Dict

import json
from web3 import Web3
from web3.contract import Contract
from web3.types import ChecksumAddress

from app.utils.settings import settings

# ---------------------------------------------------------------------------
# Module-level constants (for backward compatibility with existing imports)
# ---------------------------------------------------------------------------

# What debug.py expects:
# from app.services.web3loader import get_web3, RPC_URL, CONTRACT_ADDRESS, ARTIFACT_PATH

RPC_URL: str = settings.rpc_url
# May be an empty string if not set – we normalize it here
CONTRACT_ADDRESS: str = (settings.contract_address or "").strip()
ARTIFACT_PATH: Path = Path(settings.contract_artifact)


# ---------------------------------------------------------------------------
# Web3 helpers
# ---------------------------------------------------------------------------

def get_web3() -> Web3:
    """
    Return a Web3 instance connected to the configured RPC URL.
    """
    if not RPC_URL:
        raise RuntimeError("RPC_URL is not set. Check your backend .env file.")

    web3 = Web3(Web3.HTTPProvider(RPC_URL))

    if not web3.is_connected():
        raise RuntimeError(f"Unable to connect to RPC at {RPC_URL}")

    return web3


def _load_artifact() -> Dict[str, Any]:
    """
    Load the contract artifact JSON from ARTIFACT_PATH.
    Path may be relative to the backend root.
    """
    artifact_path = ARTIFACT_PATH

    # Resolve relative to backend root (backend-python/)
    if not artifact_path.is_absolute():
        backend_root = Path(__file__).resolve().parents[2]  # .../backend-python
        artifact_path = backend_root / artifact_path

    if not artifact_path.exists():
        raise RuntimeError(f"Contract artifact not found at: {artifact_path}")

    with artifact_path.open("r", encoding="utf-8") as f:
        artifact = json.load(f)

    return artifact


def _resolve_contract_address(web3: Web3, artifact: Dict[str, Any]) -> ChecksumAddress:
    """
    Decide which contract address to use.

    Priority:
    1. CONTRACT_ADDRESS from settings (if non-empty).
    2. Address from artifact["networks"][chain_id]["address"].
    """
    raw_env_addr = CONTRACT_ADDRESS

    # 1) If CONTRACT_ADDRESS is set in .env and not blank, use that
    if raw_env_addr:
        return Web3.to_checksum_address(raw_env_addr)

    # 2) Otherwise, fall back to artifact.networks[chainId].address
    networks = artifact.get("networks") or {}
    chain_id = web3.eth.chain_id
    net_info = networks.get(str(chain_id))

    if not net_info or "address" not in net_info:
        raise RuntimeError(
            f"No contract address found for chain_id {chain_id} in artifact "
            f"and CONTRACT_ADDRESS env var is not set. "
            f"Did you deploy the contract and copy the artifact?"
        )

    return Web3.to_checksum_address(net_info["address"])


def get_contract(web3: Web3) -> Contract:
    """
    Return a web3 Contract instance using artifact + configured address.

    Raises a helpful RuntimeError if there is no code at that address.
    """
    artifact = _load_artifact()
    address = _resolve_contract_address(web3, artifact)

    abi = artifact.get("abi")
    if not abi:
        raise RuntimeError("Artifact is missing 'abi' field.")

    # Sanity check: is there code at that address?
    code = web3.eth.get_code(address)
    if code in (b"", b"\x00", None):
        raise RuntimeError(
            f"No contract code at {address} on {RPC_URL}. "
            f"Start your node and deploy the contract, or update CONTRACT_ADDRESS."
        )

    contract = web3.eth.contract(address=address, abi=abi)
    return contract
