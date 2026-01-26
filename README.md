# 🎭 Multimodal Emotion Analysis System

A comprehensive AI-powered emotion analysis system that processes video files to detect emotions through:
- 😊 **Face Emotion Detection** - DeepFace powered facial expression analysis
- 🎵 **Audio Tone Analysis** - Librosa-based audio emotion detection
- 💬 **Speech Transcription** - Google Speech Recognition
- 💭 **Sentiment Analysis** - Text-based sentiment from transcripts

## ✨ Features

- **Modern, Aesthetic UI** - Beautiful gradient design with smooth animations
- **Multimodal Analysis** - Combines face, audio, and speech data
- **Real-time Processing** - Fast emotion detection and analysis
- **Visual Analytics** - Color-coded emotion breakdowns and confidence scores
- **Responsive Design** - Works on desktop, tablet, and mobile

## 🏗️ Project Structure

```
multimodal_emotion_analysis/
├── backend/
│   ├── backend.py           # Flask API server
│   ├── requirements.txt     # Python dependencies
│   └── README.md
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js          # Main React component
│   │   ├── App.css         # Styles
│   │   ├── index.js
│   │   └── index.css
│   ├── package.json
│   └── README.md
└── README.md
```

## 🚀 Quick Start

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg (required for audio processing):
   - **Windows**: Download from https://ffmpeg.org/download.html
   - **Mac**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg`

4. Run the Flask server:
```bash
python backend.py
```

Backend will start on `http://localhost:5000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install Node dependencies:
```bash
npm install
```

3. Start the React app:
```bash
npm start
```

Frontend will open at `http://localhost:3000`

## 📖 Usage

1. **Upload Video**: Click "Choose Video File" and select an MP4, AVI, or MOV file
2. **Analyze**: Click "Analyze Emotions" button
3. **View Results**: See comprehensive emotion analysis across all modalities

### Tips for Best Results

- Use videos with **clear, audible speech** for transcript and sentiment analysis
- Ensure videos have **visible faces** for face emotion detection
- Videos with **good audio quality** provide better tone analysis
- Supported formats: MP4, AVI, MOV, WEBM

## 🛠️ Technologies Used

### Backend
- **Flask** - Web framework
- **DeepFace** - Face emotion recognition
- **OpenCV** - Video processing
- **Librosa** - Audio feature extraction
- **SpeechRecognition** - Speech-to-text
- **Pydub** - Audio manipulation

### Frontend
- **React** - UI framework
- **Axios** - HTTP client
- **CSS3** - Modern styling with gradients and animations

## 📊 API Endpoints

### POST `/analyze_full_video`
Analyzes uploaded video for emotions across all modalities.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `video` file

**Response:**
```json
{
  "face_emotion_result": {
    "dominant_face_emotion": "happy",
    "total_frames": 187,
    "analyzed_frames": 37,
    "frame_emotions": {...}
  },
  "audio_tone_emotion": {
    "predicted": "neutral",
    "probs": {...}
  },
  "transcript": "Hello, this is a test",
  "transcript_sentiment": {
    "primary_emotion": "happy",
    "score": 0.95,
    "description": "Positive sentiment detected"
  }
}
```

### GET `/health`
Health check endpoint.

## 🎨 UI Features

- **Gradient Backgrounds** - Eye-catching animated gradients
- **Emotion Color Coding** - Each emotion has a unique color
- **Progress Bars** - Visual representation of emotion distributions
- **Confidence Scores** - Percentage-based accuracy metrics
- **Responsive Cards** - Clean, organized result presentation
- **Loading States** - Smooth loading animations

## 🔧 Troubleshooting

### No Speech Detected
- Ensure video has clear audio track
- Check that FFmpeg is properly installed
- Try videos with louder, clearer speech

### Face Detection Issues
- Make sure faces are clearly visible
- Good lighting improves detection
- Frontal face views work best

### Installation Issues
- For TensorFlow errors: Ensure compatible Python version (3.8-3.11)
- For FFmpeg errors: Add FFmpeg to system PATH
- For npm errors: Try `npm cache clean --force`

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📧 Support

For issues or questions, please open an issue on the project repository.

---

**Made with ❤️ using AI-powered emotion recognition**
