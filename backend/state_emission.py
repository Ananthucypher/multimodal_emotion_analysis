"""
MIRO State Emission System
==========================
Provides Redis Pub/Sub based state emission for progressive result delivery.
Part of P0 implementation for SSE streaming architecture.
"""
import json
import redis
import os
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

# Redis connection
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
_redis_client = None


def get_redis_client():
    """Get or create Redis client for pub/sub."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


class JobState(str, Enum):
    """Progressive state definitions per execution blueprint."""
    JOB_STARTED = "JOB_STARTED"
    EXTRACTION_COMPLETE = "EXTRACTION_COMPLETE"
    FACE_READY = "FACE_READY"
    AUDIO_READY = "AUDIO_READY"
    TRANSCRIPT_READY = "TRANSCRIPT_READY"
    PRIMARY_EMOTION_READY = "PRIMARY_EMOTION_READY"
    INCONGRUENCE_READY = "INCONGRUENCE_READY"
    THERAPEUTIC_RESPONSE_READY = "THERAPEUTIC_RESPONSE_READY"
    JOB_COMPLETE = "JOB_COMPLETE"
    JOB_FAILED = "JOB_FAILED"


# Progress percentages for each state
STATE_PROGRESS = {
    JobState.JOB_STARTED: 5,
    JobState.EXTRACTION_COMPLETE: 15,
    JobState.FACE_READY: 35,
    JobState.AUDIO_READY: 45,
    JobState.TRANSCRIPT_READY: 55,
    JobState.PRIMARY_EMOTION_READY: 65,
    JobState.INCONGRUENCE_READY: 75,
    JobState.THERAPEUTIC_RESPONSE_READY: 95,
    JobState.JOB_COMPLETE: 100,
    JobState.JOB_FAILED: 100,
}


@dataclass
class StateUpdate:
    """Contract for all state emissions."""
    job_id: str
    state: str
    timestamp: str
    payload: Dict[str, Any]
    progress_percent: int
    is_terminal: bool
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def create(cls, job_id: str, state: JobState, payload: Optional[Dict] = None) -> 'StateUpdate':
        return cls(
            job_id=job_id,
            state=state.value,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            payload=payload or {},
            progress_percent=STATE_PROGRESS.get(state, 0),
            is_terminal=state in (JobState.JOB_COMPLETE, JobState.JOB_FAILED)
        )


def get_channel_name(job_id: str) -> str:
    """Get Redis channel name for a job."""
    return f"miro:job:{job_id}:state"


def emit_state(job_id: str, state: JobState, payload: Optional[Dict] = None) -> bool:
    """
    Emit a state update via Redis Pub/Sub.
    
    Args:
        job_id: The job identifier
        state: The JobState enum value
        payload: Optional state-specific data
        
    Returns:
        True if published successfully, False otherwise
    """
    try:
        client = get_redis_client()
        update = StateUpdate.create(job_id, state, payload)
        channel = get_channel_name(job_id)
        
        # Publish to channel
        subscribers = client.publish(channel, update.to_json())
        logger.info(f"Emitted {state.value} for job {job_id} ({subscribers} subscribers)")
        
        # Also store latest state in Redis for late joiners
        client.setex(
            f"miro:job:{job_id}:latest",
            3600,  # 1 hour TTL
            update.to_json()
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to emit state {state.value} for job {job_id}: {e}")
        return False


def subscribe_to_job(job_id: str):
    """
    Subscribe to job state updates.
    Yields StateUpdate objects as they arrive.
    """
    client = redis.from_url(REDIS_URL, decode_responses=True)
    pubsub = client.pubsub()
    channel = get_channel_name(job_id)
    
    pubsub.subscribe(channel)
    logger.info(f"Subscribed to {channel}")
    
    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                yield data
                
                # Stop if terminal state
                if data.get('is_terminal'):
                    break
                    
    finally:
        pubsub.unsubscribe(channel)
        pubsub.close()


def get_latest_state(job_id: str) -> Optional[Dict]:
    """Get the latest state for a job (for late joiners)."""
    try:
        client = get_redis_client()
        data = client.get(f"miro:job:{job_id}:latest")
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get latest state for {job_id}: {e}")
        return None


# Convenience functions for common state emissions
def emit_job_started(job_id: str):
    return emit_state(job_id, JobState.JOB_STARTED, {"message": "Processing started"})


def emit_extraction_complete(job_id: str, duration_seconds: float):
    return emit_state(job_id, JobState.EXTRACTION_COMPLETE, {
        "duration_seconds": round(duration_seconds, 1)
    })


def emit_face_ready(job_id: str, dominant_emotion: str, confidence: float, trajectory: list = None):
    return emit_state(job_id, JobState.FACE_READY, {
        "dominant_emotion": dominant_emotion,
        "confidence": round(confidence, 2),
        "trajectory": trajectory or []
    })


def emit_audio_ready(job_id: str, predicted: str, confidence: float, probs: dict = None):
    return emit_state(job_id, JobState.AUDIO_READY, {
        "predicted": predicted,
        "confidence": round(confidence, 2),
        "probs": probs or {}
    })


def emit_transcript_ready(job_id: str, text: str):
    return emit_state(job_id, JobState.TRANSCRIPT_READY, {
        "text": text[:500] if text else "",  # Truncate for SSE payload
        "word_count": len(text.split()) if text else 0
    })


def emit_primary_emotion_ready(job_id: str, emotion: str, confidence: float):
    return emit_state(job_id, JobState.PRIMARY_EMOTION_READY, {
        "emotion": emotion,
        "confidence": round(confidence, 2)
    })


def emit_incongruence_ready(job_id: str, incongruence_data: dict):
    return emit_state(job_id, JobState.INCONGRUENCE_READY, incongruence_data)


def emit_therapeutic_ready(job_id: str, strategy: str, advice: str):
    return emit_state(job_id, JobState.THERAPEUTIC_RESPONSE_READY, {
        "strategy": strategy,
        "advice": advice[:500] if advice else ""  # Truncate for SSE
    })


def emit_job_complete(job_id: str, result_summary: dict = None):
    return emit_state(job_id, JobState.JOB_COMPLETE, {
        "result_url": f"/status/{job_id}",
        "summary": result_summary or {}
    })


def emit_job_failed(job_id: str, error: str, partial_results: dict = None):
    return emit_state(job_id, JobState.JOB_FAILED, {
        "error": error,
        "partial_results": partial_results or {}
    })
