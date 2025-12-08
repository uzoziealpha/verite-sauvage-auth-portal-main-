# backend-python/app/security.py

import os
from fastapi import Header, HTTPException, status

# Set this in your .env / hosting environment for production
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")


async def require_admin(x_admin_token: str = Header(default="")):
    """
    Simple header-based admin auth.

    For protected routes, frontend must send:
      X-Admin-Token: <ADMIN_API_KEY>

    If ADMIN_API_KEY is empty (dev mode), auth is effectively disabled.
    """
    if not ADMIN_API_KEY:
        # dev / local mode – keep endpoints open
        return

    if x_admin_token != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized",
        )
