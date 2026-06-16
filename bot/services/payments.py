"""Yookassa payment service with status polling."""

import logging
import asyncio
from typing import Dict

from yookassa import Configuration, Payment

log = logging.getLogger(__name__)


def configure_yookassa(shop_id: str, secret_key: str) -> None:
    Configuration.configure(shop_id, secret_key)


async def create_yookassa_payment(
    amount: int,
    description: str,
    user_id: int,
    return_url: str
) -> Dict:
    try:
        payment = Payment.create({
            "amount": {"value": f"{amount}.00", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "capture": True,
            "description": description[:128],
            "metadata": {"user_id": str(user_id), "source": "telegram_bot"}
        })

        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status
        }
    except Exception as e:
        log.exception("Failed to create Yookassa payment")
        raise


async def check_payment_status(payment_id: str, db_path: str, user_id: int) -> bool:
    """Проверяет статус платежа и выдаёт доступ"""
    try:
        payment = Payment.find_one(payment_id)
        if payment.status == "succeeded":
            from ..database import update_user_access
            await update_user_access(db_path, user_id, paid=True)
            log.info(f"✅ Доступ автоматически выдан пользователю {user_id}")
            return True
    except Exception as e:
        log.exception(f"Error checking payment {payment_id}")
    return False