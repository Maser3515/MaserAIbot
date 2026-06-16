@echo off
REM Запускать из папки bot или двойным кликом по этому файлу.
cd /d "%~dp0.."
python -m bot.main
pause
