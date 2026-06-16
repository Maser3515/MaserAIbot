"""Keyboard definitions for the Telegram bot.

This module centralises all inline and reply keyboard markups used in
the bot. Keeping keyboards in one place makes it easier to manage
button labels and callback data. Each function returns a specific
keyboard markup ready to be sent with a message.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ---------- Main menu keyboards ----------

def main_menu_free() -> InlineKeyboardMarkup:
    """Keyboard for the main menu shown to users without paid access."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Получить бесплатный урок", callback_data="free_lesson")],
            [InlineKeyboardButton(text="Что внутри курса", callback_data="course_info")],
            [InlineKeyboardButton(text="Купить курс за 499 ₽", callback_data="buy_course")],
            [InlineKeyboardButton(text="Поддержка", callback_data="support")],
        ]
    )


def main_menu_paid() -> InlineKeyboardMarkup:
    """Keyboard for the main menu shown to users with paid access."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Продолжить обучение", callback_data="continue_course")],
            [InlineKeyboardButton(text="Мои материалы", callback_data="my_materials")],
            [InlineKeyboardButton(text="Оставить отзыв", callback_data="review")],
            [InlineKeyboardButton(text="Поддержка", callback_data="support")],
        ]
    )


# ---------- Free lesson keyboards ----------

def free_lesson_sent() -> InlineKeyboardMarkup:
    """Keyboard shown after sending the free lesson."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Купить курс за 499 ₽", callback_data="buy_course")],
            [InlineKeyboardButton(text="Посмотреть программу", callback_data="course_info")],
            [InlineKeyboardButton(text="Назад в меню", callback_data="back_main")],
        ]
    )


# ---------- Course info keyboards ----------

def course_info_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for the course description screen."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Купить курс за 499 ₽", callback_data="buy_course")],
            [InlineKeyboardButton(text="Получить бесплатный урок", callback_data="free_lesson")],
            [InlineKeyboardButton(text="Назад", callback_data="back_main")],
        ]
    )


# ---------- Purchase keyboards ----------

def purchase_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown on the purchase page."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти к оплате", callback_data="pay")],
            [InlineKeyboardButton(text="Посмотреть программу", callback_data="course_info")],
            [InlineKeyboardButton(text="Поддержка", callback_data="support")],
            [InlineKeyboardButton(text="Назад", callback_data="back_main")],
        ]
    )


def payment_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for confirming manual payment."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Я оплатил", callback_data="payment_sent")],
            [InlineKeyboardButton(text="Назад", callback_data="back_main")],
        ]
    )


def yookassa_payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """Keyboard with direct link to Yookassa payment page."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить сейчас", url=payment_url)],
            [InlineKeyboardButton(text="Назад", callback_data="back_main")],
        ]
    )


# ---------- Modules keyboards ----------

def module_keyboard(current: int) -> InlineKeyboardMarkup:
    """Generate a keyboard for a given module number (1‑5).

    Args:
        current: The module number being shown.
    """
    buttons = []
    if current < 5:
        buttons.append([InlineKeyboardButton(text=f"Перейти к Модулю {current + 1}", callback_data=f"module_{current + 1}")])
    else:
        buttons.append([InlineKeyboardButton(text="Завершить обучение", callback_data="finish_course")])
    # Common navigation buttons
    buttons.append([InlineKeyboardButton(text="Мои материалы", callback_data="my_materials")])
    buttons.append([InlineKeyboardButton(text="Главное меню", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ---------- Materials keyboard ----------

def materials_keyboard() -> InlineKeyboardMarkup:
    """Keyboard listing available PDFs and modules for paid users."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Полный курс PDF", callback_data="pdf_full_course")],
            [InlineKeyboardButton(text="Модуль 1 PDF", callback_data="pdf_mod_1"), InlineKeyboardButton(text="Модуль 1", callback_data="module_1")],
            [InlineKeyboardButton(text="Модуль 2 PDF", callback_data="pdf_mod_2"), InlineKeyboardButton(text="Модуль 2", callback_data="module_2")],
            [InlineKeyboardButton(text="Модуль 3 PDF", callback_data="pdf_mod_3"), InlineKeyboardButton(text="Модуль 3", callback_data="module_3")],
            [InlineKeyboardButton(text="Модуль 4 PDF", callback_data="pdf_mod_4"), InlineKeyboardButton(text="Модуль 4", callback_data="module_4")],
            [InlineKeyboardButton(text="Модуль 5 PDF", callback_data="pdf_mod_5"), InlineKeyboardButton(text="Модуль 5", callback_data="module_5")],
            [InlineKeyboardButton(text="Главное меню", callback_data="back_main")],
        ]
    )


# ---------- Review keyboard ----------

def finish_course_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown after finishing all modules."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оставить отзыв", callback_data="review")],
            [InlineKeyboardButton(text="Получить все PDF", callback_data="pdf_all")],
            [InlineKeyboardButton(text="Мои материалы", callback_data="my_materials")],
            [InlineKeyboardButton(text="Главное меню", callback_data="back_main")],
        ]
    )


# ---------- Support keyboard ----------

def support_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for support prompt."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_main")],
        ]
    )