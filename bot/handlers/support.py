from __future__ import annotations

import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter

from ..config import Config
from .. import database, keyboards, content

router = Router()
log = logging.getLogger(__name__)


class SupportStates(StatesGroup):
    waiting_for_message = State()


@router.callback_query(lambda c: c.data == "support")
async def support_start(callback: types.CallbackQuery, config: Config, state: FSMContext) -> None:
    await database.log_event(config.db_path, callback.from_user.id, "support_open")
    await callback.message.answer(content.SUPPORT_PROMPT, reply_markup=keyboards.support_keyboard())
    await state.set_state(SupportStates.waiting_for_message)
    await callback.answer()


@router.message(StateFilter(SupportStates.waiting_for_message))
async def process_support_message(message: types.Message, config: Config, state: FSMContext) -> None:
    user_id = message.from_user.id
    text = message.text or message.caption or ""
    file_id = None
    kind = None
    if message.photo:
        file_id = message.photo[-1].file_id
        kind = "photo"
    elif message.document:
        file_id = message.document.file_id
        kind = "document"

    await database.add_support_message(config.db_path, user_id, text, file_id)
    await database.log_event(config.db_path, user_id, "support_message")

    caption = (
        "Новое сообщение в поддержку.\n\n"
        f"User ID: {user_id}\n"
        f"Username: @{message.from_user.username or 'нет'}\n"
        f"Name: {message.from_user.full_name}\n\n"
        f"Сообщение:\n{text}"
    )
    try:
        if kind == "photo" and file_id:
            await message.bot.send_photo(config.admin_id, file_id, caption=caption)
        elif kind == "document" and file_id:
            await message.bot.send_document(config.admin_id, file_id, caption=caption)
        else:
            await message.bot.send_message(config.admin_id, caption)
    except Exception:
        log.exception("Failed to send support message to admin")

    await message.answer("Спасибо! Ваш вопрос отправлен администратору.")
    await state.clear()
