from llama_cpp import Llama
from huggingface_hub import hf_hub_download
import logging
import os

logger = logging.getLogger(__name__)

# Config
REPO_ID = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
FILENAME = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
# Path relative to backend/processors/text_gguf.py -> backend/models
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

_llm = None

def get_llm():
    """Load Llama 3.1 GGUF model (Resident) with Self-Healing."""
    global _llm
    if _llm is None:
        model_path = os.path.join(MODEL_DIR, FILENAME)
        try:
            # 1. Download if missing
            if not os.path.exists(model_path):
                logger.info(f"Downloading {FILENAME} from HF...")
                os.makedirs(MODEL_DIR, exist_ok=True)
                model_path = hf_hub_download(
                    repo_id=REPO_ID, 
                    filename=FILENAME, 
                    local_dir=MODEL_DIR,
                    local_dir_use_symlinks=False
                )
            
            # 2. Try Loading
            logger.info(f"Loading Llama GGUF from {model_path}...")
            _llm = Llama(
                model_path=model_path,
                n_gpu_layers=-1, 
                n_ctx=2048,
                verbose=False
            )
            logger.info("Llama GGUF loaded successfully.")

        except ValueError as ve:
            # 3. Handle Corruption (Llama-cpp raises ValueError on bad file)
            logger.error(f"CORRUPT MODEL DETECTED: {ve}")
            logger.info("Deleting corrupt file and re-downloading...")
            if os.path.exists(model_path):
                os.remove(model_path)
            
            # Retry Download & Load once
            try:
                model_path = hf_hub_download(
                    repo_id=REPO_ID, 
                    filename=FILENAME, 
                    local_dir=MODEL_DIR,
                    local_dir_use_symlinks=False,
                    force_download=True
                )
                _llm = Llama(
                    model_path=model_path,
                    n_gpu_layers=-1, 
                    n_ctx=2048,
                    verbose=True
                )
                logger.info("Llama GGUF recovered successfully.")
            except Exception as e2:
                 logger.critical(f"Fatal LLM Error: {e2}")
                 raise e2

        except Exception as e:
            logger.error(f"Failed to load Llama GGUF: {e}")
            raise e
            
    return _llm

def generate_therapeutic_response(context_data):
    """
    Generate response using resident Llama 3.1.
    """
    try:
        llm = get_llm()
        
        # Construct Prompt
        transcript = context_data.get("transcript", "")
        # If no transcript, can't really do meaningful therapy
        if not transcript or len(transcript) < 5:
            return "I noticed you were quiet. I'm here if you want to talk."

        emotions = context_data.get("emotions", {})
        
        system_prompt = (
            "You are a compassionate clinical psychologist (CBT/DBT Expert). "
            "Analyze the user's situation based on their transcript and emotional state. "
            "Provide brief, actionable guidance. Do not verify you are an AI. "
            "Keep it under 100 words."
        )
        
        user_prompt = f"""
        Transcript: "{transcript}"
        Detected Emotions: {emotions}
        
        Provide therapeutic insight and one coping strategy.
        """
        
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        text = response['choices'][0]['message']['content']
        if not text:
             return "I'm listening, but having trouble formulating a response right now."
        return text
        
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return "I'm here to listen, but I'm having trouble processing right now. Please tell me more."
