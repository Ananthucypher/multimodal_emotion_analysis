import os
import logging
from huggingface_hub import hf_hub_download
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Setup")

def download_models():
    print("\n=== MIRO Phase 6 Setup: Downloading Models ===\n")
    
    # 1. Download Llama 3.1 GGUF
    print("1. Downloading Llama 3.1 8B (Q4_K_M GGUF)...")
    print("   Note: This file is ~5GB. Please wait.")
    
    REPO_ID = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
    FILENAME = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    # Path relative to backend/download_models.py -> backend/models
    MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    try:
        path = hf_hub_download(
            repo_id=REPO_ID, 
            filename=FILENAME, 
            local_dir=MODEL_DIR,
            local_dir_use_symlinks=False
        )
        print(f"   ✅ Llama ready at: {path}")
    except Exception as e:
        print(f"   ❌ Llama download failed: {e}")
        return

    # 2. Download Faster-Whisper (INT8)
    print("\n2. Pre-caching Faster-Whisper (Small/INT8)...")
    try:
        # Initializing the model triggers the download
        model = WhisperModel("small", device="cpu", compute_type="int8", download_root=os.path.join(MODEL_DIR, "whisper"))
        print("   ✅ Whisper ready.")
    except Exception as e:
         print(f"   ❌ Whisper download failed: {e}")

    print("\n=== Setup Complete! You can now start the Celery Worker. ===")

if __name__ == "__main__":
    download_models()
