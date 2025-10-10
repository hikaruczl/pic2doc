"""Database connection and models for PostgreSQL."""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Dict

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Database configuration from environment
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "ocr_db")
DB_USER = os.getenv("DB_USER", "ocr_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ocr_password")

# Connection pool
_pool: Optional[ThreadedConnectionPool] = None


def init_db_pool(minconn: int = 1, maxconn: int = 10):
    """Initialize the database connection pool."""
    global _pool

    try:
        _pool = ThreadedConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        logger.info("Database connection pool initialized")

        # Test connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                logger.info(f"Connected to PostgreSQL: {version}")

    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise


def close_db_pool():
    """Close all database connections in the pool."""
    global _pool
    if _pool:
        _pool.closeall()
        logger.info("Database connection pool closed")


@contextmanager
def get_db_connection():
    """Get a database connection from the pool."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized")

    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


USER_COLUMNS = "id, username, password_hash, full_name, phone, disabled, created_at, updated_at"


def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username from database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT {columns}
                    FROM users
                    WHERE username = %s
                    """.format(columns=USER_COLUMNS),
                    (username,),
                )
                row = cur.fetchone()
                return dict(row) if row else None
    except Exception as e:
        logger.error(f"Failed to get user {username}: {e}")
        return None


def get_user_by_phone(phone: str) -> Optional[Dict]:
    """Get user by phone number from database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT {columns}
                    FROM users
                    WHERE phone = %s
                    """.format(columns=USER_COLUMNS),
                    (phone,),
                )
                row = cur.fetchone()
                return dict(row) if row else None
    except Exception as e:
        logger.error(f"Failed to get user by phone {phone}: {e}")
        return None


def create_user(
    username: str,
    password_hash: str,
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
) -> bool:
    """Create a new user in the database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username, password_hash, full_name, phone)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (username, password_hash, full_name, phone),
                )
        logger.info(f"User {username} created successfully")
        return True
    except psycopg2.IntegrityError:
        logger.warning(f"User {username} already exists")
        return False
    except Exception as e:
        logger.error(f"Failed to create user {username}: {e}")
        return False


def update_user_password(username: str, password_hash: str) -> bool:
    """Update user password."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET password_hash = %s, updated_at = NOW()
                    WHERE username = %s
                    """,
                    (password_hash, username)
                )
        logger.info(f"Password updated for user {username}")
        return True
    except Exception as e:
        logger.error(f"Failed to update password for {username}: {e}")
        return False
