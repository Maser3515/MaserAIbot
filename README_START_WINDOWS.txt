БЫСТРЫЙ ЗАПУСК НА WINDOWS

1. Открой CMD.

2. Перейди в корень проекта, не в папку bot:
cd /d "C:\Users\Вова Марадона\Downloads\ChatGPT_dlya_raboty_bot"

3. Создай виртуальное окружение:
python -m venv venv

Если команда не сработала, попробуй:
py -m venv venv

4. Активируй окружение в CMD:
venv\Scripts\activate

Важно: команда source venv/bin/activate работает только в Linux/Mac, в Windows CMD она не работает.

5. Установи зависимости:
python -m pip install -r bot\requirements.txt

6. Создай .env в корне проекта:
copy .env.example .env
notepad .env

7. Заполни BOT_TOKEN и ADMIN_ID.

8. Запускай бота из корня проекта:
python -m bot.main

Не запускай так:
python bot/main.py

Потому что в проекте используются относительные импорты, и его нужно запускать как модуль.
