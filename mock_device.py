import requests
import json

BASE_URL = "http://localhost:8000"
API_KEY = "generate_a_secure_key_here" # Matches .env

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health Check: {response.json()}")

def test_ingest():
    headers = {"x-api-key": API_KEY}
    data = {
        "device_id": "pot_001",
        "temperature": 25.5,
        "moisture": 45.0,
        "light": 300.0,
        "event": "voice_query"
    }
    
    # Simulate multipart request without audio first
    response = requests.post(
        f"{BASE_URL}/v1/ingest",
        params=data,
        headers=headers
    )
    print(f"Ingest (No Audio): {response.status_code}, {response.json()}")

if __name__ == "__main__":
    test_health()
    test_ingest()
