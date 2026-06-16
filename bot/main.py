from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import load_config
from .database import init_db
from .handlers import start, free_lesson, course, payment, modules, materials, reviews, support, admin


def setup_logging() -> None:
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler()],
    )


async def main() -> None:
    setup_logging()
    config = load_config()
    await init_db(config.db_path)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage(), config=config)

    dp.include_router(start.router)
    dp.include_router(free_lesson.router)
    dp.include_router(course.router)
    dp.include_router(payment.router)
    dp.include_router(modules.router)
    dp.include_router(materials.router)
    dp.include_router(reviews.router)
    dp.include_router(support.router)
    dp.include_router(admin.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())