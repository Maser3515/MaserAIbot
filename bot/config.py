"""Configuration module for the Telegram bot.

This module defines a `Config` dataclass and helper functions to load
environment variables from a `.env` file. All sensitive credentials
and settings should be stored in `.env` and never hard‑coded in the
source code. Use `python-dotenv` to parse the file.

The configuration values control the bot behaviour such as the
Telegram token, admin ID, payment settings and database path. You can
extend this configuration as your project evolves.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os

from dotenv import load_dotenv


@dataclass
class Config:
    """Dataclass holding all configurable values for the bot.

    The values are read from environment variables using `dotenv`.
    If a variable is missing the corresponding attribute will be
    assigned a sensible default (e.g. `None` for optional values or
    predefined numeric/string constants).
    """

    bot_token: str
    admin_id: int

    course_title: str = "ChatGPT для работы"
    course_price: int = 499

    payment_mode: str = "manual_link"
    payment_url: Optional[str] = None
    payment_provider_name: Optional[str] = None
    payment_webhook_secret: Optional[str] = None

    # Yookassa settings
    yookassa_shop_id: Optional[str] = None
    yookassa_secret_key: Optional[str] = None

    db_path: str = "bot.db"


def load_config(env_file: Optional[Path] = None) -> Config:
    """Load configuration from a `.env` file or environment variables.

    Args:
        env_file: Optional path to a specific `.env` file. If not
            provided the default `.env` in the project root will be
            loaded if present.

    Returns:
        Config: Populated configuration dataclass.
    """
    # Locate and load the .env file if it exists
    if env_file is None:
        env_path = Path(__file__).resolve().parent.parent / ".env"
    else:
        env_path = env_file
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    # Required fields
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN is not set in environment")

    admin_id_str = os.getenv("ADMIN_ID")
    if not admin_id_str:
        raise ValueError("ADMIN_ID is not set in environment")
    try:
        admin_id = int(admin_id_str)
    except ValueError:
        raise ValueError("ADMIN_ID must be an integer")

    # Optional fields with defaults
    course_title = os.getenv("COURSE_TITLE", "ChatGPT для работы")
    course_price = int(os.getenv("COURSE_PRICE", "499"))
    payment_mode = os.getenv("PAYMENT_MODE", "manual_link")
    payment_url = os.getenv("PAYMENT_URL")
    payment_provider_name = os.getenv("PAYMENT_PROVIDER_NAME")
    payment_webhook_secret = os.getenv("PAYMENT_WEBHOOK_SECRET")
    yookassa_shop_id = os.getenv("YOOKASSA_SHOP_ID")
    yookassa_secret_key = os.getenv("YOOKASSA_SECRET_KEY")
    db_path = os.getenv("DB_PATH", "bot.db")

    return Config(
        bot_token=bot_token,
        admin_id=admin_id,
        course_title=course_title,
        course_price=course_price,
        payment_mode=payment_mode,
        payment_url=payment_url,
        payment_provider_name=payment_provider_name,
        payment_webhook_secret=payment_webhook_secret,
        yookassa_shop_id=yookassa_shop_id,
        yookassa_secret_key=yookassa_secret_key,
        db_path=db_path,
    )