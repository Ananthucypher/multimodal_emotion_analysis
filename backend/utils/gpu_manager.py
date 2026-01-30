"""
GPU Context Manager for Tier 3 Dynamic Scheduling.
Manages VRAM allocation by swapping models between GPU and CPU.

Strategy:
1. Analysis Phase: Load Audio/Whisper models to GPU. Unload Ollama.
2. Therapy Phase: Load Ollama to GPU. Unload Audio/Whisper models (move to CPU).
"""
import torch
import gc
import logging
import requests
import time
from processors import audio_emotion, audio_dim, speech_whisper

logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
# Assuming we use the default model name from text_ollama, but hardcoded for unload
OLLAMA_MODEL = "llama3.1" 

class GPUContextManager:
    def __init__(self):
        self.has_gpu = torch.cuda.is_available()
        if not self.has_gpu:
            logger.warning("GPUContextManager: No GPU detected. Scheduling disabled.")

    def _empty_cache(self):
        """Force garbage collection and clear CUDA cache."""
        gc.collect()
        if self.has_gpu:
            torch.cuda.empty_cache()

    def unload_ollama(self):
        """Force Ollama to unload its model from VRAM."""
        try:
            # Setting keep_alive to 0 triggers immediate unload
            requests.post(OLLAMA_API_URL, json={
                "model": OLLAMA_MODEL,
                "keep_alive": 0
            }, timeout=5)
            logger.info("GPUContextManager: Requested Ollama unload.")
        except Exception as e:
            logger.warning(f"GPUContextManager: Failed to unload Ollama: {e}")

    def enter_analysis_mode(self):
        """
        Prepare GPU for Parallel Analysis (Face/Audio/Speech).
        Action: Unload Ollama, Move Analysis models to GPU.
        """
        if not self.has_gpu: return

        logger.info("=== GPU SCHEDULER: Enter Analysis Mode ===")
        
        # 1. Unload Ollama to free up VRAM
        self.unload_ollama()
        self._empty_cache()
        
        # 2. Move Analysis Models to GPU
        # We start with Audio/Speech as they benefit most from FP16 on GPU
        try:
            audio_emotion.set_device('cuda')
            audio_dim.set_device('cuda')
            speech_whisper.set_device('cuda')
            # Face is kept on CPU (Py-Feat) or managed internally
        except Exception as e:
            logger.error(f"Failed to move analysis models to GPU: {e}")

    def enter_therapy_mode(self):
        """
        Prepare GPU for Llama 3.1 Therapy Generation.
        Action: Move Analysis models to CPU, Free VRAM for Ollama.
        """
        if not self.has_gpu: return

        logger.info("=== GPU SCHEDULER: Enter Therapy Mode ===")
        
        # 1. Move Analysis Models to CPU to save VRAM
        try:
            audio_emotion.set_device('cpu')
            audio_dim.set_device('cpu')
            speech_whisper.set_device('cpu')
        except Exception as e:
            logger.error(f"Failed to move analysis models to CPU: {e}")
            
        # 2. Clear VRAM
        self._empty_cache()
        
        # 3. Ollama will automatically load into the free VRAM when queried

    def release_all(self):
        """Optional: Release everything to CPU/Unload at end of job."""
        if not self.has_gpu: return
        
        logger.info("=== GPU SCHEDULER: Release All ===")
        try:
            audio_emotion.set_device('cpu')
            audio_dim.set_device('cpu')
            speech_whisper.set_device('cpu')
            self.unload_ollama()
            self._empty_cache()
        except:
            pass

# Global instance
gpu_manager = GPUContextManager()
