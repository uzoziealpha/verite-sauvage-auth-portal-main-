import json
import os
from pathlib import Path
from typing import Any, Dict

from web3 import Web3


# --- Configuration ---

# Default to local Hardhat for development
RPC_URL: str = os.getenv("RPC_URL", "http://127.0.0.1:8545")

# 31337 = Hardhat chain ID (Hardhat local)
CHAIN_ID: int = int(os.getenv("CHAIN_ID", "31337"))

# Resolve repo root:
# web3loader.py -> services -> app -> backend-python -> REPO_ROOT
REPO_ROOT = Path(__file__).resolve().parents[3]

# Path to the compiled contract artifact (from solidity build)
ARTIFACT_PATH = (
    REPO_ROOT
    / "solidity"
    / "artifacts"
    / "contracts"
    / "FakeProdDetector.sol"
    / "FakeProdDetector.json"
)

if not ARTIFACT_PATH.exists():
    raise RuntimeError(f"Contract artifact not found at: {ARTIFACT_PATH}")

with ARTIFACT_PATH.open("r") as f:
    CONTRACT_ARTIFACT = json.load(f)

ABI = CONTRACT_ARTIFACT.get("abi")
if not ABI:
    raise RuntimeError("No ABI found in FakeProdDetector.json artifact")

# Local default address from Hardhat network info, if present
networks = CONTRACT_ARTIFACT.get("networks", {})
local_address = None
if str(CHAIN_ID) in networks:
    local_address = networks[str(CHAIN_ID)].get("address")

# Fallback to the classic Hardhat deterministic address
if not local_address:
    local_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

CONTRACT_ADDRESS: str = os.getenv("CONTRACT_ADDRESS", local_address)


# --- Helpers ---


def get_web3() -> Web3:
    """
    Return a Web3 instance pointing at RPC_URL.
    """
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    return web3


def get_contract(web3: Web3):
    """
    Return a Web3 contract instance for FakeProdDetector.
    Raises if the address has no code.
    """
    if not web3.is_connected():
        raise RuntimeError(f"Cannot connect to RPC at {RPC_URL}")

    checksum_address = web3.to_checksum_address(CONTRACT_ADDRESS)
    code = web3.eth.get_code(checksum_address)

    if not code or len(code) == 0:
        raise RuntimeError(
            f"No contract code at {CONTRACT_ADDRESS} on {RPC_URL}. "
            f"Start your node and deploy the contract, or update CONTRACT_ADDRESS."
        )

    return web3.eth.contract(address=checksum_address, abi=ABI)


def get_contract_debug_info() -> Dict[str, Any]:
    """
    Safe, non-throwing helper for /debug/contract.
    Always returns a JSON-serializable dict, even if RPC or contract are broken.
    """
    info: Dict[str, Any] = {
        "ok": False,
        "error": None,
        "rpc_url": RPC_URL,
        "contract_address": CONTRACT_ADDRESS,
        "has_code": False,
        "code_hex_prefix": None,
        "artifact_path": str(ARTIFACT_PATH),
    }

    try:
        web3 = get_web3()
        if not web3.is_connected():
            info["error"] = f"Cannot connect to RPC at {RPC_URL}"
            return info

        checksum_address = web3.to_checksum_address(CONTRACT_ADDRESS)
        code = web3.eth.get_code(checksum_address)

        if code and len(code) > 0:
            info["has_code"] = True
            info["code_hex_prefix"] = code.hex()[:18]
        else:
            info["has_code"] = False
            info["error"] = "No code at contract address"

        info["ok"] = True
        return info
    except Exception as e:
        info["error"] = str(e)
        return info
