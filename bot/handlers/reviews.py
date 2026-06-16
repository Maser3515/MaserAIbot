from __future__ import annotations

import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ..config import Config
from .. import database, content

router = Router()
log = logging.getLogger(__name__)


class ReviewStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()


@router.callback_query(lambda c: c.data == "review")
async def start_review(callback: types.CallbackQuery, config: Config, state: FSMContext) -> None:
    user_id = callback.from_user.id
    await database.log_event(config.db_path, user_id, "review_started")
    await callback.message.answer(content.REVIEW_PROMPT)
    await state.set_state(ReviewStates.waiting_for_text)
    await callback.answer()


@router.message(StateFilter(ReviewStates.waiting_for_text))
async def collect_review_text(message: types.Message, config: Config, state: FSMContext) -> None:
    review_text = message.text or message.caption or ""
    if not review_text.strip():
        await message.answer("Пришли отзыв текстом одним сообщением.")
        return
    await state.update_data(review_text=review_text)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Пропустить", callback_data="review_skip_photo")]])
    await message.answer("Спасибо! Хочешь прикрепить фото? Пришли фото или нажми 'Пропустить'.", reply_markup=kb)
    await state.set_state(ReviewStates.waiting_for_photo)


@router.callback_query(StateFilter(ReviewStates.waiting_for_photo), lambda c: c.data == "review_skip_photo")
async def skip_review_photo(callback: types.CallbackQuery, config: Config, state: FSMContext) -> None:
    data = await state.get_data()
    review_text = data.get("review_text", "")
    user_id = callback.from_user.id
    await database.add_review(config.db_path, user_id, review_text, photo_file_id=None)
    await database.log_event(config.db_path, user_id, "review_sent")
    try:
        await callback.bot.send_message(config.admin_id, f"Новый отзыв от @{callback.from_user.username or 'нет'} ({user_id})\n\n{review_text}")
    except Exception:
        log.exception("Failed to send review to admin")
    await callback.message.answer("Спасибо за отзыв! Он сохранён и отправлен администратору.")
    await state.clear()
    await callback.answer()


@router.message(StateFilter(ReviewStates.waiting_for_photo))
async def collect_review_photo(message: types.Message, config: Config, state: FSMContext) -> None:
    data = await state.get_data()
    review_text = data.get("review_text", "")
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id if message.photo else None
    await database.add_review(config.db_path, user_id, review_text, photo_file_id=photo_id)
    await database.log_event(config.db_path, user_id, "review_sent")
    caption = f"Новый отзыв от @{message.from_user.username or 'нет'} ({user_id})\n\n{review_text}"
    try:
        if photo_id:
            await message.bot.send_photo(config.admin_id, photo_id, caption=caption)
        else:
            await message.bot.send_message(config.admin_id, caption)
    except Exception:
        log.exception("Failed to send review to admin")
    await message.answer("Спасибо за отзыв! Он сохранён и отправлен администратору.")
    await state.clear()
