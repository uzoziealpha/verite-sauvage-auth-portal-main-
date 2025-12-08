# backend-python/app/utils/settings.py

from typing import Optional, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central config for the backend.

    Reads from backend-python/.env (or process env) and exposes:
      - rpc_url
      - contract_address
      - contract_artifact
      - backend_base_url
      - public_verify_base_url
      - cors_origins (as a comma-separated string)
    """

    # Hardhat / RPC config
    rpc_url: str = Field(
        default="http://127.0.0.1:8545",
        alias="RPC_URL",
    )

    # If empty, we will try to read address from the artifact's networks[chainId]
    contract_address: str = Field(
        default="",
        alias="CONTRACT_ADDRESS",
    )

    # Relative to backend root by default
    contract_artifact: str = Field(
        default="contracts/FakeProdDetector.json",
        alias="CONTRACT_ARTIFACT",
    )

    # Backend base URL (used for QR URLs, etc.)
    backend_base_url: str = Field(
        default="http://127.0.0.1:4000",
        alias="BACKEND_BASE_URL",
    )

    # Optional public-facing verify URL (for production / deployed envs)
    public_verify_base_url: Optional[str] = Field(
        default=None,
        alias="PUBLIC_VERIFY_BASE_URL",
    )

    # Comma-separated list of allowed origins for CORS
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:5175",
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS env (comma-separated string) into a clean list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
