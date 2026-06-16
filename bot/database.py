"""Database management for the Telegram bot.

This module provides asynchronous functions for interacting with the
SQLite database using `aiosqlite`. It creates required tables on
startup and exposes helper functions for common operations such as
registering users, recording payments, saving reviews, logging
events and retrieving information for analytics or admin features.

All interactions are performed via parameterised SQL queries to
prevent SQL injection. Make sure to call :func:`init_db` before using
other functions to ensure the database schema is created.
"""

from __future__ import annotations

import aiosqlite
import datetime
from typing import Any, Dict, Optional, List


# ---------- Schema creation ----------
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    registered_at TEXT,
    source TEXT,
    paid_access INTEGER DEFAULT 0,
    paid_at TEXT,
    current_module INTEGER DEFAULT 0,
    last_activity_at TEXT
);
"""

CREATE_PAYMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    order_id TEXT,
    status TEXT,
    amount INTEGER,
    provider TEXT,
    proof_type TEXT,
    proof_text TEXT,
    proof_file_id TEXT,
    created_at TEXT,
    confirmed_at TEXT
);
"""

CREATE_REVIEWS_TABLE = """
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    review_text TEXT,
    photo_file_id TEXT,
    created_at TEXT
);
"""

CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_name TEXT NOT NULL,
    event_data TEXT,
    created_at TEXT
);
"""

CREATE_SUPPORT_TABLE = """
CREATE TABLE IF NOT EXISTS support_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message_text TEXT,
    file_id TEXT,
    created_at TEXT
);
"""


async def init_db(db_path: str) -> None:
    """Initialise the SQLite database and create tables if missing.

    Args:
        db_path: Path to the SQLite database file.
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_USERS_TABLE)
        await db.execute(CREATE_PAYMENTS_TABLE)
        await db.execute(CREATE_REVIEWS_TABLE)
        await db.execute(CREATE_EVENTS_TABLE)
        await db.execute(CREATE_SUPPORT_TABLE)
        await db.commit()


# ---------- User operations ----------

async def create_user(db_path: str, user_id: int, username: Optional[str], first_name: Optional[str], source: Optional[str]) -> None:
    """Insert a new user into the database.

    If the user already exists this function does nothing. The
    registration date and last activity are set to current time.
    """
    now = datetime.datetime.utcnow().isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, registered_at, source, last_activity_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, first_name, now, source, now),
        )
        await db.commit()


async def get_user(db_path: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a user record by Telegram user_id."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_user_access(db_path: str, user_id: int, paid: bool) -> None:
    """Grant or revoke paid access to a user."""
    now = datetime.datetime.utcnow().isoformat() if paid else None
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE users SET paid_access = ?, paid_at = ? WHERE user_id = ?",
            (1 if paid else 0, now, user_id),
        )
        await db.commit()


async def update_user_module(db_path: str, user_id: int, module_number: int) -> None:
    """Update the current module a user is on."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE users SET current_module = ?, last_activity_at = ? WHERE user_id = ?",
            (module_number, datetime.datetime.utcnow().isoformat(), user_id),
        )
        await db.commit()


# ---------- Event logging ----------

async def log_event(db_path: str, user_id: int, event_name: str, event_data: Optional[str] = None) -> None:
    """Log a custom event for analytics purposes."""
    now = datetime.datetime.utcnow().isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO events (user_id, event_name, event_data, created_at) VALUES (?, ?, ?, ?)",
            (user_id, event_name, event_data, now),
        )
        await db.commit()


# ---------- Payment operations ----------

async def create_payment(db_path: str, user_id: int, amount: int, provider: Optional[str], order_id: Optional[str] = None) -> int:
    """Insert a new payment record and return its row ID."""
    now = datetime.datetime.utcnow().isoformat()
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "INSERT INTO payments (user_id, order_id, status, amount, provider, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, order_id, "pending", amount, provider, now),
        )
        await db.commit()
        return cursor.lastrowid


async def update_payment_status(db_path: str, payment_id: int, status: str, proof_type: Optional[str] = None, proof_text: Optional[str] = None, proof_file_id: Optional[str] = None) -> None:
    """Update the status and proof details of a payment."""
    now = datetime.datetime.utcnow().isoformat() if status == "confirmed" else None
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE payments SET status = ?, proof_type = ?, proof_text = ?, proof_file_id = ?, confirmed_at = ? WHERE id = ?",
            (status, proof_type, proof_text, proof_file_id, now, payment_id),
        )
        await db.commit()


# ---------- Review operations ----------

async def add_review(db_path: str, user_id: int, review_text: str, photo_file_id: Optional[str] = None) -> None:
    """Save a user review."""
    now = datetime.datetime.utcnow().isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO reviews (user_id, review_text, photo_file_id, created_at) VALUES (?, ?, ?, ?)",
            (user_id, review_text, photo_file_id, now),
        )
        await db.commit()


# ---------- Support operations ----------

async def add_support_message(db_path: str, user_id: int, message_text: str, file_id: Optional[str] = None) -> None:
    """Store a support message from a user."""
    now = datetime.datetime.utcnow().isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO support_messages (user_id, message_text, file_id, created_at) VALUES (?, ?, ?, ?)",
            (user_id, message_text, file_id, now),
        )
        await db.commit()