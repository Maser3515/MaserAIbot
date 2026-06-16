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


def parse_module_callback(data: str) -> int | None:
    if data.startswith("module_"):
        try:
            return int(data.split("_")[1])
        except (ValueError, IndexError):
            return None
    return None


@router.callback_query(lambda c: c.data.startswith("module_"))
async def handle_module(callback: types.CallbackQuery, config: Config) -> None:
    user_id = callback.from_user.id
    number = parse_module_callback(callback.data)
    if not number or number not in content.MODULE_CONTENTS:
        await callback.answer()
        return

    user = await database.get_user(config.db_path, user_id)
    if not user or not user.get("paid_access"):
        await callback.message.answer(content.ACCESS_REQUIRED, reply_markup=keyboards.main_menu_free())
        await callback.answer()
        return

    await database.log_event(config.db_path, user_id, f"module_{number}_open")
    module_info = content.MODULE_CONTENTS[number]
    await callback.message.answer(f"<b>{module_info['title']}</b>\n\n{module_info['text']}")

    pdf_path = BASE_DIR / module_info["file"]
    try:
        if not pdf_path.exists():
            raise FileNotFoundError(str(pdf_path))
        await callback.message.answer_document(FSInputFile(pdf_path))
    except Exception as e:
        log.exception("Failed to send module file")
        await callback.message.answer("Материал временно недоступен. Администратор уже получил уведомление.")
        try:
            await callback.bot.send_message(config.admin_id, f"Ошибка отправки PDF модуля {number}: {e}")
        except Exception:
            pass

    await database.update_user_module(config.db_path, user_id, number)
    await callback.message.answer("Что дальше?", reply_markup=keyboards.module_keyboard(number))
    await callback.answer()


@router.callback_query(lambda c: c.data == "finish_course")
async def finish_course(callback: types.CallbackQuery, config: Config) -> None:
    user_id = callback.from_user.id
    user = await database.get_user(config.db_path, user_id)
    if not user or not user.get("paid_access"):
        await callback.message.answer(content.ACCESS_REQUIRED, reply_markup=keyboards.main_menu_free())
        await callback.answer()
        return
    await database.update_user_module(config.db_path, user_id, 5)
    await database.log_event(config.db_path, user_id, "course_finished")
    await callback.message.answer(content.FINISH_COURSE, reply_markup=keyboards.finish_course_keyboard())
    await callback.answer()
