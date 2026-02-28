import requests
import time
import os

def test_stt_streaming():
    audio_file = "audio_artifacts/pot_simulator_001/uploads/1770733730.wav"
    if not os.path.exists(audio_file):
        print(f"Error: {audio_file} not found")
        return

    url = "http://localhost:8000/v1/ingest"
    params = {
        "device_id": "test_device_stt",
        "temperature": 25.0,
        "moisture": 50.0,
        "light": 500.0
    }
    
    print(f"Connecting to {url} with audio {audio_file}...")
    start_time = time.time()
    try:
        with open(audio_file, "rb") as f:
            files = {"audio": ("test.wav", f, "audio/wav")}
            with requests.post(url, params=params, files=files, stream=True, timeout=60) as r:
                print(f"Response Status: {r.status_code}")
                
                if r.status_code != 200:
                    print(f"Error Body: {r.text}")
                    return

                iterator = r.iter_content(chunk_size=1024)
                try:
                    first_chunk = next(iterator)
                    ttfb = time.time() - start_time
                    print(f"Time to First Byte (TTFB): {ttfb:.4f} seconds")
                    
                    if ttfb < 1.0:
                        print("PASS: TTFB is under 1 second (Backchannel worked during STT!).")
                    else:
                        print(f"FAIL: TTFB is {ttfb:.4f}s. Backchannel did not play immediately.")
                    
                    byte_count = len(first_chunk)
                    for chunk in iterator:
                        byte_count += len(chunk)
                    
                    total_time = time.time() - start_time
                    print(f"Stream complete. Total bytes: {byte_count}. Total time: {total_time:.4f}s")
                except StopIteration:
                     print("ERROR: Stream was empty!")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_stt_streaming()
