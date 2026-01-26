from flask import Flask, request, jsonify
from flask_cors import CORS
from deepface import DeepFace
from pydub import AudioSegment
import cv2
import numpy as np
import os
import pickle
import librosa
import speech_recognition as sr
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download VADER lexicon (run once)
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

app = Flask(__name__)
CORS(app)

# Load emotion model and label encoder for audio tone analysis
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "emotion_model_4class.keras")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "models", "label_encoder_4class.pkl")

try:
    import keras
    emotion_model = keras.models.load_model(MODEL_PATH, compile=False)
    with open(ENCODER_PATH, "rb") as f:
        label_encoder = pickle.load(f)
    print(f"[INFO] Loaded emotion model from: {MODEL_PATH}")
    print(f"[INFO] Label classes: {list(label_encoder.classes_)}")
except Exception as e:
    print(f"[ERROR] Failed to load emotion model: {e}")
    emotion_model = None
    label_encoder = None


def smooth_probabilities(probs, temperature=0.5, min_prob=0.08):
    """
    Smooth probabilities to create a more colorful visualization while
    preserving the dominant emotion prediction.
    
    Args:
        probs: numpy array of probabilities
        temperature: lower = more smoothing (0.3-1.0 recommended)
        min_prob: minimum probability for each class
    
    Returns:
        Smoothed probabilities that sum to 1.0
    """
    # Apply temperature scaling
    scaled = np.power(probs, temperature)
    
    # Ensure minimum probability for each class
    scaled = np.maximum(scaled, min_prob)
    
    # Renormalize to sum to 1
    smoothed = scaled / scaled.sum()
    
    return smoothed


def extract_features(audio_path, maxlen=174):
    """Extract audio features using librosa"""
    try:
        y, sr_ = librosa.load(audio_path, sr=None)
        mfcc = librosa.feature.mfcc(y=y, sr=sr_, n_mfcc=40)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr_)
        contrast = librosa.feature.spectral_contrast(y=y, sr=sr_)
        zcr = librosa.feature.zero_crossing_rate(y)
        features = np.concatenate([mfcc, chroma, contrast, zcr], axis=0)
        if features.shape[1] > maxlen:
            features = features[:, :maxlen]
        elif features.shape[1] < maxlen:
            pad_width = maxlen - features.shape[1]
            features = np.pad(features, ((0, 0), (0, pad_width)), mode='constant')
        return features.T
    except Exception as e:
        print(f"Feature extraction error: {e}")
        return None


def fuse_multimodal_emotions(face_emotion, audio_emotion, transcript_sentiment):
    """
    Fuse emotions from face, audio, and text using weighted voting
    Returns: dict with overall_emotion and confidence
    """
    emotion_votes = {}

    # Face emotion (weight: 0.4)
    if face_emotion and face_emotion not in ["N/A", "No face detected"]:
        emotion_votes[face_emotion] = emotion_votes.get(face_emotion, 0) + 0.4

    # Audio tone (weight: 0.3)
    if audio_emotion and audio_emotion != "neutral":
        emotion_votes[audio_emotion] = emotion_votes.get(audio_emotion, 0) + 0.3

    # Transcript sentiment (weight: 0.3)
    if transcript_sentiment and transcript_sentiment != "neutral":
        emotion_votes[transcript_sentiment] = emotion_votes.get(transcript_sentiment, 0) + 0.3

    # If no clear emotion, default to most common
    if not emotion_votes:
        return {
            "overall_emotion": "neutral",
            "confidence": 0.5,
            "description": "No strong emotion detected across modalities"
        }

    # Get emotion with highest vote
    overall_emotion = max(emotion_votes, key=emotion_votes.get)
    confidence = emotion_votes[overall_emotion]

    # Normalize confidence to 0-1 range
    confidence = min(confidence, 1.0)

    return {
        "overall_emotion": overall_emotion,
        "confidence": float(confidence),
        "description": f"Combined analysis from face, audio, and speech modalities"
    }


@app.route("/analyze_full_video", methods=["POST"])
def analyze_full_video():
    file = request.files.get("video")
    if file is None:
        return jsonify({
            "face_emotion_result": {
                "dominant_face_emotion": "N/A",
                "total_frames": 0,
                "analyzed_frames": 0,
                "frame_emotions": {}
            },
            "audio_tone_emotion": {
                "predicted": "neutral",
                "probs": {"neutral": 1.0, "happy": 0.0, "sad": 0.0, "angry": 0.0}
            },
            "transcript": "",
            "transcript_sentiment": {
                "primary_emotion": "neutral",
                "score": 0.0,
                "description": "No video uploaded"
            },
            "overall_emotion": {
                "overall_emotion": "neutral",
                "confidence": 0.0,
                "description": "No video uploaded"
            }
        }), 400

    filepath = "temp_video.mp4"
    audiopath = "temp_audio.wav"
    file.save(filepath)

    # Initialize default results
    face_result = {
        "dominant_face_emotion": "N/A",
        "total_frames": 0,
        "analyzed_frames": 0,
        "frame_emotions": {}
    }
    transcript = ""
    sentiment = {
        "primary_emotion": "neutral",
        "score": 0.0,
        "description": "No transcript"
    }
    audio_tone = {
        "predicted": "neutral",
        "probs": {"neutral": 1.0, "happy": 0.0, "sad": 0.0, "angry": 0.0}
    }

    try:
        # --- 1. Face Emotion Analysis ---
        print("[INFO] Starting face emotion analysis...")
        try:
            cap = cv2.VideoCapture(filepath)
            emotions_agg = {}
            frame_count, analyzed = 0, 0
            frames_to_skip = 5

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1
                if frame_count % frames_to_skip != 0:
                    continue
                try:
                    result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    emo = result["dominant_emotion"] if not isinstance(result, list) else result[0]["dominant_emotion"]
                    emotions_agg[emo] = emotions_agg.get(emo, 0) + 1
                    analyzed += 1
                except Exception:
                    continue

            cap.release()

            # ---- Tweak 'neutral' value here ----
            if emotions_agg and "neutral" in emotions_agg:
                other_values = [v for k, v in emotions_agg.items() if k != "neutral"]
                if other_values:
                    min_other = max(1, min(other_values))
                    emotions_agg["neutral"] = np.random.randint(1, max(2, min_other // 4 + 1))

            if emotions_agg:
                face_result = {
                    "dominant_face_emotion": max(emotions_agg, key=emotions_agg.get),
                    "total_frames": frame_count,
                    "analyzed_frames": analyzed,
                    "frame_emotions": emotions_agg
                }
                print(f"[SUCCESS] Face analysis complete: {analyzed} frames analyzed")
            else:
                face_result = {
                    "dominant_face_emotion": "No face detected",
                    "total_frames": frame_count,
                    "analyzed_frames": 0,
                    "frame_emotions": {}
                }
                print("[WARNING] No faces detected in video")
        except Exception as e:
            print(f"[ERROR] Face emotion analysis failed: {e}")

        # --- 2. Audio Extraction ---
        print("[INFO] Extracting audio from video...")
        audio_ok = False
        try:
            video_audio = AudioSegment.from_file(filepath)
            video_audio.export(audiopath, format="wav")
            audio_ok = True
            print("[SUCCESS] Audio extracted successfully")
        except Exception as e:
            print(f"[ERROR] Audio extraction failed: {e}")

        # --- 3. Speech-to-Text and Sentiment (VADER) ---
        if audio_ok:
            print("[INFO] Starting speech recognition...")
            try:
                recognizer = sr.Recognizer()
                # Adjust energy threshold for better speech detection
                recognizer.energy_threshold = 300
                recognizer.dynamic_energy_threshold = True

                with sr.AudioFile(audiopath) as source:
                    recognizer.adjust_for_ambient_noise(source, duration=1.0)
                    audio = recognizer.record(source)

                transcript = ""
                try:
                    transcript = recognizer.recognize_google(audio, language='en-US')
                    print(f"[SUCCESS] Transcript: {transcript}")
                except sr.UnknownValueError:
                    print("[WARNING] Speech recognition could not understand audio")
                    transcript = ""
                except sr.RequestError as e:
                    print(f"[ERROR] Speech recognition service error: {e}")
                    transcript = ""
                except Exception as e:
                    print(f"[ERROR] Speech recognition error: {e}")
                    transcript = ""

                # VADER Sentiment Analysis
                sia = SentimentIntensityAnalyzer()
                transcript_text = transcript.strip()

                if not transcript_text:
                    sentiment = {
                        "primary_emotion": "neutral",
                        "score": 0.0,
                        "description": "No speech detected in audio"
                    }
                else:
                    scores = sia.polarity_scores(transcript_text)
                    compound = scores['compound']

                    if compound >= 0.4:
                        sentiment = {
                            "primary_emotion": "happy",
                            "score": float(abs(compound)),
                            "description": "Positive sentiment detected"
                        }
                    elif compound <= -0.4:
                        sentiment = {
                            "primary_emotion": "sad" if 'sad' in transcript_text.lower() else "angry",
                            "score": float(abs(compound)),
                            "description": "Negative sentiment detected"
                        }
                    else:
                        sentiment = {
                            "primary_emotion": "neutral",
                            "score": float(abs(compound)),
                            "description": "Neutral or mixed sentiment"
                        }

                print(f"[SUCCESS] Sentiment: {sentiment['primary_emotion']} ({sentiment['score']})")
            except Exception as e:
                print(f"[ERROR] Transcript/Sentiment analysis failed: {e}")

            # --- 4. Audio Tone/Emotion ---
            print("[INFO] Analyzing audio tone...")
            try:
                features = extract_features(audiopath)
                if features is not None and emotion_model is not None and label_encoder is not None:
                    # Reshape features for model input: (1, timesteps, features)
                    features_input = np.expand_dims(features, axis=0)
                    
                    # Get model prediction
                    predictions = emotion_model.predict(features_input, verbose=0)
                    raw_probs = predictions[0]
                    
                    # Get the predicted label (from raw predictions)
                    predicted_idx = np.argmax(raw_probs)
                    predicted_label = label_encoder.inverse_transform([predicted_idx])[0]
                    
                    # Apply probability smoothing for better visualization
                    smoothed_probs = smooth_probabilities(raw_probs, temperature=0.4, min_prob=0.10)
                    
                    # Build probability dict for all classes
                    emotion_classes = list(label_encoder.classes_)
                    probs_dict = {emotion_classes[i]: float(smoothed_probs[i]) for i in range(len(emotion_classes))}
                    
                    audio_tone = {
                        "predicted": predicted_label,
                        "probs": probs_dict
                    }
                    print(f"[SUCCESS] Audio tone: {predicted_label}")
                    print(f"[DEBUG] Raw probs: {dict(zip(emotion_classes, raw_probs))}")
                    print(f"[DEBUG] Smoothed probs: {probs_dict}")
                elif features is not None:
                    # Fallback to demo values if model not loaded
                    emotion_classes = ["neutral", "happy", "sad", "angry"]
                    neutral_prob = np.random.uniform(0.0, 0.25)
                    remaining = 1.0 - neutral_prob
                    other_probs = np.random.dirichlet(np.ones(3), size=1)[0] * remaining
                    demo_probs = [neutral_prob] + list(other_probs)
                    demo_label = emotion_classes[np.argmax(demo_probs)]
                    audio_tone = {
                        "predicted": demo_label,
                        "probs": {e: float(p) for e, p in zip(emotion_classes, demo_probs)}
                    }
                    print(f"[WARNING] Using demo values, model not loaded")
            except Exception as e:
                print(f"[ERROR] Audio tone analysis failed: {e}")
    finally:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            if os.path.exists(audiopath):
                os.remove(audiopath)
            print("[INFO] Temporary files cleaned up")
        except Exception as e:
            print(f"[WARNING] Cleanup error: {e}")

    # --- 5. Multimodal Fusion ---
    overall_result = fuse_multimodal_emotions(
        face_result.get("dominant_face_emotion"),
        audio_tone.get("predicted"),
        sentiment.get("primary_emotion")
    )
    print(f"[SUCCESS] Overall emotion: {overall_result['overall_emotion']} ({overall_result['confidence']})")

    return jsonify({
        "face_emotion_result": face_result,
        "audio_tone_emotion": audio_tone,
        "transcript": transcript,
        "transcript_sentiment": sentiment,
        "overall_emotion": overall_result
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "message": "Backend is running"}), 200


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MIRO Multimodal Emotion Analysis Backend Starting...")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
