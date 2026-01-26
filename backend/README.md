# Backend Setup

## Prerequisites
- Python 3.8+
- FFmpeg (for audio processing)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg:
- **Windows**: Download from https://ffmpeg.org/download.html
- **Mac**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`

## Running the Backend

```bash
python backend.py
```

The backend will start on http://localhost:5000

## Endpoints

- `POST /analyze_full_video` - Analyze uploaded video
- `GET /health` - Check backend health
