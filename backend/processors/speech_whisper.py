import whisper
import logging
import torch
import warnings

# Suppress FP16 warning on CPU
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

logger = logging.getLogger(__name__)

# Model Size: 'tiny', 'base', 'small', 'medium', 'large'
# 'small' is a great balance for local CPU (approx 240MB - 500MB)
MODEL_SIZE = "small"

_model = None

def get_whisper_model():
    """Alias for preloading compatibility."""
    global _model
    if _model is None:
        logger.info(f"Loading OpenAI Whisper model ('{MODEL_SIZE}')...")
        try:
            _model = whisper.load_model(MODEL_SIZE)
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")
            raise e
    return _model

# Alias for backward compatibility
get_whisper = get_whisper_model

def set_device(target_device):
    """Move model to specified device (cpu/cuda) to manage VRAM."""
    global _model
    if _model is not None:
        device = torch.device(target_device)
        _model = _model.to(device)
        # Whisper automatically handles fp16/float32 switch during inference based on device
        logger.info(f"Whisper Model moved to {target_device}")
    else:
        logger.warning("Whisper Model not loaded, cannot move device.")

def transcribe_with_whisper(audio_path):
    """
    Transcribe audio using local Whisper model.
    Returns: Text string
    """
    if not audio_path: 
        return ""
        
    try:
        model = get_whisper()
        
        # Transcribe
        # Enable FP16 if CUDA is available for speedup (Tier 2 Optimization)
        use_fp16 = torch.cuda.is_available()
        result = model.transcribe(audio_path, fp16=use_fp16)
        
        text = result.get('text', '').strip()
        logger.info(f"Whisper transcription: {text[:50]}...")
        return text

    except Exception as e:
        logger.error(f"Whisper Transcription Error: {e}", exc_info=True)
        return ""
