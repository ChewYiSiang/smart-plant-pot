import requests
import time
import json

BASE_URL = "http://localhost:8000"
DEVICE_ID = "pot_simulator_001"
PHYSICAL_DEVICE_ID = "s3_devkitc_plant_pot"

def test_latency():
    # 1. Trigger low moisture event on simulator
    print(f"Triggering low moisture event on {DEVICE_ID}...")
    start_time = time.time()
    params = {
        "device_id": DEVICE_ID,
        "temperature": 25.0,
        "moisture": 10.0,
        "light": 50.0,
        "event": "low_moisture_alert"
    }
    
    response = requests.post(f"{BASE_URL}/v1/ingest", params=params)
    if response.status_code != 200:
        print(f"Error triggering event: {response.status_code}")
        return

    print("Event triggered. Polling for alert on physical device...")
    
    # 2. Poll for the alert on the physical device
    attempts = 0
    while attempts < 20:
        poll_response = requests.get(f"{BASE_URL}/v1/device/{PHYSICAL_DEVICE_ID}/poll")
        if poll_response.status_code == 200:
            data = poll_response.json()
            if data.get("notification_url"):
                latency = time.time() - start_time
                print(f"SUCCESS: Alert detected after {latency:.4f} seconds!")
                print(f"Poll data: {json.dumps(data, indent=2)}")
                return
        
        attempts += 1
        time.sleep(0.1) # Poll frequently for the test
    
    print("FAILED: Alert not detected within timeout.")

if __name__ == "__main__":
    test_latency()
