from aiogram import Router, types, F
import logging
import asyncio

from .. import database, keyboards
from ..config import Config
from ..services.payments import create_yookassa_payment, configure_yookassa, check_payment_status

log = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "pay")
async def handle_pay(callback: types.CallbackQuery, config: Config) -> None:
    user_id = callback.from_user.id
    
    user = await database.get_user(config.db_path, user_id)
    if user and user.get("paid_access") == 1:
        await callback.message.answer("✅ У тебя уже есть полный доступ!", 
                                     reply_markup=keyboards.main_menu_paid())
        await callback.answer()
        return

    await database.log_event(config.db_path, user_id, "payment_started")

    if config.payment_mode == "yookassa" and config.yookassa_shop_id and config.yookassa_secret_key:
        try:
            configure_yookassa(config.yookassa_shop_id, config.yookassa_secret_key)
            
            bot_me = await callback.bot.get_me()
            return_url = f"https://t.me/{bot_me.username}"

            payment_data = await create_yookassa_payment(
                amount=config.course_price,
                description=f"Курс ChatGPT для работы - User {user_id}",
                user_id=user_id,
                return_url=return_url
            )

            text = (
                f"💳 <b>Оплата курса</b>\n\n"
                f"📘 {config.course_title}\n"
                f"💰 Сумма: <b>{config.course_price} ₽</b>\n\n"
                "Нажмите кнопку ниже для оплаты:"
            )

            await callback.message.answer(
                text,
                reply_markup=keyboards.yookassa_payment_keyboard(payment_data["confirmation_url"]),
                parse_mode="HTML"
            )

            asyncio.create_task(monitor_payment(payment_data["payment_id"], config.db_path, user_id, callback.bot))

            log.info(f"Платёж создан для {user_id} | ID: {payment_data['payment_id']}")

        except Exception as e:
            log.exception("Yookassa error")
            await callback.message.answer("❌ Ошибка создания платежа.")
    else:
        await callback.message.answer("Ручной режим...")

    await callback.answer()


async def monitor_payment(payment_id: str, db_path: str, user_id: int, bot, max_attempts: int = 36):
    """Мониторинг + отправка сообщения после успеха"""
    for attempt in range(max_attempts):
        await asyncio.sleep(10)
        success = await check_payment_status(payment_id, db_path, user_id)
        if success:
            try:
                await bot.send_message(
                    user_id,
                    "🎉 <b>Оплата прошла успешно!</b>\n\n"
                    "Доступ к полному курсу открыт!\n"
                    "Теперь ты можешь изучать все модули.",
                    parse_mode="HTML",
                    reply_markup=keyboards.main_menu_paid()
                )
                log.info(f"Сообщение об успешной оплате отправлено пользователю {user_id}")
            except Exception as e:
                log.error(f"Не удалось отправить сообщение: {e}")
            return
    log.warning(f"Мониторинг платежа {payment_id} завершён")