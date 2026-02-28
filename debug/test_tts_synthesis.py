import asyncio
import os
from services.speech_synthesis import SpeechSynthesisService
from config import get_settings

async def test_synthesis():
    print("Starting TTS Test...")
    tts = SpeechSynthesisService()
    text = "Hello! I am your friendly plant pot. Your moisture level is currently doing great."
    
    try:
        print(f"Testing synthesize_stream with: {text}")
        audio_bytes = await tts.synthesize_stream(text)
        if audio_bytes:
            print(f"SUCCESS: Received {len(audio_bytes)} bytes of audio.")
            with open("test_voice_output.mp3", "wb") as f:
                f.write(audio_bytes)
            print("Audio saved to test_voice_output.mp3")
        else:
            print("FAILURE: Received 0 bytes of audio.")
    except Exception as e:
        print(f"ERROR during synthesis: {e}")

if __name__ == "__main__":
    asyncio.run(test_synthesis())
