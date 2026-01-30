from transformers import Wav2Vec2Processor, Wav2Vec2ForSequenceClassification
import torch
import librosa
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Model for Dimensional Emotion (Arousal, Dominance, Valence)
MODEL_NAME = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"

_processor = None
_model = None

def get_audio_model():
    global _processor, _model
    if _model is None:
        logger.info(f"Loading Wav2Vec2 Dimensional Model: {MODEL_NAME}")
        try:
            _processor = Wav2Vec2Processor.from_pretrained(MODEL_NAME)
            _model = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_NAME)
            
            # Use GPU if available (FP32 ONLY - disable FP16 due to device-side assert errors)
            _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            _model = _model.to(_device)
            # Remove .half() - keep float32
            
            _model.eval() 
            logger.info(f"Wav2Vec2 loaded successfully on {_device} (FP32)")
        except Exception as e:
            logger.error(f"Failed to load Wav2Vec2: {e}")
            raise e
    return _processor, _model

# Alias for preloading
get_dimensional_model = get_audio_model

def set_device(target_device):
    """Move model to specified device (cpu/cuda) to manage VRAM."""
    global _model
    if _model is not None:
        device = torch.device(target_device)
        _model = _model.to(device)
        # Always use float32
        _model.float()
        logger.info(f"Audio Dimensional Model moved to {target_device}")
    else:
        logger.warning("Audio Dimensional Model not loaded, cannot move device.")

def analyze_audio_dimensional(audio_path):
    """
    Analyze audio for dimensional emotion (Arousal, Dominance, Valence).
    Input: Audio file path
    Output: Dict with scores
    """
    try:
        processor, model = get_audio_model()
        
        # Load audio at 16000Hz (Required for Wav2Vec)
        # Limit duration to avoid OOM on local cpu? 
        # Let's take up to 60 seconds for now, or chunk.
        y, sr = librosa.load(audio_path, sr=16000, duration=60)
        
        if len(y) == 0:
            return {"error": "Empty audio"}

        # Prepare input
        inputs = processor(y, sampling_rate=16000, return_tensors="pt", padding=True)
        
        # Move to device (ensure float32)
        device = next(model.parameters()).device
        
        if device.type == 'cuda':
            inputs = {k: v.to(device).float() for k, v in inputs.items()}
        else:
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
        with torch.no_grad():
            logits = model(**inputs).logits
            
        # Output format: [arousal, dominance, valence] for this specific model
        scores = logits[0].float().cpu().numpy() # Cast back to float for numpy safety
        
        return {
            "arousal": float(scores[0]),
            "dominance": float(scores[1]),
            "valence": float(scores[2]), 
            "model": MODEL_NAME
        }
    except Exception as e:
        logger.error(f"Phase 2 Audio Analysis Failed: {e}", exc_info=True)
        return {"error": str(e)}
