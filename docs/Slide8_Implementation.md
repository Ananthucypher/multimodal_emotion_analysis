# 📋 Slide 8: Implementation Details

## **Project Name: MIRO - Multimodal Emotion Analysis System**

---

## 🖥️ Hardware Requirements

| Component | Specification |
|-----------|--------------|
| **Processor** | Any modern CPU (Intel/AMD with 4+ cores recommended) |
| **RAM** | 8 GB minimum, 16 GB recommended |
| **GPU** | Optional (NVIDIA with CUDA for TensorFlow acceleration) |
| **Storage** | ~2 GB for dependencies and models |
| **Platform** | Cross-platform (Windows, macOS, Linux) |

---

## 🛠️ Software Stack

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.8 - 3.11 | Core programming language |
| **Flask** | 3.0.0 | Web framework / REST API |
| **Flask-CORS** | 4.0.0 | Cross-Origin Resource Sharing |
| **TensorFlow** | 2.15.0 | Deep learning framework |
| **Keras** | (bundled with TF) | High-level neural network API |
| **OpenCV** | 4.9.0.80 | Video frame processing |
| **DeepFace** | 0.0.92 | Facial emotion recognition |
| **Librosa** | 0.10.1 | Audio feature extraction |
| **Pydub** | 0.25.1 | Audio manipulation |
| **SpeechRecognition** | 3.10.1 | Speech-to-text conversion |
| **NLTK (VADER)** | - | Sentiment analysis |
| **FFmpeg** | External | Audio/Video processing |

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.2.0 | UI component framework |
| **React Router DOM** | 6.20.0 | Client-side routing |
| **Axios** | 1.6.0 | HTTP client for API calls |
| **Framer Motion** | 10.16.0 | Animations & transitions |
| **Recharts** | 2.10.0 | Data visualization (charts) |
| **Three.js** | 0.150.1 | 3D graphics |
| **React Three Fiber** | 8.15.0 | React renderer for Three.js |

---

## 🧠 AI/ML Models & Layers

### 1. Facial Emotion Recognition (DeepFace)

- **Architecture**: Pre-trained CNN-based model
- **Detects**: 7 emotions (happy, sad, angry, fear, surprise, disgust, neutral)
- **Processing**: Frame-by-frame analysis (every 5th frame for efficiency)
- **Output**: Dominant emotion aggregated across all video frames

### 2. Audio Tone Emotion Model (Custom Keras Model)

- **Model File**: `emotion_model_4class.keras`
- **Architecture**: LSTM/CNN-based deep learning model
- **Classes**: 4 emotions (neutral, happy, sad, angry)
- **Input Features**:
  - **MFCC** (40 coefficients) - Mel-Frequency Cepstral Coefficients
  - **Chroma Features** - Pitch class profiles
  - **Spectral Contrast** - Valley-to-peak differences
  - **Zero Crossing Rate** - Signal sign changes
- **Feature Shape**: 174 timesteps × 60 features
- **Output**: Probability distribution over 4 emotion classes

### 3. Speech Recognition (Google Speech API)

- **Type**: Cloud-based API
- **Language**: English (en-US)
- **Output**: Transcribed text from audio

### 4. Sentiment Analysis (NLTK VADER)

- **Model**: Valence Aware Dictionary and Sentiment Reasoner
- **Type**: Lexicon and rule-based analysis
- **Output**: Compound sentiment score (-1 to +1)
- **Classification**:
  - Positive (≥ 0.4) → Happy
  - Negative (≤ -0.4) → Sad/Angry
  - Neutral (-0.4 to 0.4) → Neutral

---

## 🔄 System Architecture / Data Flow

```
                     ┌─────────────────────────────────────┐
                     │         FRONTEND (React)            │
                     │  ┌─────────────────────────────┐    │
                     │  │     Video Upload (Drag/Drop) │    │
                     │  └─────────────┬───────────────┘    │
                     └────────────────┼───────────────────┘
                                      │ HTTP POST
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        BACKEND (Flask API)                               │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Video Processing Pipeline                       │  │
│  │                                                                    │  │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │  │
│  │  │ 1. FACE      │   │ 2. AUDIO     │   │ 3. SPEECH-TO-TEXT    │   │  │
│  │  │ ANALYSIS     │   │ EXTRACTION   │   │    (Google API)      │   │  │
│  │  │ (DeepFace +  │   │ (Pydub)      │   │                      │   │  │
│  │  │  OpenCV)     │   │              │   │    ↓                 │   │  │
│  │  └──────┬───────┘   └──────┬───────┘   │ 4. SENTIMENT         │   │  │
│  │         │                  │           │    ANALYSIS (VADER)  │   │  │
│  │         │                  │           └──────────┬───────────┘   │  │
│  │         │                  │                      │               │  │
│  │         │           ┌──────▼───────┐              │               │  │
│  │         │           │ 5. AUDIO     │              │               │  │
│  │         │           │ TONE MODEL   │              │               │  │
│  │         │           │ (Keras LSTM) │              │               │  │
│  │         │           └──────┬───────┘              │               │  │
│  │         │                  │                      │               │  │
│  │         └──────────────────┴──────────────────────┘               │  │
│  │                            │                                      │  │
│  │                     ┌──────▼──────┐                               │  │
│  │                     │ 6. FUSION   │  Weighted Voting:             │  │
│  │                     │   ENGINE    │  Face: 40%, Audio: 30%,       │  │
│  │                     │             │  Text: 30%                    │  │
│  │                     └──────┬──────┘                               │  │
│  │                            │                                      │  │
│  └────────────────────────────┼──────────────────────────────────────┘  │
│                               │                                          │
└───────────────────────────────┼──────────────────────────────────────────┘
                                │ JSON Response
                                ▼
                     ┌─────────────────────────────────────┐
                     │         FRONTEND (React)            │
                     │  ┌─────────────────────────────┐    │
                     │  │    Results Visualization     │    │
                     │  │  • Emotion Charts (Recharts) │    │
                     │  │  • Confidence Scores         │    │
                     │  │  • Transcript Display        │    │
                     │  │  • Animated UI (Framer)      │    │
                     │  └─────────────────────────────┘    │
                     └─────────────────────────────────────┘
```

---

## 🎯 Multimodal Fusion Algorithm

```python
# Weighted Voting Fusion
weights = {
    "face_emotion": 0.4,    # 40% weight
    "audio_tone": 0.3,      # 30% weight  
    "text_sentiment": 0.3   # 30% weight
}

# Final emotion = max(weighted_votes)
overall_emotion = argmax(Σ modality_votes × weights)
```

### Fusion Logic Explained

1. **Face Emotion (40% weight)**: Visual expressions carry the highest weight as they are the most reliable indicator of emotion
2. **Audio Tone (30% weight)**: Voice tone and prosody provide complementary emotional cues
3. **Text Sentiment (30% weight)**: The actual words spoken reveal semantic emotional content

The system combines these three modalities using a weighted voting mechanism:
- Each modality contributes its detected emotion with its assigned weight
- The emotion with the highest cumulative weighted score becomes the overall emotion
- Confidence is calculated based on the winning emotion's total vote

---

## 📊 Key Implementation Features

| Feature | Description |
|---------|-------------|
| **Frame Sampling** | Analyzes every 5th frame for efficiency |
| **Probability Smoothing** | Temperature scaling (0.4) for better visualization |
| **RESTful API** | Single endpoint (`/analyze_full_video`) for complete analysis |
| **Error Handling** | Graceful fallbacks when modalities fail |
| **Real-time Feedback** | Loading animations during processing |
| **Theme Support** | Light/Dark mode toggle |

---

## 🔌 API Endpoint

### POST `/analyze_full_video`

**Request:**
- Content-Type: `multipart/form-data`
- Body: `video` file (MP4, AVI, MOV, WEBM)

**Response:**
```json
{
  "face_emotion_result": {
    "dominant_face_emotion": "happy",
    "total_frames": 187,
    "analyzed_frames": 37,
    "frame_emotions": {
      "happy": 20,
      "surprise": 10,
      "neutral": 7
    }
  },
  "audio_tone_emotion": {
    "predicted": "happy",
    "probs": {
      "neutral": 0.15,
      "happy": 0.55,
      "sad": 0.18,
      "angry": 0.12
    }
  },
  "transcript": "Hello, I am feeling great today!",
  "transcript_sentiment": {
    "primary_emotion": "happy",
    "score": 0.85,
    "description": "Positive sentiment detected"
  },
  "overall_emotion": {
    "overall_emotion": "happy",
    "confidence": 0.95,
    "description": "Combined analysis from face, audio, and speech modalities"
  }
}
```

---

## 🎨 Frontend Components

| Component | File | Purpose |
|-----------|------|---------|
| **App** | `App.js` | Main router and theme management |
| **Home** | `pages/Home.js` | Landing page with 3D elements |
| **Analyze** | `pages/Analyze.js` | Video upload with drag-and-drop |
| **Results** | `pages/Results.js` | Emotion visualization dashboard |
| **EmotionChart** | `components/EmotionChart.js` | Recharts bar/pie charts |
| **ThemeToggle** | `components/ThemeToggle.js` | Light/Dark mode switch |
| **AnimatedBackground** | `components/AnimatedBackground.js` | Dynamic gradient background |

---

## 📁 Project Structure

```
multimodal_emotion_analysis/
├── backend/
│   ├── backend.py              # Flask API server (385 lines)
│   ├── requirements.txt        # Python dependencies
│   ├── models/                 # ML model files
│   │   ├── emotion_model_4class.keras
│   │   └── label_encoder_4class.pkl
│   └── .env.example
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js              # Main React component
│   │   ├── App.css             # Global styles
│   │   ├── index.js            # Entry point
│   │   ├── index.css           # CSS variables & animations
│   │   ├── theme.js            # Theme configuration
│   │   ├── components/
│   │   │   ├── EmotionChart.js
│   │   │   ├── ThemeToggle.js
│   │   │   └── AnimatedBackground.js
│   │   └── pages/
│   │       ├── Home.js
│   │       ├── Analyze.js
│   │       └── Results.js
│   └── package.json
└── README.md
```

---

## 🚀 Deployment Requirements

### Backend
1. Python 3.8 - 3.11
2. FFmpeg installed and in PATH
3. TensorFlow with Keras
4. All pip dependencies from requirements.txt

### Frontend
1. Node.js 16+ 
2. npm or yarn package manager
3. All npm dependencies from package.json

---

## 📈 Performance Considerations

| Aspect | Implementation |
|--------|----------------|
| **Video Processing** | Frame sampling (every 5th frame) reduces computation by ~80% |
| **Model Loading** | Models loaded once at startup, cached in memory |
| **Audio Processing** | Converted to WAV for consistent analysis |
| **Feature Extraction** | Fixed-length padding/truncation to 174 timesteps |
| **API Response** | JSON format for lightweight data transfer |

---

*Document generated for MIRO Multimodal Emotion Analysis System Presentation*
*Date: December 2024*
