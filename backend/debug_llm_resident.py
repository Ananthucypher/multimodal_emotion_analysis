import logging
import sys
import os

# Ensure backend can be imported
sys.path.append(os.path.join(os.getcwd(), 'backend'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugLLM")

def debug_llm():
    print("--- Debugging Resident LLM ---")
    try:
        from processors import text_gguf
        
        # Test 1: Load Model
        print("[1] Loading Model...")
        llm = text_gguf.get_llm()
        if llm:
            print("✅ Model Loaded.")
        else:
            print("❌ Model Load Failed (None).")
            return

        # Test 2: Generate
        print("[2] Generating Response...")
        context = {
            "transcript": "I tried so hard, but it just didn't work out. I feel like giving up.",
            "emotions": {
                "face": "sad",
                "voice": "sad",
                "incongruence": {}
            }
        }
        
        response = text_gguf.generate_therapeutic_response(context)
        print(f"\n[Raw Response]: '{response}'")
        
        if response and len(response) > 5:
            print("✅ Generation Success.")
        else:
            print("❌ Empty or invalid response.")

    except Exception as e:
        print(f"❌ CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_llm()
