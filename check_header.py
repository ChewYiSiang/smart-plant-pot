import requests

def check_header():
    url = "http://localhost:8000/v1/ingest"
    params = {
        "device_id": "test_device",
        "temperature": 25.0,
        "moisture": 50.0,
        "light": 500.0,
        "user_query": "Test"
    }
    
    print(f"Connecting to {url}...")
    try:
        with requests.post(url, params=params, stream=True, timeout=10) as r:
            first_chunks = r.iter_content(chunk_size=44)
            header = next(first_chunks)
            print(f"First 44 bytes: {header}")
            if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                print("PASS: Valid WAV header detected!")
            else:
                print("FAIL: No WAV header at start.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_header()
