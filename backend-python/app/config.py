# app/config.py

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central config object for the backend.

    Values are loaded from environment variables and .env:
      - RPC_URL
      - CONTRACT_ADDRESS
      - BACKEND_BASE_URL
      - CORS_ORIGINS
      - DATABASE_URL
    """

    # Hardhat local by default (for local testing)
    RPC_URL: str = "http://127.0.0.1:8545"

    # Default local contract address (Hardhat deploy)
    CONTRACT_ADDRESS: str = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

    # Where this backend is reachable (mainly for self-links / debugging)
    BACKEND_BASE_URL: str = "http://127.0.0.1:4000"

    # Comma-separated list of allowed CORS origins
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Optional DB URL – seed_codes_db.py will also read this
    DATABASE_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def cors_origins_list(self) -> List[str]:
        """
        Utility: turn the CORS_ORIGINS string into a clean list.
        """
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    """
    Cached singleton Settings instance.
    """
    return Settings()


# This is what your other modules import:
settings = get_settings()
