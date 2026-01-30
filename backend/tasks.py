"""
MIRO Video Processing Task - P0 SSE Streaming Edition
======================================================
Enhancements:
1. Progressive State Emission via Redis Pub/Sub
2. Hierarchical Timestamps for Observability
3. All Phase 6 optimizations retained

States Emitted:
- JOB_STARTED
- EXTRACTION_COMPLETE
- FACE_READY, AUDIO_READY, TRANSCRIPT_READY (parallel)
- PRIMARY_EMOTION_READY
- INCONGRUENCE_READY
- THERAPEUTIC_RESPONSE_READY
- JOB_COMPLETE / JOB_FAILED
"""
from celery import current_task
from celery_config import celery_app
from processors import core, audio_dim, audio_emotion, therapist
from processors import face_mediapipe as face_mp
from processors import speech_faster as speech_transcribe
from utils import video_stream
import state_emission as emit
import os
import shutil
import tempfile
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# PHASE 6: RESIDENT MODEL LOADING
# ============================================================
def preload_optimized_models():
    """Preload lightweight resident models."""
    logger.info("=== PRELOADING OPTIMIZED MODELS ===")
    try:
        # 1. Faster Whisper (INT8)
        speech_transcribe.get_whisper_model()
        # 2. Audio Emotion (FP32 Stable)
        audio_emotion.get_audio_emotion_model()
        # Note: Ollama LLM loads on-demand (external service)
        logger.info("Models preloaded. Ollama LLM will connect on first use.")
    except Exception as e:
        logger.error(f"Preload failed: {e}")

# Check if running in Celery
import sys
if 'celery' in sys.modules and 'worker' in ' '.join(sys.argv).lower():
    preload_optimized_models()


def process_mp_face(video_path, job_id):
    """MediaPipe GPU Face Analysis with state emission."""
    result = face_mp.analyze_face_mediapipe(video_path)
    # Emit FACE_READY state
    emit.emit_face_ready(
        job_id,
        dominant_emotion=result.get('dominant_emotion', 'neutral'),
        confidence=result.get('emotions', {}).get(result.get('dominant_emotion', 'neutral'), 0.5)
    )
    return result

def process_audio_modality(temp_audio_path, job_id):
    """Audio Analysis (Emotion + Dimensions) with state emission."""
    try:
        emo = audio_emotion.analyze_audio_emotion(temp_audio_path)
        dims = audio_dim.analyze_audio_dimensional(temp_audio_path)
        # Emit AUDIO_READY state
        emit.emit_audio_ready(
            job_id,
            predicted=emo.get('predicted', 'neutral'),
            confidence=emo.get('confidence', 0.5),
            probs=emo.get('probs', {})
        )
        return {"emotion": emo, "dimensions": dims}
    except Exception as e: 
        logger.error(f"Audio failed: {e}")
        return {"emotion": {}, "dimensions": {}}

def process_speech_modality(temp_audio_path, job_id):
    """Faster-Whisper Transcription with state emission."""
    try:
        transcript = speech_transcribe.transcribe_audio(temp_audio_path)
        # Emit TRANSCRIPT_READY state
        emit.emit_transcript_ready(job_id, transcript or "")
        return {"transcript": transcript}
    except Exception as e:
        logger.error(f"Speech failed: {e}")
        return {"transcript": ""}


@celery_app.task(bind=True)
def process_video_job(self, video_path):
    """
    Async task with Progressive State Emission.
    
    Each processing phase emits its state via Redis Pub/Sub,
    enabling real-time SSE delivery to frontend.
    """
    job_id = self.request.id
    start_time = time.time()
    timestamps = {"job_started": datetime.utcnow().isoformat() + 'Z'}
    
    logger.info(f"Starting SSE-enabled job {job_id} for {video_path}")
    
    # Emit JOB_STARTED
    emit.emit_job_started(job_id)
    
    job_dir = os.path.join(tempfile.gettempdir(), f"miro_job_{job_id}")
    os.makedirs(job_dir, exist_ok=True)
    temp_audio_path = os.path.join(job_dir, "audio.wav")
    
    try:
        # ========================================
        # 1. EXTRACTION PHASE
        # ========================================
        self.update_state(state='PROGRESS', meta={'status': 'Extracting...', 'progress': 10})
        t_extract_start = time.time()
        
        # Determine duration
        duration = video_stream.get_video_duration(video_path)
        
        # Extract audio
        from pydub import AudioSegment
        audio = AudioSegment.from_file(video_path)
        audio.export(temp_audio_path, format="wav")
        
        t_extract = time.time() - t_extract_start
        timestamps["extraction_complete"] = datetime.utcnow().isoformat() + 'Z'
        
        # Emit EXTRACTION_COMPLETE
        emit.emit_extraction_complete(job_id, duration)
        
        # ========================================
        # 2. PARALLEL ANALYSIS PHASE
        # ========================================
        self.update_state(state='PROGRESS', meta={'status': 'Analyzing signals...', 'progress': 30})
        t0_parallel = time.time()
        
        face_res = {}
        audio_res = {}
        speech_res = {}
        
        # Submit all modalities in parallel - each emits its own state when done
        with ThreadPoolExecutor(max_workers=3) as executor:
            f_face = executor.submit(process_mp_face, video_path, job_id)
            f_audio = executor.submit(process_audio_modality, temp_audio_path, job_id)
            f_speech = executor.submit(process_speech_modality, temp_audio_path, job_id)
            
            # Wait for results
            face_res = f_face.result()
            audio_res = f_audio.result()
            speech_res = f_speech.result()
            
        t_parallel = time.time() - t0_parallel
        timestamps["parallel_complete"] = datetime.utcnow().isoformat() + 'Z'
        logger.info(f"Signal Analysis took {t_parallel:.1f}s")
        
        # ========================================
        # 3. FUSION PHASE
        # ========================================
        self.update_state(state='PROGRESS', meta={'status': 'Fusing emotions...', 'progress': 60})
        t_fusion_start = time.time()
        
        # Unpack results
        dominant_face = face_res.get('dominant_emotion', 'neutral')
        transcript = speech_res.get('transcript', '')
        
        # Audio Unpack
        a_emo = audio_res.get('emotion', {})
        a_dim = audio_res.get('dimensions', {})
        predicted_audio = a_emo.get('predicted', 'neutral')
        
        # Sentiment analysis
        from nltk.sentiment import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        compound = sia.polarity_scores(transcript)['compound'] if transcript else 0
        text_emo = "happy" if compound > 0.4 else ("sad" if compound < -0.4 else "neutral")
        
        # Fusion
        fusion_result = core.fuse_multimodal_emotions(dominant_face, predicted_audio, text_emo)
        
        t_fusion = time.time() - t_fusion_start
        timestamps["fusion_complete"] = datetime.utcnow().isoformat() + 'Z'
        
        # Emit PRIMARY_EMOTION_READY (first meaningful insight)
        emit.emit_primary_emotion_ready(
            job_id,
            emotion=fusion_result.get('overall_emotion', 'neutral'),
            confidence=fusion_result.get('confidence', 0.5)
        )
        
        # Emit INCONGRUENCE_READY
        incongruence = fusion_result.get('incongruence', {})
        emit.emit_incongruence_ready(job_id, incongruence)
        
        # ========================================
        # 4. LLM GENERATION PHASE
        # ========================================
        self.update_state(state='PROGRESS', meta={'status': 'Generating response...', 'progress': 75})
        t_llm_start = time.time()
        timestamps["llm_started"] = datetime.utcnow().isoformat() + 'Z'
        
        therapeutic_advice = therapist.generate_therapeutic_advice(
            overall_emotion_data=fusion_result,
            transcript=transcript,
            incongruence_data=incongruence
        )
        
        t_llm = time.time() - t_llm_start
        timestamps["llm_complete"] = datetime.utcnow().isoformat() + 'Z'
        
        # Emit THERAPEUTIC_RESPONSE_READY
        emit.emit_therapeutic_ready(
            job_id,
            strategy=therapeutic_advice.get('strategy_used', 'General'),
            advice=therapeutic_advice.get('advice', '')
        )
        
        # ========================================
        # 5. FINAL PAYLOAD
        # ========================================
        total_time = time.time() - start_time
        timestamps["job_complete"] = datetime.utcnow().isoformat() + 'Z'
        logger.info(f"JOB {job_id} FINISHED in {total_time:.1f}s")
        
        result = {
            "face_emotion_result": {
                 "dominant_face_emotion": dominant_face,
                 "frame_emotions": face_res.get("emotions", {}),
                 "advanced_action_units": {}
            },
            "audio_tone_emotion": {
                "predicted": predicted_audio,
                "probs": a_emo.get("probs", {}),
                "dimensional_metrics": a_dim
            },
            "transcript": transcript,
            "transcript_sentiment": {"score": compound, "primary_emotion": text_emo},
            "llm_analysis": {},
            "overall_emotion": fusion_result,
            "therapeutic_advice": therapeutic_advice,
            "performance": {
                "total_time_seconds": round(total_time, 1),
                "parallel_analysis_seconds": round(t_parallel, 1),
                "extraction_seconds": round(t_extract, 1),
                "fusion_seconds": round(t_fusion, 1),
                "llm_seconds": round(t_llm, 1)
            },
            "timestamps": timestamps
        }
        
        # Emit JOB_COMPLETE
        emit.emit_job_complete(job_id, {
            "total_time": round(total_time, 1),
            "emotion": fusion_result.get('overall_emotion', 'neutral')
        })
        
        return result

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        # Emit JOB_FAILED
        emit.emit_job_failed(job_id, str(e))
        raise e
    finally:
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir)

