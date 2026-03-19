"""
API key authentication dependency.
Set AGENTPROBE_API_KEY in .env to enable.
If the env var is empty (default), auth is disabled — useful for local dev.
"""
from fastapi import Header, HTTPException, status

from .settings import settings


async def verify_api_key(x_api_key: str = Header(default="")) -> None:
    """FastAPI dependency — inject via Depends(verify_api_key)."""
    if not settings.agentprobe_api_key:
        return  # Auth disabled in dev mode
    if x_api_key != settings.agentprobe_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key. Provide X-API-Key header.",
        )
