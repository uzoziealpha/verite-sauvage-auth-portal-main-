# backend-python/app/data/seed_codes.py

"""Utility for storing Vérité Sauvage security codes on disk.

We keep a simple JSON mapping of::

    productId (0x + 64 hex) -> 6-character VS code (e.g. "VS2BOF")

The JSON file lives next to this module as ``codes.json`` so that it is
easy to back up or inspect:

    app/data/codes.json

The public functions you should use are:

    * register_code_for_product(pid) -> str
    * get_short_code_for_product(pid) -> Optional[str]
    * check_short_code(pid, code) -> bool

These are used by the /codes/register admin endpoint and the
/customer-verify public endpoint.
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Dict, Optional

# Characters we use for the suffix part of the VS code.
# (No O/0 or I/1 to avoid confusion.)
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

# Location of codes.json on disk
CODES_FILE = Path(__file__).resolve().parent / "codes.json"


def _normalise_pid(pid: str) -> str:
    """Normalise and validate a productId.

    * must be a string
    * must start with '0x'
    * must be exactly 0x + 64 hex characters
    * we always store it in lowercase
    """
    if not isinstance(pid, str):
        raise ValueError("product_id must be a string")

    pid = pid.strip()
    if not pid.startswith("0x") or len(pid) != 66:
        raise ValueError("product_id must be 0x + 64 hex characters.")

    hex_part = pid[2:]
    try:
        int(hex_part, 16)
    except ValueError:
        raise ValueError("product_id contains non-hex characters.")

    return "0x" + hex_part.lower()


def _load_codes() -> Dict[str, str]:
    """Load the mapping {productId: short_code} from JSON file."""
    if not CODES_FILE.exists():
        return {}

    try:
        with CODES_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # normalise keys to lowercase
            return {str(k).lower(): str(v) for k, v in data.items()}
        return {}
    except Exception:
        # If file is corrupted, start fresh (in production you may want logging)
        return {}


def _save_codes(codes: Dict[str, str]) -> None:
    """Persist the mapping to JSON file in a safe way."""
    os.makedirs(CODES_FILE.parent, exist_ok=True)

    # Write to a temporary file then replace atomically to avoid partial writes.
    tmp_path = CODES_FILE.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(codes, f, indent=2, sort_keys=True)
    tmp_path.replace(CODES_FILE)


def _generate_short_code() -> str:
    """Generate a new 6-character VS security code.

    Always starts with "VS" and uses the ALPHABET above for the suffix.
    """
    suffix = "".join(random.choice(ALPHABET) for _ in range(4))
    return "VS" + suffix


def register_code_for_product(pid: str) -> str:
    """Ensure a VS code exists for this productId and return it.

    * If a code is already stored for this pid, we return that.
    * Otherwise we generate a new unique code, save it to codes.json,
      and return the new code.
    """
    key = _normalise_pid(pid)
    codes = _load_codes()

    # Already exists -> just return
    existing = codes.get(key)
    if existing:
        return str(existing)

    # Generate a unique code (very unlikely collision in practice, but we guard)
    existing_codes = set(codes.values())
    guard = 0
    short_code = _generate_short_code()
    while short_code in existing_codes and guard < 1000:
        short_code = _generate_short_code()
        guard += 1

    codes[key] = short_code
    _save_codes(codes)
    return short_code


def get_short_code_for_product(pid: str) -> Optional[str]:
    """Return the stored 6-character code for a given productId, or None."""
    try:
        key = _normalise_pid(pid)
    except ValueError:
        return None
    codes = _load_codes()
    return codes.get(key)


def check_short_code(pid: str, code: str) -> bool:
    """Return True if the provided code matches the stored code for pid."""
    stored = get_short_code_for_product(pid)
    if not stored:
        return False
    return stored.lower() == str(code).strip().lower()
