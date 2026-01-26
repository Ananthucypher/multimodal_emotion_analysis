@echo off
echo 🚀 Starting MIRO Multimodal Emotion Analysis...
echo ==============================================

echo 📦 Starting Backend Server...
start "MIRO Backend" cmd /k "cd backend && python backend.py"

echo 🎨 Starting Frontend Server...
start "MIRO Frontend" cmd /k "cd frontend && npm start"

echo.
echo ✅ Services started in separate windows!
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000 (or next available port)
