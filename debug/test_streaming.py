import requests
import time
import os

def test_streaming():
    with open("streaming_result.txt", "w") as f:
        url = "http://localhost:8000/v1/ingest"
        params = {
            "device_id": "test_device",
            "temperature": 25.0,
            "moisture": 50.0,
            "light": 500.0,
            "user_query": "What is your name?"
        }
        
        f.write(f"Connecting to {url}...\n")
        start_time = time.time()
        try:
            # stream=True is key
            with requests.post(url, params=params, stream=True, timeout=30) as r:
                f.write(f"Response Status: {r.status_code}\n")
                
                if r.status_code != 200:
                    f.write(f"Error Body: {r.text}\n")
                    return

                # Check Time to First Byte (TTFB)
                # accessing r.iter_content triggers the read
                iterator = r.iter_content(chunk_size=1024)
                try:
                    first_chunk = next(iterator)
                    ttfb = time.time() - start_time
                    f.write(f"Time to First Byte (TTFB): {ttfb:.4f} seconds\n")
                    
                    # Continue reading the rest
                    byte_count = len(first_chunk)
                    chunk_count = 1
                    
                    for chunk in iterator:
                        byte_count += len(chunk)
                        chunk_count += 1
                    
                    total_time = time.time() - start_time
                    f.write(f"Stream complete. Total bytes: {byte_count}. Total time: {total_time:.4f}s\n")
                    
                    if ttfb < 1.0:
                        f.write("PASS: TTFB is under 1 second (Backchannel worked).\n")
                    else:
                        f.write("WARN: TTFB is high. Backchannel might be missing or slow.\n")
                except StopIteration:
                     f.write("ERROR: Stream was empty!\n")

        except Exception as e:
            f.write(f"ERROR: {e}\n")

if __name__ == "__main__":
    test_streaming()
