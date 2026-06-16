from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject

from ..config import Config
from .. import database, keyboards, content

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject, config: Config) -> None:
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    source = command.args if command and command.args else None

    await database.create_user(config.db_path, user_id, username, first_name, source)
    await database.log_event(config.db_path, user_id, "start", source or "")

    user = await database.get_user(config.db_path, user_id)
    keyboard = keyboards.main_menu_paid() if user and user.get("paid_access") else keyboards.main_menu_free()
    await message.answer(content.welcome(first_name), reply_markup=keyboard)
