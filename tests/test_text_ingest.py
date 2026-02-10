import requests

def test_text_ingest():
    url = "http://localhost:8000/v1/ingest"
    params = {
        "device_id": "test_device_001",
        "temperature": 25.0,
        "moisture": 60.0,
        "light": 80.0,
        "user_query": "Hello plant, tell me a joke."
    }
    
    print(f"Testing ingestion with text query: {params['user_query']}")
    try:
        response = requests.post(url, params=params)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"User Query returned: '{data.get('user_query')}'")
        print(f"Reply Text: '{data.get('reply_text')}'")
        
        if data.get('user_query') == params['user_query']:
            print("SUCCESS: Text query received and echoed correctly.")
        else:
            print(f"FAILURE: Expected '{params['user_query']}', got '{data.get('user_query')}'")
            
    except Exception as e:
        print(f"Error connecting to server: {e}")
        print("Make sure the server is running on http://localhost:8000")

if __name__ == "__main__":
    test_text_ingest()
