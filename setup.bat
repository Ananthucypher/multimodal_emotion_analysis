@echo off
echo 🎭 Multimodal Emotion Analysis - Setup Script
echo ==============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 14+ first.
    pause
    exit /b 1
)

echo ✅ Python found
echo ✅ Node.js found
echo.

REM Backend setup
echo 📦 Setting up Backend...
cd backend
python -m pip install -r requirements.txt
echo ✅ Backend dependencies installed
cd ..
echo.

REM Frontend setup
echo 📦 Setting up Frontend...
cd frontend
call npm install
echo ✅ Frontend dependencies installed
cd ..
echo.

echo 🎉 Setup complete!
echo.
echo To run the application:
echo 1. Terminal 1 - Backend:  cd backend ^&^& python backend.py
echo 2. Terminal 2 - Frontend: cd frontend ^&^& npm start
echo.
echo 📝 Note: Make sure FFmpeg is installed for audio processing
pause
