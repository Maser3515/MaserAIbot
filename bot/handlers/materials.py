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


@router.callback_query(lambda c: c.data == "my_materials")
async def show_materials(callback: types.CallbackQuery, config: Config) -> None:
    user = await database.get_user(config.db_path, callback.from_user.id)
    if not user or not user.get("paid_access"):
        await callback.message.answer(content.ACCESS_REQUIRED, reply_markup=keyboards.main_menu_free())
        await callback.answer()
        return
    await callback.message.answer("Твои материалы курса 'ChatGPT для работы':", reply_markup=keyboards.materials_keyboard())
    await callback.answer()


async def send_pdf(callback: types.CallbackQuery, config: Config, relative_path: str) -> None:
    path = BASE_DIR / relative_path
    try:
        if not path.exists():
            raise FileNotFoundError(str(path))
        await callback.message.answer_document(FSInputFile(path))
    except Exception as e:
        log.exception("Failed to send pdf")
        await callback.message.answer("Материал временно недоступен. Администратор уже получил уведомление.")
        try:
            await callback.bot.send_message(config.admin_id, f"Ошибка отправки PDF: {e}")
        except Exception:
            pass


@router.callback_query(lambda c: c.data.startswith("pdf_"))
async def handle_material_pdf(callback: types.CallbackQuery, config: Config) -> None:
    user = await database.get_user(config.db_path, callback.from_user.id)
    if not user or not user.get("paid_access"):
        await callback.message.answer(content.ACCESS_REQUIRED, reply_markup=keyboards.main_menu_free())
        await callback.answer()
        return

    mapping = {
        "pdf_full_course": "materials/ChatGPT_dlya_raboty_polny_kurs.pdf",
        "pdf_mod_1": "materials/ChatGPT_dlya_raboty_modul_1.pdf",
        "pdf_mod_2": "materials/ChatGPT_dlya_raboty_modul_2.pdf",
        "pdf_mod_3": "materials/ChatGPT_dlya_raboty_modul_3.pdf",
        "pdf_mod_4": "materials/ChatGPT_dlya_raboty_modul_4.pdf",
        "pdf_mod_5": "materials/ChatGPT_dlya_raboty_modul_5.pdf",
    }

    if callback.data == "pdf_all":
        for rel in mapping.values():
            await send_pdf(callback, config, rel)
    elif callback.data in mapping:
        await send_pdf(callback, config, mapping[callback.data])

    await callback.answer()
