# backend-python/app/data/seed_codes.py

"""
Utility for storing Vérité Sauvage security codes and metadata on disk.

We keep a JSON mapping of::

    productId (0x + 64 hex) -> {
        "shortCode": "VS2BOF",
        "meta": { ... optional bag metadata ... },
        "createdAt": "<ISO timestamp>",
        "history": [
            {
                "at": "<ISO timestamp>",
                "source": "admin" | "customer",
                "verdict": "authentic" | "fake",
                "details": { ... optional extra ... }
            },
            ...
        ]
    }

For backward-compatibility with older data, we also support the legacy shape::

    productId -> "VS2BOF"

The JSON file lives next to this module as ``codes.json`` so that it is
easy to inspect or back up.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json
import os
import re
import secrets
from datetime import datetime, timezone

CODES_FILE = Path(__file__).with_name("codes.json")

# We avoid ambiguous characters like 0,1,I,O,L
ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


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
    """
    Normalise and validate a productId.

    * must be a string
    * must start with "0x"
    * must contain exactly 64 hex characters after 0x
    """
    if not isinstance(pid, str):
        raise ValueError("productId must be a string")
    pid = pid.strip()
    if not pid.startswith("0x"):
        raise ValueError("productId must start with 0x")
    if len(pid) != 66:
        raise ValueError("productId must be 0x + 64 hex characters")
    if not re.fullmatch(r"0x[0-9a-fA-F]{64}", pid):
        raise ValueError("productId must be 0x + 64 hex characters")
    return pid.lower()


def _generate_short_code(length: int = 6) -> str:
    """Generate a random VS security code like VSAB12 or similar."""
    # Prefix 'VS' + 4 random characters by default
    body = "".join(secrets.choice(ALPHABET) for _ in range(length - 2))
    return "VS" + body


def _extract_short_code(value: Any) -> Optional[str]:
    """Extract shortCode from either the new dict shape or legacy string."""
    if isinstance(value, dict):
        sc = value.get("shortCode")
        if isinstance(sc, str):
            return sc
        return None
    if isinstance(value, str):
        return value
    return None


def _extract_meta(value: Any) -> Dict[str, Any]:
    """Extract meta dict from stored value, if any."""
    if isinstance(value, dict):
        meta = value.get("meta")
        if isinstance(meta, dict):
            return dict(meta)
    return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def register_code_for_product(
    pid: str, meta: Optional[Dict[str, Any]] = None
) -> str:
    """
    Ensure a VS code exists for this productId, optionally attaching metadata.

    - Normalises and validates pid
    - If pid already has a code, returns the existing code and merges meta (if given)
    - If not, generates a fresh VS**** code, stores it, and returns it
    """
    key = _normalise_pid(pid)
    codes = _load_codes()

    entry = codes.get(key)

    short_code: Optional[str] = None

    if isinstance(entry, str):
        # Legacy: just "VS2BOF"
        short_code = entry
        entry = {"shortCode": short_code}
    elif isinstance(entry, dict):
        short_code = _extract_short_code(entry)
    else:
        entry = {}

    # Merge metadata if provided
    if meta:
        existing_meta = entry.get("meta")
        if isinstance(existing_meta, dict):
            merged = {**existing_meta, **meta}
        else:
            merged = dict(meta)
        entry["meta"] = merged

    # If we already have a shortCode, just persist merged meta and return
    if short_code:
        codes[key] = entry
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

    entry["shortCode"] = short_code
    entry.setdefault("meta", {})
    entry["createdAt"] = datetime.now(timezone.utc).isoformat()

    codes[key] = entry
    _save_codes(codes)
    return short_code


def get_short_code_for_product(pid: str) -> Optional[str]:
    """Return the shortCode for a given productId, if any."""
    try:
        key = _normalise_pid(pid)
    except ValueError:
        return None
    codes = _load_codes()
    value = codes.get(key)
    return _extract_short_code(value)


def get_meta_for_product(pid: str) -> Dict[str, Any]:
    """Return meta dict for a given productId, or {} if none."""
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


def append_verification_event(
    pid: str,
    source: str,
    verdict: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Append a verification event into codes.json for analytics / traceability.

    - source: "admin" or "customer"
    - verdict: "authentic" or "fake"
    """
    try:
        key = _normalise_pid(pid)
    except ValueError:
        return

    codes = _load_codes()
    entry = codes.get(key)

    if isinstance(entry, str):
        entry = {"shortCode": entry}
    elif not isinstance(entry, dict):
        entry = {}

    history = entry.get("history")
    if not isinstance(history, list):
        history = []

    event: Dict[str, Any] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "verdict": verdict,
    }
    if details:
        event["details"] = details

    history.append(event)
    entry["history"] = history
    codes[key] = entry
    _save_codes(codes)
