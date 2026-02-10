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

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000, # Matches hardware
            language_code="en-US",
            model="chirp", # Use the powerful Chirp model (Vertex AI) if available, otherwise "default"
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
