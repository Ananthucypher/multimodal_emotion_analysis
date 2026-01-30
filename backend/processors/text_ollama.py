import requests
import logging
import time

logger = logging.getLogger(__name__)

# Ollama runs locally on port 11434
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1"

def query_ollama(prompt, max_tokens=300, temperature=0.7, retries=2):
    """
    Send a prompt to the local Ollama Llama 3.1 instance.
    Returns generated text.
    """
    for attempt in range(retries + 1):
        try:
            payload = {
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_ctx": 1024  # Limit context window for speed
                }
            }
            
            response = requests.post(OLLAMA_URL, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            logger.info(f"Ollama response: {generated_text[:100]}...")
            return generated_text
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ollama attempt {attempt+1} failed: {e}")
            if attempt < retries:
                time.sleep(2)
                continue
            return f"[Ollama temporarily unavailable. Try again in a moment.]"
        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
            return f"[Error: {e}]"

def generate_therapeutic_response(emotion_data, transcript, incongruence, strategy_context):
    """
    Generate a therapeutic response using Llama 3.1.
    """
    
    # Build a clinical prompt - optimized for brevity and speed
    prompt = f"""You are a compassionate AI therapist assistant.
    
**Patient Input:**
- Emotion: {emotion_data.get('overall_emotion', 'unknown')} ({emotion_data.get('confidence', 0) * 100:.0f}%)
- Transcript: "{transcript if transcript else '[No speech]'}"
- Context: {incongruence.get('status', 'Normal')}

**Therapeutic Approach:** {strategy_context}

**Task:** Write a SINGLE, short paragraph (max 40 words). Validate their feeling and offer one quick tip.

Response:"""

    return query_ollama(prompt, max_tokens=100, temperature=0.7)
