import asyncio
import os
import sys
from datetime import datetime

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.transcription import TranscriptionService
from services.speech_synthesis import SpeechSynthesisService
from config import get_settings

async def debug_flow():
    settings = get_settings()
    print("--- STT/TTS Debug Tool ---")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"API Key present: {'Yes' if settings.GOOGLE_API_KEY else 'No'}")
    
    stt = TranscriptionService()
    tts = SpeechSynthesisService()
    
    test_text = "I am a helpful little plant in a ceramic pot. Testing one two three."
    output_audio = "tests/debug_tts_output.wav"
    
    print(f"\n1. Testing TTS (Text -> Audio)...")
    print(f"Target: {test_text}")
    try:
        path = await tts.synthesize(test_text, output_audio)
        print(f"SUCCESS: Audio saved to {path} ({os.path.getsize(path)} bytes)")
    except Exception as e:
        print(f"FAILURE in TTS: {e}")
        return

    print(f"\n2. Testing STT (Audio -> Text)...")
    print(f"Processing newly created file: {output_audio}")
    try:
        start_time = datetime.now()
        transcript = await stt.transcribe(output_audio)
        duration = (datetime.now() - start_time).total_seconds()
        
        if transcript:
            print(f"SUCCESS: Transcription took {duration:.2f}s")
            print(f"Result: \"{transcript}\"")
            if test_text.lower().replace(".", "").replace(",", "") in transcript.lower().replace(".", "").replace(",", ""):
                print("MATCH: Transcription correctly matches the source!")
            else:
                print("PARTIAL MATCH: Transcription differs slightly but worked.")
        else:
            print(f"FAILURE: STT returned an empty string after {duration:.2f}s")
            print("Check your RecognitionConfig and audio file format (16kHz WAV expected).")
    except Exception as e:
        print(f"FAILURE in STT: {e}")

if __name__ == "__main__":
    if not os.path.exists("tests"):
        os.makedirs("tests")
    asyncio.run(debug_flow())
