#!/usr/bin/env python3
"""
User management script for OCR system.
Create, update, and manage users in PostgreSQL database.
"""

import sys
import argparse
import getpass
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web.backend.database import init_db_pool, create_user, update_user_password, close_db_pool
from web.backend.auth import hash_password_md5


def create_user_cli(username: str, full_name: str = None):
    """Create a new user interactively."""
    password = getpass.getpass("Enter password: ")
    password_confirm = getpass.getpass("Confirm password: ")

    if password != password_confirm:
        print("Error: Passwords do not match")
        return False

    password_hash = hash_password_md5(password)

    if create_user(username, password_hash, full_name):
        print(f"User '{username}' created successfully")
        return True
    else:
        print(f"Failed to create user '{username}'")
        return False


def update_password_cli(username: str):
    """Update user password interactively."""
    password = getpass.getpass("Enter new password: ")
    password_confirm = getpass.getpass("Confirm new password: ")

    if password != password_confirm:
        print("Error: Passwords do not match")
        return False

    password_hash = hash_password_md5(password)

    if update_user_password(username, password_hash):
        print(f"Password updated for user '{username}'")
        return True
    else:
        print(f"Failed to update password for user '{username}'")
        return False


def main():
    parser = argparse.ArgumentParser(description="User management for OCR system")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create user command
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument("username", help="Username")
    create_parser.add_argument("--full-name", help="Full name (optional)")

    # Update password command
    update_parser = subparsers.add_parser("update-password", help="Update user password")
    update_parser.add_argument("username", help="Username")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize database connection
    try:
        init_db_pool()
    except Exception as e:
        print(f"Error: Failed to connect to database: {e}")
        print("Make sure PostgreSQL is running and environment variables are set correctly.")
        return 1

    try:
        if args.command == "create":
            success = create_user_cli(args.username, args.full_name)
        elif args.command == "update-password":
            success = update_password_cli(args.username)
        else:
            parser.print_help()
            return 1

        return 0 if success else 1

    finally:
        close_db_pool()


if __name__ == "__main__":
    sys.exit(main())
