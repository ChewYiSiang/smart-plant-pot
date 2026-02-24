import requests
import json

def test_ingest():
    url = "http://127.0.0.1:8000/v1/ingest"
    params = {
        "device_id": "pot_simulator_001",
        "temperature": 22.0,
        "moisture": 35.0,
        "light": 60.0,
        "event": "test"
    }
    
    print(f"Sending ingest request to {url}...")
    try:
        # We use a timeout to avoid hanging if the server is stuck
        response = requests.post(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
        print("Note: If the server is not running, this test will fail. Make sure to run 'python main.py' first.")

if __name__ == "__main__":
    test_ingest()
