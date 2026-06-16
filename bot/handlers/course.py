from __future__ import annotations

from aiogram import Router, types

from ..config import Config
from .. import database, keyboards, content

router = Router()


@router.callback_query(lambda c: c.data == "course_info")
async def show_course_info(callback: types.CallbackQuery, config: Config) -> None:
    await database.log_event(config.db_path, callback.from_user.id, "course_info_open")
    await callback.message.answer(content.COURSE_INFO, reply_markup=keyboards.course_info_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "buy_course")
async def show_sales_message(callback: types.CallbackQuery, config: Config) -> None:
    await database.log_event(config.db_path, callback.from_user.id, "buy_click")
    await callback.message.answer(content.SALES_MESSAGE, reply_markup=keyboards.purchase_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_main")
async def back_main(callback: types.CallbackQuery, config: Config) -> None:
    user = await database.get_user(config.db_path, callback.from_user.id)
    kb = keyboards.main_menu_paid() if user and user.get("paid_access") else keyboards.main_menu_free()
    await callback.message.answer("Главное меню:", reply_markup=kb)
    await callback.answer()


@router.callback_query(lambda c: c.data == "continue_course")
async def continue_course(callback: types.CallbackQuery, config: Config) -> None:
    user = await database.get_user(config.db_path, callback.from_user.id)
    if not user or not user.get("paid_access"):
        await callback.message.answer(content.ACCESS_REQUIRED, reply_markup=keyboards.main_menu_free())
        await callback.answer()
        return
    current = int(user.get("current_module") or 0)
    next_module = min(max(current + 1, 1), 5)
    await callback.message.answer(f"Продолжим с Модуля {next_module}.", reply_markup=keyboards.module_keyboard(next_module - 1))
    await callback.answer()
