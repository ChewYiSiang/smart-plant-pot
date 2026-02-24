import asyncio
import os
import sys
import time
import requests

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.transcription import TranscriptionService
from config import get_settings

async def test_google_connectivity():
    print("\n--- [Test 1: Google API Connectivity] ---")
    settings = get_settings()
    if not settings.GOOGLE_API_KEY:
        print("❌ FAILED: GOOGLE_API_KEY is missing in .env")
        return False
    print("✅ GOOGLE_API_KEY found.")
    return True

async def test_stt_isolation():
    print("\n--- [Test 2: STT Service Isolation] ---")
    stt = TranscriptionService()
    
    # Look for a sample wav file
    sample_file = None
    pot_dir = "audio_artifacts/s3_devkitc_plant_pot/uploads"
    if os.path.exists(pot_dir):
        files = [f for f in os.listdir(pot_dir) if f.endswith(".wav")]
        if files:
            sample_file = os.path.join(pot_dir, files[0])
    
    if not sample_file:
        print("⚠️ No existing recordings found in audio_artifacts. Please record a file or check the path.")
        return False

    print(f"Testing with sample: {sample_file} ({os.path.getsize(sample_file)} bytes)")
    try:
        start_time = time.time()
        transcript = await stt.transcribe(sample_file)
        duration = time.time() - start_time
        print(f"✅ STT Successful ({duration:.2f}s)")
        print(f"Result: '{transcript}'")
        return True
    except Exception as e:
        print(f"❌ STT Failed: {e}")
        return False

async def test_full_pipeline():
    print("\n--- [Test 3: Full Backend Pipeline] ---")
    url = "http://127.0.0.1:8000/v1/ingest"
    
    # Find a sample file for ingestion
    sample_file = None
    pot_dir = "audio_artifacts/s3_devkitc_plant_pot/uploads"
    if os.path.exists(pot_dir):
        files = [f for f in os.listdir(pot_dir) if f.endswith(".wav")]
        if files:
            sample_file = os.path.join(pot_dir, files[0])

    if not sample_file:
        print("⚠️ Skipping full pipeline test (no sample file).")
        return False

    print(f"Sending {sample_file} to {url}...")
    try:
        with open(sample_file, "rb") as f:
            files = {"audio": (os.path.basename(sample_file), f, "audio/wav")}
            params = {
                "device_id": "mic_test_device",
                "temperature": 25.0,
                "moisture": 50.0,
                "light": 80.0
            }
            response = requests.post(url, params=params, files=files, timeout=15)
            
        if response.status_code == 200:
            print("✅ Full Pipeline Success!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend returned error {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the backend server running on http://127.0.0.1:8000?")
        return False
    except Exception as e:
        print(f"❌ Pipeline Test Failed: {e}")
        return False

async def main():
    print("========================================")
    print("   Smart Plant Pot Mic Troubleshooter   ")
    print("========================================\n")
    
    conn_ok = await test_google_connectivity()
    if not conn_ok: return

    stt_ok = await test_stt_isolation()
    
    # Full pipeline test only if backend is likely up
    await test_full_pipeline()

    print("\n========================================")
    print("Troubleshooting complete.")
    print("If STT failed but connectivity is OK:")
    print("1. Check if the audio file is empty or corrupted.")
    print("2. Ensure your Windows Mic is granting permission to apps.")
    print("3. Try recording a wav file using 'Voice Recorder' and place it in audio_artifacts.")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(main())
