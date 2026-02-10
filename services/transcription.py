import os
from google.cloud import speech
from google.api_core.client_options import ClientOptions
from config import get_settings

class TranscriptionService:
    def __init__(self):
        self.settings = get_settings()
        # Initializing with API Key via ClientOptions
        options = ClientOptions(api_key=self.settings.GOOGLE_API_KEY)
        self.client = speech.SpeechClient(client_options=options)

    async def transcribe(self, audio_file_path: str) -> str:
        """Transcribes audio file to text using Google Cloud Speech-to-Text."""
        if not os.path.exists(audio_file_path):
            return ""
            
        with open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()

        # Simple format detection for Google STT
        # WebM files start with \x1A\x45\xDF\xA3 (EBML header)
        if content.startswith(b"\x1a\x45\xdf\xa3"):
            encoding = speech.RecognitionConfig.AudioEncoding.WEBM_OPUS
            # For WEBM_OPUS, sample_rate_hertz should be unspecified or match exactly.
            # Setting it to 0 or leaving it out is best.
            sample_rate = 0 
        else:
            # Default to LINEAR16 for raw ESP32 data (usually 16kHz)
            encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
            sample_rate = 16000 

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=sample_rate,
            language_code="en-US",
            model="chirp",
        )

        try:
            response = self.client.recognize(config=config, audio=audio)
            
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript
                
            return transcript.strip()
        except Exception as e:
            print(f"STT Error: {e}")
            return ""
