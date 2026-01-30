import requests
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1"

def test_ollama_unload():
    print(f"--- Testing Ollama Unload on {MODEL_NAME} ---")
    
    # 1. Load Model
    print("1. Loading model with a prompt...")
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL_NAME,
            "prompt": "Hello",
            "stream": False
        })
        if response.status_code == 200:
            print("   Model loaded and responded.")
        else:
            print(f"   Failed to load: {response.text}")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return

    # 2. Wait a bit
    time.sleep(2)
    
    # 3. Unload Model
    print("2. Sending unload request (keep_alive=0)...")
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL_NAME,
            "keep_alive": 0
        })
        if response.status_code == 200:
            print("   Unload request sent successfully.")
        else:
            print(f"   Failed to send unload request: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    print("--- Test Complete (Check 'ollama ps' in another terminal to verify) ---")

if __name__ == "__main__":
    test_ollama_unload()
