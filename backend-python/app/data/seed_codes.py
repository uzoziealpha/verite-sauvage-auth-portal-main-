# backend-python/app/data/seed_codes.py

"""Utility for storing Vérité Sauvage security codes and metadata on disk.

We keep a JSON mapping of::

    productId (0x + 64 hex) -> {
        "shortCode": "VS2BOF",
        "meta": { ... optional bag metadata ... }
    }

For backward-compatibility with older data, we also support the legacy shape::

    productId -> "VS2BOF"

The JSON file lives next to this module as ``codes.json`` so that it is
easy to back up or inspect:

    app/data/codes.json

Public functions:

    * register_code_for_product(pid, meta=None) -> str
    * get_short_code_for_product(pid) -> Optional[str]
    * get_meta_for_product(pid) -> Dict[str, Any]
    * check_short_code(pid, code) -> bool
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

HERE = Path(__file__).parent
CODES_FILE = HERE / "codes.json"

# Allowed characters for VS codes (excluding confusing ones)
ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"  # no 0,1,I,O,L


def _load_codes() -> Dict[str, Any]:
    """Load the mapping from JSON; return {} if file missing or invalid."""
    if not CODES_FILE.exists():
        return {}
    try:
        with CODES_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        # If it's corrupted, just ignore and start fresh in memory
        return {}
    return {}


def _save_codes(codes: Dict[str, Any]) -> None:
    """Persist the mapping to JSON file in a safe way."""
    os.makedirs(CODES_FILE.parent, exist_ok=True)

    tmp_path = CODES_FILE.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(codes, f, indent=2, sort_keys=True)
    tmp_path.replace(CODES_FILE)


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
    int(hex_part, 16)  # will raise ValueError if not valid hex
    return "0x" + hex_part.lower()


def _generate_short_code() -> str:
    """Generate a new 6-character VS security code.

    Always starts with "VS" and uses the ALPHABET above for the suffix.
    """
    suffix = "".join(random.choice(ALPHABET) for _ in range(4))
    return "VS" + suffix


def _extract_short_code(value: Any) -> Optional[str]:
    """Given a stored value (string or object), return the short code if present."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # support multiple field names just in case
        for key in ("shortCode", "vsCode", "code"):
            code = value.get(key)
            if isinstance(code, str) and code:
                return code
    return None


def _extract_meta(value: Any) -> Dict[str, Any]:
    """Extract meta dict from stored value, if any."""
    if isinstance(value, dict):
        meta = value.get("meta")
        if isinstance(meta, dict):
            return dict(meta)
    return {}


def register_code_for_product(pid: str, meta: Optional[Dict[str, Any]] = None) -> str:
    """Ensure a VS code exists for this productId, optionally attaching metadata.

    - Normalises and validates pid
    - If pid already has a code, returns the existing code and merges meta (if given)
    - If not, generates a fresh VS***** code, stores it, and returns it
    """
    key = _normalise_pid(pid)
    codes = _load_codes()

    existing = codes.get(key)
    if existing is not None:
        # Already have an entry; keep its code, merge any new meta
        short_code = _extract_short_code(existing)
        if short_code is None:
            # weird/invalid entry -> generate a new one but keep meta if present
            existing_meta = _extract_meta(existing)
            if meta:
                existing_meta.update(meta)
            short_code = _generate_short_code()
            codes[key] = {"shortCode": short_code, "meta": existing_meta}
            _save_codes(codes)
            return short_code

        # Normal case: valid existing code
        existing_meta = _extract_meta(existing)
        if meta:
            existing_meta.update(meta)

        # Store back in normalised object form
        codes[key] = {
            "shortCode": short_code,
            "meta": existing_meta,
        }
        _save_codes(codes)
        return short_code

    # No entry yet -> generate a unique code
    existing_codes = set()
    for v in codes.values():
        c = _extract_short_code(v)
        if c:
            existing_codes.add(c)

    guard = 0
    short_code = _generate_short_code()
    while short_code in existing_codes and guard < 1000:
        short_code = _generate_short_code()
        guard += 1

    codes[key] = {
        "shortCode": short_code,
        "meta": dict(meta) if meta else {},
    }
    _save_codes(codes)
    return short_code


def get_short_code_for_product(pid: str) -> Optional[str]:
    """Return the stored 6-character code for a given productId, or None."""
    try:
        key = _normalise_pid(pid)
    except ValueError:
        return None
    codes = _load_codes()
    value = codes.get(key)
    return _extract_short_code(value)


def get_meta_for_product(pid: str) -> Dict[str, Any]:
    """Return stored metadata for a given productId (may be empty)."""
    try:
        key = _normalise_pid(pid)
    except ValueError:
        return {}
    codes = _load_codes()
    value = codes.get(key)
    return _extract_meta(value)


def check_short_code(pid: str, code: str) -> bool:
    """Return True if the provided code matches the stored code for pid."""
    stored = get_short_code_for_product(pid)
    if not stored:
        return False
    return stored.lower() == str(code).strip().lower()
