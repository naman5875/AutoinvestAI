@echo off
title AutoInvest Celery Worker
echo ===================================================
echo  AutoInvest AI — Starting Celery Background Worker
echo ===================================================

:: 1. Change directory to the backend folder automatically
cd /d "D:\autoinvest_project\autoinvest_backend"

:: 2. Activate the correct virtual environment automatically
call .venv\Scripts\activate

:: 3. Set your Gemini API keys automatically (Replace the placeholder below)
set GEMINI_API_KEY=" "
set GOOGLE_API_KEY=" "

:: 4. Start Celery with the Windows solo pool automatically
celery -A autoinvest_backend worker --loglevel=info -P solo

pause
