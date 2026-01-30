"""
MIRO Therapeutic Advisor with Safety Layer
===========================================
P0 Implementation: Integrates crisis detection and therapeutic verification.
"""
import json
import os
import logging
from processors import text_ollama
import safety_layer

logger = logging.getLogger(__name__)

# Load knowledge base
STRATEGIES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "strategies.json")
_strategies = None

def load_strategies():
    """Load therapeutic strategies from JSON knowledge base."""
    global _strategies
    if _strategies is None:
        try:
            with open(STRATEGIES_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _strategies = data.get('strategies', [])
                logger.info(f"Loaded {len(_strategies)} therapeutic strategies")
        except Exception as e:
            logger.error(f"Failed to load strategies: {e}")
            _strategies = []
    return _strategies

def retrieve_strategy(emotion, incongruence_data):
    """
    Retrieve the most relevant therapeutic strategy based on:
    - Detected emotion
    - Incongruence status
    
    This is a simple rule-based retriever (can be upgraded to embeddings later).
    """
    strategies = load_strategies()
    
    # Determine condition
    if incongruence_data.get('is_incongruent'):
        condition = 'high_incongruence'
    elif incongruence_data.get('status') == 'Potential Masking':
        condition = 'potential_masking'
    elif incongruence_data.get('status') == 'Potential Mismatch':
        condition = 'potential_mismatch'
    else:
        condition = 'congruent'
    
    # Filter strategies
    candidates = []
    for strategy in strategies:
        # Check if emotion matches
        if emotion.lower() in strategy['triggers'] or 'any' in strategy['triggers']:
            # Check if condition matches
            if condition in strategy['conditions'] or 'any' in strategy.get('conditions', []):
                candidates.append(strategy)
    
    # Return best match (first for now, could rank by priority)
    if candidates:
        selected = candidates[0]
        logger.info(f"Selected strategy: {selected['name']}")
        return selected
    
    # Fallback
    return {
        "name": "General Support",
        "prompt_context": "Provide general emotional support and validation."
    }

def generate_therapeutic_advice(overall_emotion_data, transcript, incongruence_data):
    """
    Main RAG function with Safety Layer: Retrieve strategy + Generate advice + Verify.
    
    Safety checks:
    1. Crisis detection on transcript
    2. Therapeutic verification on LLM response
    
    Returns dict with:
    - strategy_used: Name of technique
    - advice: Generated therapeutic response from Llama 3.1
    - safety_verified: Whether response passed safety checks
    - crisis_detected: Crisis detection result
    """
    try:
        # Extract emotion
        emotion = overall_emotion_data.get('overall_emotion', 'neutral')
        
        # ========================================
        # SAFETY CHECK 1: Crisis Detection
        # ========================================
        crisis_result = safety_layer.detect_crisis(transcript)
        
        if crisis_result.level == "CRITICAL":
            # Critical crisis - override with crisis resources
            logger.warning(f"CRITICAL CRISIS DETECTED: {crisis_result.matched_keyword}")
            crisis_response = safety_layer.get_crisis_response(crisis_result)
            return {
                "strategy_used": "Crisis Support",
                "technique": "Crisis Intervention",
                "advice": crisis_response["message"],
                "crisis_detected": crisis_result.to_dict(),
                "safety_verified": True,
                "resources": crisis_response.get("resources", {})
            }
        
        # ========================================
        # RETRIEVE STRATEGY
        # ========================================
        strategy = retrieve_strategy(emotion, incongruence_data)
        
        # ========================================
        # GENERATE LLM RESPONSE
        # ========================================
        raw_advice = text_ollama.generate_therapeutic_response(
            emotion_data=overall_emotion_data,
            transcript=transcript,
            incongruence=incongruence_data,
            strategy_context=strategy.get('prompt_context', '')
        )
        
        # ========================================
        # SAFETY CHECK 2: Therapeutic Verification
        # ========================================
        safe_advice, safety_metadata = safety_layer.apply_safety_filter(
            transcript=transcript,
            llm_response=raw_advice
        )
        
        result = {
            "strategy_used": strategy.get('name', 'Unknown'),
            "technique": strategy.get('technique', 'General'),
            "advice": safe_advice,
            "safety_verified": True,
            "safety_metadata": safety_metadata
        }
        
        # Add crisis info if HIGH level detected
        if crisis_result.level == "HIGH":
            result["crisis_detected"] = crisis_result.to_dict()
        
        return result
        
    except Exception as e:
        logger.error(f"Therapeutic advice generation failed: {e}", exc_info=True)
        return {
            "strategy_used": "Error",
            "technique": "N/A",
            "advice": "I want to support you, but I'm having trouble generating a response right now. If you're struggling, please consider reaching out to someone you trust.",
            "safety_verified": False
        }

