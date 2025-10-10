"""Redis client for session management."""

import os
import logging
import json
from datetime import datetime
from typing import Optional, Any, Dict

import redis

logger = logging.getLogger(__name__)

# Redis configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Redis client
_redis_client: Optional[redis.Redis] = None

PHONE_CODE_TTL_SECONDS = int(os.getenv("PHONE_CODE_TTL_SECONDS", "300"))
PHONE_CODE_PREFIX = "phone:code"


def init_redis_client():
    """Initialize Redis client."""
    global _redis_client

    try:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

        # Test connection
        _redis_client.ping()
        logger.info(f"Redis client initialized and connected to {REDIS_HOST}:{REDIS_PORT}")

    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {e}")
        raise


def close_redis_client():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        logger.info("Redis client closed")


def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client


# Session management functions
def set_session(token: str, data: dict, expire_seconds: int = 3600):
    """Store session data in Redis."""
    try:
        client = get_redis_client()
        key = f"session:{token}"
        client.setex(key, expire_seconds, json.dumps(data))
        logger.debug(f"Session stored for token: {token[:8]}...")
    except Exception as e:
        logger.error(f"Failed to store session: {e}")
        raise


def get_session(token: str) -> Optional[dict]:
    """Get session data from Redis."""
    try:
        client = get_redis_client()
        key = f"session:{token}"
        data = client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        return None


def delete_session(token: str):
    """Delete session from Redis."""
    try:
        client = get_redis_client()
        key = f"session:{token}"
        client.delete(key)
        logger.debug(f"Session deleted for token: {token[:8]}...")
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")


def extend_session(token: str, expire_seconds: int = 3600) -> bool:
    """Extend session expiration time."""
    try:
        client = get_redis_client()
        key = f"session:{token}"
        result = client.expire(key, expire_seconds)
        return bool(result)
    except Exception as e:
        logger.error(f"Failed to extend session: {e}")
        return False


def _phone_code_key(phone: str, purpose: str) -> str:
    sanitized_phone = phone.replace(" ", "")
    return f"{PHONE_CODE_PREFIX}:{purpose}:{sanitized_phone}"


def set_phone_code(
    phone: str,
    purpose: str,
    code: str,
    ttl_seconds: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Store phone verification code in Redis."""
    payload = {
        "code": code,
        "purpose": purpose,
        "created_at": datetime.utcnow().isoformat(),
    }
    if metadata:
        payload.update(metadata)

    try:
        client = get_redis_client()
        client.setex(
            _phone_code_key(phone, purpose),
            ttl_seconds or PHONE_CODE_TTL_SECONDS,
            json.dumps(payload),
        )
    except Exception as exc:
        logger.error(f"Failed to store phone code for {phone}: {exc}")
        raise


def get_phone_code(phone: str, purpose: str) -> Optional[Dict[str, Any]]:
    """Retrieve phone verification code payload."""
    try:
        client = get_redis_client()
        data = client.get(_phone_code_key(phone, purpose))
        return json.loads(data) if data else None
    except Exception as exc:
        logger.error(f"Failed to read phone code for {phone}: {exc}")
        return None


def delete_phone_code(phone: str, purpose: str) -> None:
    """Delete stored phone verification code."""
    try:
        client = get_redis_client()
        client.delete(_phone_code_key(phone, purpose))
    except Exception as exc:
        logger.error(f"Failed to delete phone code for {phone}: {exc}")


def get_phone_code_ttl(phone: str, purpose: str) -> Optional[int]:
    """Return remaining TTL (seconds) for the stored code."""
    try:
        client = get_redis_client()
        ttl = client.ttl(_phone_code_key(phone, purpose))
        return ttl if ttl and ttl > 0 else None
    except Exception as exc:
        logger.error(f"Failed to read phone code TTL for {phone}: {exc}")
        return None
