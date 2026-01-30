from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

# Using Flan-T5-Base (Balanced for CPU/Performance)
MODEL_NAME = "google/flan-t5-base"

_pipeline = None

def get_llm():
    global _pipeline
    if _pipeline is None:
        logger.info(f"Loading Local LLM ({MODEL_NAME})...")
        try:
            # text2text-generation pipeline covers T5 family
            _pipeline = pipeline("text2text-generation", model=MODEL_NAME)
            logger.info("Local LLM loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")
            raise e
    return _pipeline

def analyze_sentiment_llm(text):
    """
    Analyze text nuance using Flan-T5.
    Returns generated analysis string.
    """
    if not text or not text.strip():
        return {"analysis": "No text provided"}

    try:
        llm = get_llm()
        
        # Simple zero-shot prompt
        prompt = f"Analyze the emotional tone and underlying sentiment of this text: '{text}'"
        
        # Generate
        output = llm(prompt, max_length=128, do_sample=False)
        result_text = output[0]['generated_text']
        
        return {
            "model": MODEL_NAME,
            "analysis": result_text
        }
    except Exception as e:
        logger.error(f"LLM Analysis Error: {e}")
        return {"error": str(e)}
