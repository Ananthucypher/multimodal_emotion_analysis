echo ==================================================
echo   MIRO Phase 6: One-Click Setup and Launch
echo ==================================================

cd /d "%~dp0"

echo.
echo [1/3] Installing/Verifying Dependencies...
pip install -r backend/requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error installing dependencies.
    pause
    exit /b
)

echo.
echo [2/3] Downloading Models (GGUF + Whisper)...
echo This may take time on first run (5GB download).
python backend/download_models.py
if %ERRORLEVEL% NEQ 0 (
    echo Error downloading models.
    pause
    exit /b
)

echo.
echo [3/3] Starting Celery Worker (Optimized)...
echo.
echo **************************************************
echo * SUCCESS! The worker is starting.               *
echo * Keep this window open.                         *
echo * Return to your browser and click "Analyze"!    *
echo **************************************************
echo.

cd backend
python -m celery -A celery_config.celery_app worker --pool=solo --loglevel=info

pause
