"""
API key authentication dependency.
Set AGENTPROBE_API_KEY in .env to enable.
If the env var is empty (default), auth is disabled — useful for local dev.
"""
import logging
import secrets

from fastapi import Header, HTTPException, Request, status

from .settings import settings

logger = logging.getLogger(__name__)


async def verify_api_key(
    request: Request,
    x_api_key: str = Header(default=""),
) -> None:
    """FastAPI dependency — inject via Depends(verify_api_key)."""
    if not settings.agentprobe_api_key:
        return  # Auth disabled in dev mode
    if not secrets.compare_digest(x_api_key, settings.agentprobe_api_key):
        client_ip = request.client.host if request.client else "unknown"
        logger.warning("Failed auth attempt from %s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key. Provide X-API-Key header.",
        )
