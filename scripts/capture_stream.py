import requests
import time

def capture_stream():
    url = "http://localhost:8000/v1/ingest"
    params = {
        "device_id": "debug_device",
        "temperature": 25.0,
        "moisture": 50.0,
        "light": 500.0,
        "user_query": "Hello plant, tell me a short story."
    }
    
    print(f"Connecting to {url}...")
    try:
        with requests.post(url, params=params, stream=True, timeout=60) as r:
            print(f"Status: {r.status_code}")
            if r.status_code != 200:
                print(f"Error: {r.text}")
                return
                
            with open("captured_stream.wav", "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        print(f"Received {len(chunk)} bytes", end='\r')
            print("\nStream captured to captured_stream.wav")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    capture_stream()
