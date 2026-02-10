import os
from google.cloud import speech
from google.api_core.client_options import ClientOptions
from config import get_settings

class TranscriptionService:
    def __init__(self):
        self.settings = get_settings()
        # Initializing with API Key via ClientOptions
        options = ClientOptions(api_key=self.settings.GOOGLE_API_KEY)
        self.client = speech.SpeechAsyncClient(client_options=options)

    async def transcribe(self, audio_file_path: str) -> str:
        """Transcribes audio file to text using Google Cloud Speech-to-Text."""
        if not os.path.exists(audio_file_path):
            return ""
            
        with open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()

        # Robust Detection
        is_webm = content.startswith(b"\x1a\x45\xdf\xa3") or b"webm" in content[:2000]
        is_wav = content.startswith(b"RIFF")
        
        if is_webm:
            encoding = speech.RecognitionConfig.AudioEncoding.WEBM_OPUS
            sample_rate = 48000 
        elif is_wav:
            # Simulated hardware data (16kHz WAV)
            encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
            sample_rate = 16000
        else:
            # Default fallback for raw ESP32 data (usually 16kHz)
            encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
            sample_rate = 16000

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=sample_rate,
            language_code="en-US",
        )

        print(f"DEBUG STT: Encoding={encoding}, SampleRate={sample_rate}")
        try:
            print("DEBUG STT: Calling Google Speech API...")
            response = await self.client.recognize(config=config, audio=audio, timeout=30)
            print("DEBUG STT: API Response received.")
            
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript
            
            print(f"DEBUG STT: Transcript: '{transcript}'")
            return transcript.strip()
        except Exception as e:
            print(f"STT Error during API call: {e}")
            import traceback
            traceback.print_exc()
            return ""
