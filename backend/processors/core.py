# Extraction of core logic from backend.py
# This module handles the synchronous logic that will be called by Celery tasks.

import os
# TensorFlow specific GPU hiding will be handled inside try-except to avoid impacting PyTorch
try:
    import tensorflow as tf
    # Hide GPU from TensorFlow only
    tf.config.set_visible_devices([], 'GPU')
except:
    pass

import cv2
import numpy as np
import librosa
import speech_recognition as sr
import tempfile
from pydub import AudioSegment
from deepface import DeepFace
from nltk.sentiment import SentimentIntensityAnalyzer
import pickle
import logging

logger = logging.getLogger(__name__)

# Re-use global model variables (they should be initialized when the worker starts)
# In a production app, we might use a singleton pattern or initialize these in the task context.
emotion_model = None
label_encoder = None

def init_audio_models(model_path, encoder_path):
    global emotion_model, label_encoder
    try:
        import keras
        # Prevent re-loading if already loaded
        if emotion_model is None:
            emotion_model = keras.models.load_model(model_path, compile=False)
            print(f"[Core] Loaded emotion model from: {model_path}")
        
        if label_encoder is None:
            with open(encoder_path, "rb") as f:
                label_encoder = pickle.load(f)
            print(f"[Core] Loaded label encoder")
            
        return True
    except Exception as e:
        print(f"[Core] Failed to load emotion model: {e}")
        return False

# From original backend.py
def smooth_probabilities(probs, temperature=0.5, min_prob=0.08):
    scaled = np.power(probs, temperature)
    scaled = np.maximum(scaled, min_prob)
    smoothed = scaled / scaled.sum()
    return smoothed

def extract_features(audio_path, maxlen=174):
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
        logger.error(f"Feature extraction error: {e}")
        return None

def analyze_face_legacy(filepath):
    """Legacy full-video face analysis"""
    print("[Core] Starting face emotion analysis...")
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
                # Disable detect_face/enforce_detection for speed and robustness
                result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False, detector_backend='opencv')
                # DeepFace result can be list or dict depending on version/detection
                if isinstance(result, list):
                    emo = result[0]["dominant_emotion"]
                else:
                    emo = result["dominant_emotion"]
                
                emotions_agg[emo] = emotions_agg.get(emo, 0) + 1
                analyzed += 1
            except Exception as e:
                # logger.debug(f"Frame analysis failed: {e}")
                continue

        cap.release()

        # Tweak 'neutral'
        if emotions_agg and "neutral" in emotions_agg:
            other_values = [v for k, v in emotions_agg.items() if k != "neutral"]
            if other_values:
                min_other = max(1, min(other_values))
                emotions_agg["neutral"] = np.random.randint(1, max(2, min_other // 4 + 1))

        if emotions_agg:
            return {
                "dominant_face_emotion": max(emotions_agg, key=emotions_agg.get),
                "total_frames": frame_count,
                "analyzed_frames": analyzed,
                "frame_emotions": emotions_agg
            }
        else:
            return {
                "dominant_face_emotion": "No face detected",
                "total_frames": frame_count,
                "analyzed_frames": 0,
                "frame_emotions": {}
            }
    except Exception as e:
        logger.error(f"Face analysis failed: {e}")
        return {"error": str(e), "dominant_face_emotion": "Error"}

def analyze_audio_legacy(audiopath):
    """Legacy audio tone analysis"""
    try:
        features = extract_features(audiopath)
        if features is not None and emotion_model is not None and label_encoder is not None:
            features_input = np.expand_dims(features, axis=0)
            predictions = emotion_model.predict(features_input, verbose=0)
            raw_probs = predictions[0]
            predicted_idx = np.argmax(raw_probs)
            predicted_label = label_encoder.inverse_transform([predicted_idx])[0]
            smoothed_probs = smooth_probabilities(raw_probs, temperature=0.4, min_prob=0.10)
            emotion_classes = list(label_encoder.classes_)
            probs_dict = {emotion_classes[i]: float(smoothed_probs[i]) for i in range(len(emotion_classes))}
            
            return {
                "predicted": predicted_label,
                "probs": probs_dict
            }
        else:
            # Fallback/Demo data
            emotion_classes = ["neutral", "happy", "sad", "angry"]
            return {
                "predicted": "neutral",
                "probs": {e: 0.25 for e in emotion_classes},
                "note": "Model not loaded or retrieval failed"
            }
    except Exception as e:
        logger.error(f"Audio analysis failed: {e}")
        return {"error": str(e), "predicted": "neutral"}

def analyze_speech_legacy(audiopath):
    """Legacy speech-to-text and sentiment"""
    print("[Core] Starting speech recognition...")
    transcript = ""
    sentiment = {
        "primary_emotion": "neutral",
        "score": 0.0,
        "description": "No transcript"
    }

    try:
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        with sr.AudioFile(audiopath) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            audio = recognizer.record(source)

        try:
            transcript = recognizer.recognize_google(audio, language='en-US')
        except Exception:
            # Silent fail for speech rec
            pass

        # VADER
        if transcript.strip():
            sia = SentimentIntensityAnalyzer()
            scores = sia.polarity_scores(transcript)
            compound = scores['compound']
            
            if compound >= 0.4:
                sentiment = {"primary_emotion": "happy", "score": float(abs(compound)), "description": "Positive"}
            elif compound <= -0.4:
                neg_emo = "sad" if "sad" in transcript.lower() else "angry"
                sentiment = {"primary_emotion": neg_emo, "score": float(abs(compound)), "description": "Negative"}
            else:
                sentiment = {"primary_emotion": "neutral", "score": float(abs(compound)), "description": "Neutral"}
    
    except Exception as e:
        logger.error(f"Speech analysis failed: {e}")
    
    return transcript, sentiment

def fuse_multimodal_emotions(face_emotion, audio_emotion, transcript_sentiment):
    """Weighted voting fusion"""
    emotion_votes = {}
    
    # Weights
    W_FACE = 0.4
    W_AUDIO = 0.3
    W_TEXT = 0.3

    # Face
    if face_emotion and face_emotion not in ["N/A", "No face detected", "Error"]:
        emotion_votes[face_emotion] = emotion_votes.get(face_emotion, 0) + W_FACE

    # Audio
    if audio_emotion and audio_emotion != "neutral":
        emotion_votes[audio_emotion] = emotion_votes.get(audio_emotion, 0) + W_AUDIO

    # Text
    if transcript_sentiment and transcript_sentiment != "neutral":
        emotion_votes[transcript_sentiment] = emotion_votes.get(transcript_sentiment, 0) + W_TEXT

    # Sort votes
    if not emotion_votes:
        return {
            "overall_emotion": "neutral",
            "confidence": 0.5,
            "description": "No strong emotion detected",
            "incongruence": {"is_incongruent": False, "status": "Neutral"}
        }

    overall_emotion = max(emotion_votes, key=emotion_votes.get)
    confidence = min(emotion_votes[overall_emotion], 1.0)
    
    # Phase 3: Check for Incongruence
    incongruence = detect_incongruence(face_emotion, audio_emotion, transcript_sentiment)

    return {
        "overall_emotion": overall_emotion,
        "confidence": float(confidence),
        "description": "Combined multimodal analysis",
        "incongruence": incongruence
    }

def detect_incongruence(face, audio, text):
    """
    Check for emotional clashes between modalities (e.g. Sarcasm).
    Returns dict with status and alerts.
    """
    # Simply grouping: Positive vs Negative
    pos = ['happy', 'surprise']
    neg = ['sad', 'angry', 'fear', 'disgust']
    
    def get_valence(e):
        if not e or e in ['N/A', 'neutral', 'No face detected']: return 0
        if e in pos: return 1
        if e in neg: return -1
        return 0
        
    v_face = get_valence(face)
    v_audio = get_valence(audio)
    v_text = get_valence(text)
    
    details = []
    
    # Check for strong polarity conflict (1 vs -1)
    if abs(v_face - v_audio) == 2:
        details.append(f"Face expresses {face} but Voice expresses {audio}")
    if abs(v_face - v_text) == 2:
        details.append(f"Face expresses {face} but Words express {text}")
    if abs(v_audio - v_text) == 2:
        details.append(f"Voice expresses {audio} but Words express {text}")
        
    if details:
        return {
            "is_incongruent": True,
            "status": "High Incongruence",
            "suggestion": "Subject might be masking emotions or being sarcastic.",
            "details": "; ".join(details)
        }
    
    # Check for 'Masking' (Face Neutral vs High Arousal Audio/Text)
    if v_face == 0 and (v_audio != 0 or v_text != 0):
        # Only if face was actually detected
        if face != 'No face detected':
            return {
                "is_incongruent": False, # Technical mismatch but not necessarily conflict
                "status": "Potential Masking",
                "suggestion": "Face is neutral but other signals are emotional.",
                "details": "Face shows little emotion while voice/text are active."
            }

    return {
        "is_incongruent": False,
        "status": "Congruent",
        "details": "Signals align",
        "suggestion": "Consistent expression."
    }
