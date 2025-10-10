"""Authentication utilities with PostgreSQL and Redis."""

from __future__ import annotations

import hashlib
import logging
import os
import random
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict

from jose import JWTError, jwt

from web.backend.database import (
    get_user_by_username,
    get_user_by_phone,
    create_user,
    update_user_password,
)
from web.backend.redis_client import (
    get_session,
    set_session,
    delete_session,
    extend_session,
    set_phone_code,
    get_phone_code,
    delete_phone_code,
    get_phone_code_ttl,
)

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
DEFAULT_TOKEN_EXPIRE_MINUTES = 60
DEFAULT_TOKEN_RENEW_THRESHOLD_MINUTES = 15
PHONE_CODE_LENGTH = int(os.getenv("PHONE_CODE_LENGTH", "6"))
PHONE_CODE_TTL_SECONDS = int(os.getenv("PHONE_CODE_TTL_SECONDS", "300"))
PHONE_CODE_RESEND_BLOCK_SECONDS = int(os.getenv("PHONE_CODE_RESEND_SECONDS", "60"))
PHONE_NUMBER_PATTERN = re.compile(r"^\+?\d{6,15}$")
PHONE_PURPOSE_REGISTER = "register"
PHONE_PURPOSE_RESET = "reset"


def _get_secret_key() -> str:
    """Get JWT secret key from environment."""
    secret = os.getenv("AUTH_SECRET_KEY") or os.getenv("SECRET_KEY")
    if not secret:
        logger.warning("AUTH_SECRET_KEY is not set; using insecure default. Set it in the environment.")
        secret = "change-me-in-production"
    return secret


SECRET_KEY = _get_secret_key()
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", DEFAULT_TOKEN_EXPIRE_MINUTES)
)
TOKEN_RENEW_THRESHOLD_MINUTES = int(
    os.getenv("AUTH_TOKEN_RENEW_THRESHOLD_MINUTES", DEFAULT_TOKEN_RENEW_THRESHOLD_MINUTES)
)


def hash_password_md5(password: str) -> str:
    """Hash password using MD5.

    Args:
        password: Plain text password

    Returns:
        MD5 hash string
    """
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plain password against the stored hash."""

    if not stored_hash or "$" in stored_hash:
        logger.warning("Invalid password hash format")
        return False

    candidate = hashlib.md5(password.encode("utf-8")).hexdigest()
    return candidate == stored_hash


def get_user(username: str) -> Optional[dict]:
    """Get user from database.

    Args:
        username: Username

    Returns:
        User dict or None if not found
    """
    return get_user_by_username(username)


def get_user_by_phone_number(phone: str) -> Optional[dict]:
    """Helper to fetch user by phone."""

    normalized = normalize_phone_number(phone)
    return get_user_by_phone(normalized)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user with username and password.

    Args:
        username: Username
        password: Plain text password

    Returns:
        User dict if authentication successful, None otherwise
    """
    user = get_user(username)
    if not user:
        logger.info(f"User not found: {username}")
        return None

    if user.get("disabled"):
        logger.info(f"User disabled: {username}")
        return None

    if not verify_password(password, user["password_hash"]):
        logger.info(f"Invalid password for user: {username}")
        return None

    return user


def normalize_phone_number(phone: str) -> str:
    """Normalize phone number by trimming whitespace."""

    phone = phone.strip()
    if phone.startswith("+"):
        return "+" + re.sub(r"\D", "", phone[1:])
    return re.sub(r"\D", "", phone)


def validate_phone_number(phone: str) -> bool:
    """Return True if phone number matches expected pattern."""

    normalized = normalize_phone_number(phone)
    return bool(PHONE_NUMBER_PATTERN.fullmatch(normalized))


def _build_phone_metadata() -> Dict[str, str]:
    block_until = datetime.utcnow() + timedelta(seconds=PHONE_CODE_RESEND_BLOCK_SECONDS)
    return {"resend_block_until": block_until.isoformat()}


def generate_numeric_code(length: int = PHONE_CODE_LENGTH) -> str:
    """Generate a zero-padded numeric verification code."""

    if length <= 0:
        raise ValueError("Code length must be positive")
    max_value = 10 ** length
    return str(random.randint(0, max_value - 1)).zfill(length)


def send_phone_verification_code(phone: str, purpose: str) -> Tuple[str, int]:
    """Generate and store a phone verification code.

    Returns the code for downstream integrations (e.g., SMS provider).
    """

    normalized = normalize_phone_number(phone)
    if not validate_phone_number(normalized):
        raise ValueError("手机号格式不正确")

    ttl = get_phone_code_ttl(normalized, purpose)
    existing_payload = get_phone_code(normalized, purpose)
    if existing_payload and ttl:
        # Enforce resend blocking window based on metadata
        block_until_str = existing_payload.get("resend_block_until")
        if block_until_str:
            try:
                block_until = datetime.fromisoformat(block_until_str)
                if block_until > datetime.utcnow():
                    raise RuntimeError("验证码请求过于频繁，请稍后再试")
            except ValueError:
                logger.debug("Invalid resend_block_until format; regenerating code")

    code = generate_numeric_code(PHONE_CODE_LENGTH)
    metadata = _build_phone_metadata()
    set_phone_code(normalized, purpose, code, PHONE_CODE_TTL_SECONDS, metadata)

    logger.info("Phone verification code generated for %s (purpose=%s)", normalized, purpose)
    return code, PHONE_CODE_TTL_SECONDS


def verify_phone_code(phone: str, purpose: str, code: str, consume: bool = True) -> bool:
    """Validate the user provided code.

    Args:
        phone: Phone number provided by user
        purpose: Purpose string ('register' or 'reset')
        code: Code provided by user
        consume: When True, delete stored code on success
    """

    normalized = normalize_phone_number(phone)
    stored = get_phone_code(normalized, purpose)
    if not stored:
        return False

    if stored.get("code") != code:
        return False

    if consume:
        delete_phone_code(normalized, purpose)

    return True


def register_user_with_phone(
    username: str,
    password: str,
    phone: str,
    full_name: Optional[str] = None,
) -> bool:
    """Create a new user account linked to a phone number."""

    password_hash = hash_password_md5(password)
    normalized_phone = normalize_phone_number(phone)
    return create_user(username=username, password_hash=password_hash, full_name=full_name, phone=normalized_phone)


def reset_password_with_phone(phone: str, new_password: str) -> bool:
    """Update user's password using phone lookup."""

    user = get_user_by_phone_number(phone)
    if not user:
        logger.info("Attempted password reset for unknown phone: %s", phone)
        return False

    password_hash = hash_password_md5(new_password)
    return update_user_password(user["username"], password_hash)


def compute_expires_in(expires_at: datetime) -> int:
    """Compute seconds until expiration.

    Args:
        expires_at: Expiration datetime

    Returns:
        Seconds until expiration (minimum 1)
    """
    remaining = expires_at - datetime.utcnow()
    return max(1, int(remaining.total_seconds()))


def create_access_token(
    subject: str, user_data: Optional[dict] = None, expires_delta: Optional[timedelta] = None
) -> Tuple[str, datetime]:
    """Create JWT access token and store session in Redis.

    Args:
        subject: Username (token subject)
        user_data: Additional user data to store in session
        expires_delta: Custom expiration timedelta

    Returns:
        Tuple of (token, expiration_datetime)
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": subject, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Store session in Redis
    session_data = {
        "username": subject,
        "expires_at": expire.isoformat(),
        **(user_data or {}),
    }
    expire_seconds = int((expire - datetime.utcnow()).total_seconds())
    set_session(token, session_data, expire_seconds)

    return token, expire


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token, check session in Redis.

    Args:
        token: JWT token string

    Returns:
        Token payload if valid, None otherwise
    """
    try:
        # First decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if not username:
            logger.debug("Token missing subject")
            return None

        # Check session in Redis
        session = get_session(token)
        if not session:
            logger.debug("Session not found in Redis")
            return None

        # Verify user still exists in database
        user = get_user(username)
        if not user or user.get("disabled"):
            logger.debug(f"User not found or disabled: {username}")
            delete_session(token)
            return None

        return payload

    except JWTError as exc:
        logger.debug(f"Failed to decode token: {exc}")
        return None
    except Exception as exc:
        logger.error(f"Unexpected error decoding token: {exc}")
        return None


def should_refresh_token(exp_value: Optional[int]) -> bool:
    """Determine if token should be refreshed based on remaining TTL.

    Args:
        exp_value: Expiration timestamp from JWT payload

    Returns:
        True if token should be refreshed
    """
    if exp_value is None:
        return False

    try:
        expires_at = datetime.utcfromtimestamp(exp_value)
    except (TypeError, ValueError, OSError):
        logger.debug(f"Invalid exp value: {exp_value}")
        return False

    remaining = expires_at - datetime.utcnow()
    return remaining <= timedelta(minutes=TOKEN_RENEW_THRESHOLD_MINUTES)


def logout_user(token: str) -> bool:
    """Logout user by deleting session from Redis.

    Args:
        token: JWT token string

    Returns:
        True if session deleted successfully
    """
    try:
        delete_session(token)
        return True
    except Exception as exc:
        logger.error(f"Failed to logout user: {exc}")
        return False
