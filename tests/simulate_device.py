import requests
import os
import time

# --- Configuration ---
BASE_URL = "http://localhost:8000"
SAMPLE_AUDIO = "tests/sample_query.wav" # Ensure this file exists

def simulate_interaction(device_id="pot_001", has_audio=True, is_wake_word=False):
    print(f"\n--- Simulating Interaction for {device_id} (Wake Word: {is_wake_word}) ---")
    headers = {}
    
    event = "periodic_update"
    if is_wake_word:
        event = "wake_word"
    elif has_audio:
        event = "voice_query"
        
    data = {
        "device_id": device_id,
        "temperature": 27.5,
        "moisture": 35.0, # Thirsty
        "light": 500.0,
        "event": event
    }
    
    files = {}
    if has_audio and os.path.exists(SAMPLE_AUDIO):
        files = {"audio": (os.path.basename(SAMPLE_AUDIO), open(SAMPLE_AUDIO, "rb"), "audio/wav")}
    
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/v1/ingest",
        params=data,
        files=files,
        headers=headers
    )
    latency = time.time() - start_time
    
    if response.status_code == 200:
        res_data = response.json()
        print(f"Success! Latency: {latency:.2f}s")
        print(f"Reply: {res_data['reply_text']}")
        print(f"Mood: {res_data['display']['mood']}")
        print(f"Audio URL: {res_data['audio_url']}")
    else:
        print(f"Failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # Test health first
    try:
        health = requests.get(f"{BASE_URL}/health").json()
        print(f"Server Status: {health['status']}")
        
        # Run simulations
        simulate_interaction("pot_001", has_audio=True)
        simulate_interaction("pot_001", has_audio=True, is_wake_word=True)
    except Exception as e:
        print(f"Error connecting to server: {e}")
