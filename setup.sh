#!/bin/bash

echo "🎭 Multimodal Emotion Analysis - Setup Script"
echo "=============================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Python3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null
then
    echo "❌ Node.js is not installed. Please install Node.js 14+ first."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo "✅ Node.js found: $(node --version)"
echo ""

# Backend setup
echo "📦 Setting up Backend..."
cd backend
python3 -m pip install -r requirements.txt
echo "✅ Backend dependencies installed"
cd ..
echo ""

# Frontend setup
echo "📦 Setting up Frontend..."
cd frontend
npm install
echo "✅ Frontend dependencies installed"
cd ..
echo ""

echo "🎉 Setup complete!"
echo ""
echo "To run the application:"
echo "1. Terminal 1 - Backend:  cd backend && python backend.py"
echo "2. Terminal 2 - Frontend: cd frontend && npm start"
echo ""
echo "📝 Note: Make sure FFmpeg is installed for audio processing"
