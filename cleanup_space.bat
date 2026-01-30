@echo off
echo ==================================================
echo   MIRO Cleanup Utility
echo ==================================================

echo.
echo [1/3] Deleting __pycache__ folders...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo.
echo [2/3] Deleting Partial/Corrupt Models...
REM Only delete the specific GGUF if it exists to allow re-download
if exist "backend\models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf" (
    echo Found existing GGUF. Deleting to ensure fresh download...
    del "backend\models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
)

echo.
echo [3/3] Cleaning Temp Files...
del /s /q *.pyc
del /s /q backend\debug_*.py
del /s /q backend\validate_*.py

echo.
echo Check your recycle bin and downloads folder manually if you need more space!
echo.
pause
