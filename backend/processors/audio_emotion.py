"""
Audio Emotion Recognition using Hugging Face Speech Emotion Recognition Model.
Replaces the legacy LSTM model with a state-of-the-art transformer.
"""
import torch
import torchaudio
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Use a pre-trained speech emotion recognition model
MODEL_NAME = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"

_processor = None
_model = None
_device = None

# Emotion labels from this model
# Corrected: 8 classes (0..7)
EMOTION_LABELS = ["angry", "calm", "disgust", "fear", "happy", "neutral", "sad", "surprise"]

def get_audio_emotion_model():
    """Load the speech emotion recognition model (lazy loading)."""
    global _processor, _model, _device
    
    if _model is None:
        logger.info(f"Loading Audio Emotion Model: {MODEL_NAME}")
        try:
            from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
            
            _processor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_NAME)
            _model = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_NAME)
            
            # Use GPU if available (FP32 ONLY - disable FP16 due to device-side assert errors)
            _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            _model = _model.to(_device)
            # Remove .half() - keep float32 for stability
            _model.eval()
            
            logger.info(f"Audio Emotion Model loaded on {_device} (FP32)")
        except Exception as e:
            logger.error(f"Failed to load audio emotion model: {e}")
            raise e
    
    return _processor, _model, _device

def set_device(target_device):
    """Move model to specified device (cpu/cuda) to manage VRAM."""
    global _model, _device
    if _model is not None:
        _device = torch.device(target_device)
        _model = _model.to(_device)
        # Always use float32 for stability
        _model.float() 
        logger.info(f"Audio Emotion Model moved to {target_device}")
    else:
        logger.warning("Audio Emotion Model not loaded, cannot move device.")

def analyze_audio_emotion(audio_path):
    # ...
    try:
        processor, model, device = get_audio_emotion_model()
        
        # Load audio using torchaudio
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Resample to 16000Hz (Required for Wav2Vec2)
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
            waveform = resampler(waveform)
            sample_rate = 16000
        
        # Prepare input
        inputs = processor(
            waveform.squeeze().numpy(), 
            sampling_rate=16000, 
            return_tensors="pt",
            padding=True
        )
        
        # Move to device (ensure float32)
        if device.type == 'cuda':
            inputs = {k: v.to(device).float() for k, v in inputs.items()}
        else:
            inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Inference
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
        
        # Get predicted emotion
        predicted_idx = int(np.argmax(probs))
        predicted_emotion = EMOTION_LABELS[predicted_idx]
        
        # Build probability dictionary
        probs_dict = {EMOTION_LABELS[i]: float(probs[i]) for i in range(len(EMOTION_LABELS))}
        
        # Also return simplified 4-class for backward compatibility
        simplified = {
            "happy": probs_dict.get("happy", 0) + probs_dict.get("surprise", 0) * 0.5,
            "sad": probs_dict.get("sad", 0) + probs_dict.get("disgust", 0) * 0.5,
            "angry": probs_dict.get("angry", 0) + probs_dict.get("disgust", 0) * 0.5,
            "neutral": probs_dict.get("neutral", 0) + probs_dict.get("surprise", 0) * 0.5,
            "fear": probs_dict.get("fear", 0)
        }
        
        # Normalize simplified
        total = sum(simplified.values())
        if total > 0:
            simplified = {k: v/total for k, v in simplified.items()}
        
        logger.info(f"Audio emotion detected: {predicted_emotion} ({probs[predicted_idx]:.2%})")
        
        return {
            "predicted": predicted_emotion,
            "confidence": float(probs[predicted_idx]),
            "probs": simplified,
            "detailed_probs": probs_dict,
            "model": "wav2vec2-ser"
        }
        
    except Exception as e:
        logger.error(f"Audio emotion analysis failed: {e}", exc_info=True)
        return {
            "predicted": "neutral",
            "confidence": 0.0,
            "probs": {"neutral": 0.25, "happy": 0.25, "sad": 0.25, "angry": 0.25},
            "error": str(e)
        }
