import asyncio
import os
import sys
from unittest import IsolatedAsyncioTestCase

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.transcription import TranscriptionService
from services.speech_synthesis import SpeechSynthesisService

class TestServices(IsolatedAsyncioTestCase):
    async def test_stt_and_tts_flow(self):
        stt = TranscriptionService()
        tts = SpeechSynthesisService()
        
        test_audio = "tests/sample_query.wav"
        output_audio = "tests/test_output.wav"
        
        # 1. Test STT (Requires FFmpeg and the sample file)
        if os.path.exists(test_audio):
            print("Testing Transcription...")
            text = await stt.transcribe(test_audio)
            print(f"Transcribed Text: {text}")
            self.assertIsInstance(text, str)
        else:
            print("Skipping STT test: tests/sample_query.wav not found.")

        # 2. Test TTS
        print("Testing Speech Synthesis...")
        result_path = await tts.synthesize("Hello, I am your plant.", output_audio)
        print(f"TTS saved to: {result_path}")
        self.assertIsNotNone(result_path)
        self.assertTrue(os.path.exists(result_path))
        
        # Cleanup
        if os.path.exists(output_audio):
            os.remove(output_audio)

if __name__ == "__main__":
    import unittest
    unittest.main()
