"""
MIRO Video Processing Task - Phase 6 ("Flash" Optimization)
============================================================
Optimizations:
1. Resident LLM (GGUF) - No Loading Latency
2. MediaPipe Face (GPU) - <2s Latency
3. Faster-Whisper (INT8) - <3s Latency
4. Micro-Chunk Parallelism
"""
from celery import current_task
from celery_config import celery_app
from processors import core, audio_dim, audio_emotion
from processors import face_mediapipe as face_mp
from processors import speech_faster as speech_transcribe
from processors import text_gguf as llm
from utils import video_stream
import os
import shutil
import tempfile
import logging
import time
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# PHASE 6: RESIDENT MODEL LOADING
# ============================================================
def preload_optimized_models():
    """Preload lightweight resident models."""
    logger.info("=== PRELOADING RESIDENT MODELS ===")
    try:
        # 1. Faster Whisper (INT8)
        speech_transcribe.get_whisper_model()
        # 2. Llama GGUF (Resident)
        llm.get_llm()
        # 3. Audio Emotion (FP32 Stable)
        audio_emotion.get_audio_emotion_model()
    except Exception as e:
        logger.error(f"Preload failed: {e}")

# Check if running in Celery
import sys
if 'celery' in sys.modules and 'worker' in ' '.join(sys.argv).lower():
    preload_optimized_models()


def process_mp_face(video_path):
    """MediaPipe GPU Face Analysis."""
    return face_mp.analyze_face_mediapipe(video_path)

def process_audio_modality(temp_audio_path):
    """Audio Analysis (Emotion + Dimensions)."""
    try:
        emo = audio_emotion.analyze_audio_emotion(temp_audio_path)
        dims = audio_dim.analyze_audio_dimensional(temp_audio_path)
        return {"emotion": emo, "dimensions": dims}
    except Exception as e: 
        logger.error(f"Audio failed: {e}")
        return {"emotion": {}, "dimensions": {}}

def process_speech_modality(temp_audio_path):
    """Faster-Whisper Transcription."""
    try:
        return {"transcript": speech_transcribe.transcribe_audio(temp_audio_path)}
    except Exception as e:
        logger.error(f"Speech failed: {e}")
        return {"transcript": ""}

@celery_app.task(bind=True)
def process_video_job(self, video_path):
    """
    Async task - Phase 6 Optimized logic.
    """
    start_time = time.time()
    logger.info(f"Starting PHASE 6 OPTIMIZED job for {video_path}")
    
    job_dir = os.path.join(tempfile.gettempdir(), f"miro_job_{self.request.id}")
    os.makedirs(job_dir, exist_ok=True)
    temp_audio_path = os.path.join(job_dir, "audio.wav")
    
    try:
        # 1. Extraction (Fast)
        self.update_state(state='PROGRESS', meta={'status': 'Extracting...', 'progress': 10})
        
        # Determine duration
        duration = video_stream.get_video_duration(video_path)
        
        # Extract audio
        from pydub import AudioSegment
        audio = AudioSegment.from_file(video_path)
        audio.export(temp_audio_path, format="wav")
        
        # 2. Parallel Analysis (MediaPipe + Audio + Whisper)
        # All models fit in VRAM/RAM now. No swapping needed.
        self.update_state(state='PROGRESS', meta={'status': 'Analyzing signals...', 'progress': 30})
        
        t0_parallel = time.time()
        
        face_res = {}
        audio_res = {}
        speech_res = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            f_face = executor.submit(process_mp_face, video_path)
            f_audio = executor.submit(process_audio_modality, temp_audio_path)
            f_speech = executor.submit(process_speech_modality, temp_audio_path)
            
            # Wait for results
            face_res = f_face.result()
            audio_res = f_audio.result()
            speech_res = f_speech.result()
            
        t_parallel = time.time() - t0_parallel
        logger.info(f"Signal Analysis took {t_parallel:.1f}s")
        
        # 3. Fusion Logic
        self.update_state(state='PROGRESS', meta={'status': 'Fusing & Thinking...', 'progress': 70})
        
        # Unpack
        dominant_face = face_res.get('dominant_emotion', 'neutral')
        transcript = speech_res.get('transcript', '')
        
        # Audio Unpack
        a_emo = audio_res.get('emotion', {})
        a_dim = audio_res.get('dimensions', {})
        predicted_audio = a_emo.get('predicted', 'neutral')
        
        # Incongruence Check
        # Simple sentiment for fusion
        from nltk.sentiment import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        compound = sia.polarity_scores(transcript)['compound'] if transcript else 0
        text_emo = "happy" if compound > 0.4 else ("sad" if compound < -0.4 else "neutral")
        
        fusion_result = core.fuse_multimodal_emotions(dominant_face, predicted_audio, text_emo)
        
        # 4. LLM Generation (Resident GGUF)
        # No unload/reload needed. Instant inference.
        llm_context = {
            "transcript": transcript,
            "emotions": {
                "face": dominant_face,
                "voice": predicted_audio,
                "incongruence": fusion_result.get("incongruence", {})
            }
        }
        
        therapeutic_advice = llm.generate_therapeutic_response(llm_context)
        
        # 5. Final Payload
        total_time = time.time() - start_time
        logger.info(f"JOB FINISHED in {total_time:.1f}s")
        
        return {
            "face_emotion_result": {
                 "dominant_face_emotion": dominant_face,
                 "frame_emotions": face_res.get("emotions", {}),
                 "advanced_action_units": {} # MediaPipe doesn't output AUs same way as PyFeat
            },
            "audio_tone_emotion": {
                "predicted": predicted_audio,
                "probs": a_emo.get("probs", {}),
                "dimensional_metrics": a_dim
            },
            "transcript": transcript,
            "transcript_sentiment": {"score": compound, "primary_emotion": text_emo},
            "llm_analysis": {}, # Legacy field
            "overall_emotion": fusion_result,
            "therapeutic_advice": therapeutic_advice,
            "performance": {
                "total_time_seconds": round(total_time, 1),
                "parallel_analysis_seconds": round(t_parallel, 1)
            }
        }

    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        raise e
    finally:
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir)
