import os
import io
import wave
from google.cloud import speech
from google.api_core.client_options import ClientOptions
from config import get_settings

class TranscriptionService:
    def __init__(self):
        self.settings = get_settings()
        options = ClientOptions(api_key=self.settings.GOOGLE_API_KEY)
        self.client = speech.SpeechClient(client_options=options)

    async def transcribe(self, audio_path: str) -> str:
        """Transcribes audio file to text using Google Cloud STT."""
        if not os.path.exists(audio_path):
            return ""

        with io.open(audio_path, "rb") as audio_file:
            content = audio_file.read()

        # [NEW] Robust Format Detection
        is_webm = b"webm" in content[:2000] or content.startswith(b"\x1a\x45\xdf\xa3")
        is_wav = b"RIFF" in content[:100] and b"WAVE" in content[:100]
        
        detected_rate = 16000 # Default fallback
        
        if is_webm:
            encoding = speech.RecognitionConfig.AudioEncoding.WEBM_OPUS
        elif is_wav:
            # For WAV files, we try to detect the sample rate from the header
            try:
                with wave.open(io.BytesIO(content), 'rb') as wav_file:
                    detected_rate = wav_file.getframerate()
                    print(f"DEBUG STT: wave.open detected {detected_rate}Hz")
            except Exception as e:
                print(f"DEBUG STT: WAVE lib failed, using 16k: {e}")
                detected_rate = 16000
            
            encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
        else:
            # Fallback for raw or unknown
            encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
            detected_rate = 16000

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=detected_rate,
            language_code="en-US",
        )

        response = self.client.recognize(config=config, audio=audio)

        for result in response.results:
            return result.alternatives[0].transcript

        return ""
