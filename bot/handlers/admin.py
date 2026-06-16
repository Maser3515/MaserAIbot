from __future__ import annotations

import csv
import logging
from pathlib import Path

import aiosqlite
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile

from ..config import Config
from .. import database, content, keyboards

router = Router()
log = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent
EXPORTS_DIR = BASE_DIR / "exports"


def is_admin(message: types.Message, config: Config) -> bool:
    return message.from_user and message.from_user.id == config.admin_id


@router.message(Command("admin"))
async def admin_menu(message: types.Message, config: Config) -> None:
    if not is_admin(message, config):
        return
    await message.answer(
        "Админ-меню:\n"
        "/stats - статистика\n"
        "/buyers - список покупателей\n"
        "/user USER_ID - информация о пользователе\n"
        "/add_access USER_ID - выдать доступ\n"
        "/remove_access USER_ID - убрать доступ\n"
        "/deny_payment USER_ID - отклонить заявку на оплату\n"
        "/broadcast текст - рассылка всем\n"
        "/broadcast_buyers текст - рассылка покупателям\n"
        "/reviews - последние отзывы\n"
        "/export_users - экспорт пользователей в CSV\n"
        "/export_buyers - экспорт покупателей в CSV"
    )


async def count_event(db, name: str) -> int:
    cursor = await db.execute("SELECT COUNT(*) FROM events WHERE event_name = ?", (name,))
    return (await cursor.fetchone())[0]


@router.message(Command("stats"))
async def show_stats(message: types.Message, config: Config) -> None:
    if not is_admin(message, config):
        return
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE paid_access = 1")
        buyers = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM payments")
        payment_requests = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM reviews")
        reviews_count = (await cursor.fetchone())[0]
        free_lessons = await count_event(db, "free_lesson_sent")
        buy_clicks = await count_event(db, "buy_click")
        payment_checks = await count_event(db, "payment_check_request")
    conversion = (buyers / total_users * 100) if total_users else 0
    await message.answer(
        f"Всего пользователей: {total_users}\n"
        f"Покупателей: {buyers}\n"
        f"Конверсия в покупку: {conversion:.1f}%\n"
        f"Получили бесплатный урок: {free_lessons}\n"
        f"Нажали кнопку оплаты: {buy_clicks}\n"
        f"Заявок на проверку оплаты: {payment_checks}\n"
        f"Всего платежных записей: {payment_requests}\n"
        f"Отзывов: {reviews_count}"
    )


@router.message(Command("buyers"))
async def list_buyers(message: types.Message, config: Config) -> None:
    if not is_admin(message, config):
        return
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT user_id, username, first_name, paid_at FROM users WHERE paid_access = 1 ORDER BY paid_at DESC")
        rows = await cursor.fetchall()
    if not rows:
        await message.answer("Пока покупателей нет.")
        return
    lines = ["Покупатели:"]
    for r in rows:
        lines.append(f"{r['user_id']} | @{r['username'] or 'нет'} | {r['first_name'] or ''} | {r['paid_at'] or ''}")
    await message.answer("\n".join(lines))


@router.message(Command("user"))
async def user_info(message: types.Message, command: CommandObject, config: Config) -> None:
    if not is_admin(message, config):
        return
    if not command.args:
        await message.answer("Укажите USER_ID")
        return
    try:
        target_id = int(command.args.strip())
    except ValueError:
        await message.answer("USER_ID должен быть числом")
        return
    user = await database.get_user(config.db_path, target_id)
    if not user:
        await message.answer("Пользователь не найден")
        return
    await message.answer(
        f"user_id: {user['user_id']}\n"
        f"username: @{user['username'] or 'нет'}\n"
        f"first_name: {user['first_name'] or ''}\n"
        f"дата регистрации: {user['registered_at']}\n"
        f"источник: {user['source'] or 'нет'}\n"
        f"оплатил: {'да' if user['paid_access'] else 'нет'}\n"
        f"дата оплаты: {user['paid_at'] or 'нет'}\n"
        f"текущий модуль: {user['current_module']}"
    )


@router.message(Command("add_access"))
async def grant_access(message: types.Message, command: CommandObject, config: Config) -> None:
    if not is_admin(message, config):
        return
    if not command.args:
        await message.answer("Укажите USER_ID")
        return
    try:
        user_id = int(command.args.strip())
    except ValueError:
        await message.answer("USER_ID должен быть числом")
        return
    await database.update_user_access(config.db_path, user_id, True)
    await database.log_event(config.db_path, user_id, "access_granted")
    try:
        await message.bot.send_message(user_id, content.ACCESS_GRANTED, reply_markup=keyboards.module_keyboard(0))
    except Exception:
        log.exception("Failed to notify user about access")
    await message.answer(f"Пользователю {user_id} выдан доступ")


@router.message(Command("remove_access"))
async def revoke_access(message: types.Message, command: CommandObject, config: Config) -> None:
    if not is_admin(message, config):
        return
    if not command.args:
        await message.answer("Укажите USER_ID")
        return
    try:
        user_id = int(command.args.strip())
    except ValueError:
        await message.answer("USER_ID должен быть числом")
        return
    await database.update_user_access(config.db_path, user_id, False)
    await message.answer(f"Доступ для пользователя {user_id} удалён")


@router.message(Command("deny_payment"))
async def deny_payment(message: types.Message, command: CommandObject, config: Config) -> None:
    if not is_admin(message, config):
        return
    if not command.args:
        await message.answer("Укажите USER_ID")
        return
    try:
        user_id = int(command.args.strip())
        await message.bot.send_message(user_id, "Оплата не подтверждена. Если это ошибка, напишите в поддержку.")
    except Exception:
        pass
    await message.answer("Заявка отклонена")


@router.message(Command("broadcast"))
async def broadcast(message: types.Message, command: CommandObject, config: Config) -> None:
    if not is_admin(message, config):
        return
    if not command.args:
        await message.answer("Укажите текст рассылки")
        return
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        recipients = [r[0] for r in await cursor.fetchall()]
    sent = 0
    for uid in recipients:
        try:
            await message.bot.send_message(uid, command.args)
            sent += 1
        except Exception:
            pass
    await message.answer(f"Рассылка отправлена. Успешно: {sent}")


@router.message(Command("broadcast_buyers"))
async def broadcast_buyers(message: types.Message, command: CommandObject, config: Config) -> None:
    if not is_admin(message, config):
        return
    if not command.args:
        await message.answer("Укажите текст рассылки")
        return
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE paid_access = 1")
        recipients = [r[0] for r in await cursor.fetchall()]
    sent = 0
    for uid in recipients:
        try:
            await message.bot.send_message(uid, command.args)
            sent += 1
        except Exception:
            pass
    await message.answer(f"Рассылка покупателям отправлена. Успешно: {sent}")


@router.message(Command("reviews"))
async def list_reviews(message: types.Message, config: Config) -> None:
    if not is_admin(message, config):
        return
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT user_id, review_text, created_at FROM reviews ORDER BY created_at DESC LIMIT 10")
        rows = await cursor.fetchall()
    if not rows:
        await message.answer("Отзывов пока нет.")
        return
    lines = ["Последние отзывы:"]
    for r in rows:
        lines.append(f"{r['created_at']}: {r['user_id']} - {r['review_text']}")
    await message.answer("\n".join(lines))


async def export_query(config: Config, filename: str, headers: list[str], query: str) -> Path:
    EXPORTS_DIR.mkdir(exist_ok=True)
    path = EXPORTS_DIR / filename
    async with aiosqlite.connect(config.db_path) as db:
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)
    return path


@router.message(Command("export_users"))
async def export_users(message: types.Message, config: Config) -> None:
    if not is_admin(message, config):
        return
    path = await export_query(
        config,
        "users.csv",
        ["user_id", "username", "first_name", "registered_at", "source", "paid_access", "paid_at", "current_module"],
        "SELECT user_id, username, first_name, registered_at, source, paid_access, paid_at, current_module FROM users",
    )
    await message.answer_document(FSInputFile(path), caption="Экспорт пользователей")


@router.message(Command("export_buyers"))
async def export_buyers(message: types.Message, config: Config) -> None:
    if not is_admin(message, config):
        return
    path = await export_query(
        config,
        "buyers.csv",
        ["user_id", "username", "first_name", "paid_at"],
        "SELECT user_id, username, first_name, paid_at FROM users WHERE paid_access = 1",
    )
    await message.answer_document(FSInputFile(path), caption="Экспорт покупателей")
