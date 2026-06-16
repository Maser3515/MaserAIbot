from __future__ import annotations

import logging
from pathlib import Path

from aiogram import Router, types
from aiogram.types import FSInputFile

from ..config import Config
from .. import database, keyboards, content

router = Router()
log = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]


@router.callback_query(lambda c: c.data == "free_lesson")
async def handle_free_lesson(callback: types.CallbackQuery, config: Config) -> None:
    user_id = callback.from_user.id
    await database.log_event(config.db_path, user_id, "free_lesson_click")
    pdf_path = BASE_DIR / "materials" / "ChatGPT_dlya_raboty_besplatny_urok.pdf"

    try:
        if not pdf_path.exists():
            raise FileNotFoundError(str(pdf_path))
        await callback.message.answer_document(FSInputFile(pdf_path))
        await database.log_event(config.db_path, user_id, "free_lesson_sent")
    except Exception as e:
        log.exception("Failed to send free lesson")
        await callback.message.answer("Материал временно недоступен. Администратор уже получил уведомление.")
        try:
            await callback.bot.send_message(config.admin_id, f"Ошибка отправки бесплатного урока: {e}")
        except Exception:
            pass
        await callback.answer()
        return

    await callback.message.answer(content.FREE_LESSON_SENT, reply_markup=keyboards.free_lesson_sent())
    await callback.answer()
