from faster_whisper import WhisperModel
import logging
import torch
import os

logger = logging.getLogger(__name__)

# Replaces the standard openai-whisper model
MODEL_SIZE = "small" # or 'base' for even faster speed
_model = None

def get_whisper_model():
    """Load Faster-Whisper model (Lazy Load)."""
    global _model
    if _model is None:
        logger.info(f"Loading Faster-Whisper ({MODEL_SIZE})...")
        try:
            # compute_type="int8" is the key to speed on consumer GPU or CPU
            # device="cuda" if available, else "cpu"
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "int8" if device == "cuda" else "int8" 
            
            _model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
            logger.info(f"Faster-Whisper loaded on {device} ({compute_type})")
        except Exception as e:
            logger.error(f"Failed to load Faster-Whisper: {e}")
            raise e
    return _model

def transcribe_audio(audio_path):
    """
    Transcribe audio using Faster-Whisper.
    Returns: Text string.
    """
    try:
        model = get_whisper_model()
        logger.info(f"Transcribing {audio_path}...")
        
        # segments is a generator
        segments, info = model.transcribe(audio_path, beam_size=5)
        
        transcript = ""
        for segment in segments:
            transcript += segment.text + " "
            
        return transcript.strip()
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return ""

# For compatibility with GPUContextManager (though faster-whisper manages its own memory mostly)
def set_device(device_name):
    # Faster-Whisper makes it hard to move models after init. 
    # Usually we just unload it.
    pass
