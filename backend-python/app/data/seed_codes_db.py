import os
import re
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

# In dev you can leave DATABASE_URL empty to use SQLite; in production (Railway)
# you'll set DATABASE_URL in the environment to a Postgres connection string.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vs_codes.db")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class VSCode(Base):
    """
    Main table storing the Vérité Sauvage product + VS code mapping.

    Mirrors the structure of codes.json:

    {
      "0x...productId": {
        "meta": {
          "model": "...",
          "color": "...",
          "material": "...",
          "price": 18090,
          "year": 2025
        },
        "shortCode": "VS2Q25"
      }
    }
    """

    __tablename__ = "vs_codes"
    __table_args__ = (
        UniqueConstraint("product_id", name="uq_vs_codes_product_id"),
        UniqueConstraint("short_code", name="uq_vs_codes_short_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(80), nullable=False, index=True)
    short_code = Column(String(16), nullable=False, index=True)

    # Clean product meta columns
    model = Column(String(255), nullable=True)
    color = Column(String(64), nullable=True)
    material = Column(String(64), nullable=True)
    price = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)

    # Optional JSON snapshot of meta (not strictly needed but convenient)
    meta = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )


class VSVerificationEvent(Base):
    """
    Optional history of verifications from admin / customer side.
    """

    __tablename__ = "vs_verification_events"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(80), nullable=False, index=True)
    source = Column(String(32), nullable=False)  # "admin" or "customer"
    verdict = Column(String(32), nullable=False)  # "authentic" or "fake"
    details = Column(JSON, nullable=True)
    at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))


# Create tables automatically on import (simple setup)
Base.metadata.create_all(engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"  # avoid confusing chars (0,1,I,O,L)


def _normalise_pid(pid: str) -> str:
    """
    Ensure productId shape is correct: 0x + 64 hex chars.
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
    """
    Generate a VS security code, e.g. VS2Q25.
    """
    if length < 3:
        length = 3
    body = "".join(secrets.choice(ALPHABET) for _ in range(length - 2))
    return "VS" + body


# ---------------------------------------------------------------------------
# Public API – same names as codes.json helper
# ---------------------------------------------------------------------------


def register_code_for_product(
    pid: str,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Ensure a VS code exists for this product.

    - If row already exists, optionally update model/color/material/price/year.
    - If not, create a new row with a fresh VS code.
    - Returns the shortCode (e.g. "VS2Q25").
    """
    key = _normalise_pid(pid)
    session = SessionLocal()

    try:
        row = (
            session.query(VSCode)
            .filter(VSCode.product_id == key)
            .with_for_update(of=VSCode)
            .first()
        )

        meta = meta or {}
        model = meta.get("model")
        color = meta.get("color")
        material = meta.get("material")
        price = meta.get("price")
        year = meta.get("year")

        if row:
            # Update only fields we got
            if model is not None:
                row.model = model
            if color is not None:
                row.color = color
            if material is not None:
                row.material = material
            if price is not None:
                row.price = int(price)
            if year is not None:
                row.year = int(year)

            # Keep JSON mirror
            row.meta = {
                "model": row.model,
                "color": row.color,
                "material": row.material,
                "price": row.price,
                "year": row.year,
            }

            session.commit()
            session.refresh(row)
            return row.short_code

        # No existing row – generate a new unique short_code
        existing_codes = {
            c for (c,) in session.query(VSCode.short_code).all() if c is not None
        }
        guard = 0
        short_code = _generate_short_code()
        while short_code in existing_codes and guard < 1000:
            short_code = _generate_short_code()
            guard += 1

        new_row = VSCode(
            product_id=key,
            short_code=short_code,
            model=model,
            color=color,
            material=material,
            price=int(price) if price is not None else None,
            year=int(year) if year is not None else None,
        )
        new_row.meta = {
            "model": new_row.model,
            "color": new_row.color,
            "material": new_row.material,
            "price": new_row.price,
            "year": new_row.year,
        }

        session.add(new_row)
        session.commit()
        session.refresh(new_row)
        return new_row.short_code
    finally:
        session.close()


def get_short_code_for_product(pid: str) -> Optional[str]:
    try:
        key = _normalise_pid(pid)
    except ValueError:
        return None

    session = SessionLocal()
    try:
        row = session.query(VSCode).filter(VSCode.product_id == key).first()
        if not row:
            return None
        return row.short_code
    finally:
        session.close()


def get_meta_for_product(pid: str) -> Dict[str, Any]:
    """
    Returns meta with shape:

    {
      "model": "...",
      "color": "...",
      "material": "...",
      "price": 18090,
      "year": 2025
    }
    """
    try:
      key = _normalise_pid(pid)
    except ValueError:
      return {}

    session = SessionLocal()
    try:
        row = session.query(VSCode).filter(VSCode.product_id == key).first()
        if not row:
            return {}
        return {
            "model": row.model,
            "color": row.color,
            "material": row.material,
            "price": row.price,
            "year": row.year,
        }
    finally:
        session.close()


def check_short_code(pid: str, code: str) -> bool:
    """
    True if the incoming short_code matches the one stored for this productId.

    We normalise:
    - productId to 0x + 64 hex (lowercase)
    - short_code to uppercase, trimming whitespace

    So "vsz28c", " VSZ28C " etc. all match "VSZ28C" in the DB.
    """
    if not code:
        return False

    # Normalise productId
    try:
        key = _normalise_pid(pid)
    except ValueError:
        return False

    # Normalise incoming code
    incoming = str(code).strip().upper()

    session = SessionLocal()
    try:
        row = (
            session.query(VSCode.short_code)
            .filter(VSCode.product_id == key)
            .first()
        )
        if not row:
            return False

        stored = (row[0] or "").strip().upper()
        return stored == incoming
    finally:
        session.close()


def append_verification_event(
    pid: str,
    source: str,
    verdict: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log verification (admin or customer) into vs_verification_events.
    """
    try:
        key = _normalise_pid(pid)
    except ValueError:
        key = pid

    session = SessionLocal()
    try:
        ev = VSVerificationEvent(
            product_id=key,
            source=source,
            verdict=verdict,
            details=details or {},
        )
        session.add(ev)
        session.commit()
    finally:
        session.close()
