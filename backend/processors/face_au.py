from feat import Detector
import logging
import pandas as pd
import os

# Configure logging
logger = logging.getLogger(__name__)

# Global cache for the heavy model to avoid reloading per task
_feat_detector = None

def get_detector():
    global _feat_detector
    if _feat_detector is None:
        logger.info("Initializing Py-Feat Detector... (First run downloads models)")
        try:
            # Using XGB for AUs (fast/accurate) and RetinaFace for detection
            _feat_detector = Detector(
                face_model="retinaface",
                landmark_model="mobilenet",
                au_model="xgb",
                emotion_model="resmasknet",
                device="cpu", # Force CPU to save VRAM for Audio/Whisper
                verbose=True
            )
            logger.info("Py-Feat Detector initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Py-Feat: {e}")
            raise e
    return _feat_detector

def analyze_face_au(video_path, skip_frames=15):
    """
    Analyzes video for Facial Action Units (AUs) and Emotions using Py-Feat.
    
    Args:
        video_path (str): Path to video file.
        skip_frames (int): Process every Nth frame to optimize speed.
    
    Returns:
        dict: Summary of AU intensities and aggregated emotions.
    """
    try:
        detector = get_detector()
        
        logger.info(f"Running Face AU analysis on: {video_path}")
        # detect_video returns a pandas DataFrame
        prediction = detector.detect_video(video_path, skip_frames=skip_frames)
        
        if prediction is None or prediction.empty:
            logger.warning("Py-Feat found no faces or failed to process frames.")
            return {"status": "no_faces_found"}
            
        # --- Process Results ---
        
        # 1. Action Units (AUs) - Micro-expressions
        au_columns = [col for col in prediction.columns if col.startswith('AU')]
        au_means = prediction[au_columns].mean().to_dict()
        
        # 2. Emotions (Py-Feat's model)
        # Standard columns: anger, disgust, fear, happiness, sadness, surprise, neutral
        possible_emotions = ['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise', 'neutral']
        present_emotions = [c for c in possible_emotions if c in prediction.columns]
        emotion_means = prediction[present_emotions].mean().to_dict()
        
        # 3. Dominant Emotion (based on mean)
        dominant_emotion = max(emotion_means, key=emotion_means.get) if emotion_means else "unknown"
        
        return {
            "status": "success",
            "dominant_emotion": dominant_emotion,
            "emotions": emotion_means,
            "action_units": au_means,
            "frames_processed": len(prediction)
        }

    except Exception as e:
        logger.error(f"Error in analyze_face_au: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }
