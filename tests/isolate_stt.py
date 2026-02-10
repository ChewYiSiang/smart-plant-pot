import asyncio
import os
import sys

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.transcription import TranscriptionService
from config import get_settings

async def test_stt():
    settings = get_settings()
    print("Isolating STT Test...")
    stt = TranscriptionService()
    audio_path = "tests/debug_tts_output.wav"
    
    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found.")
        return

    print(f"File found ({os.path.getsize(audio_path)} bytes). Calling recognize...")
    try:
        # Pass a shorter timeout just for isolation
        transcript = await stt.transcribe(audio_path)
        print(f"Transcription Result: '{transcript}'")
    except Exception as e:
        print(f"Exception during transcribe: {e}")

if __name__ == "__main__":
    asyncio.run(test_stt())
