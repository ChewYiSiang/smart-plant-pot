import os
from google.cloud import texttospeech
from google.api_core.client_options import ClientOptions
from config import get_settings

class SpeechSynthesisService:
    def __init__(self):
        self.settings = get_settings()
        # Initializing with API Key via ClientOptions
        options = ClientOptions(api_key=self.settings.GOOGLE_API_KEY)
        self.client = texttospeech.TextToSpeechClient(client_options=options)

    async def synthesize(
        self, 
        text: str, 
        output_path: str, 
        volume_gain_db: float = 0.0,
        speaking_rate: float = 0.88,
        pitch: float = 1.0
    ):
        """Synthesizes text to an MP3 file using Google Cloud TTS as plain text."""
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # [ARTICULATE] Neural2-E is the sharpest biting voice
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-E"
        )

        # [TELEPHONY] Using telephony-class-application to force clarity over bass
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            volume_gain_db=volume_gain_db, 
            speaking_rate=speaking_rate,
            pitch=pitch,
            sample_rate_hertz=22050,
            effects_profile_id=["telephony-class-application"]
        )

        # Perform the text-to-speech request
        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "wb") as out:
            out.write(response.audio_content)
            
        return output_path

    async def synthesize_stream(
        self, 
        text: str, 
        volume_gain_db: float = 0.0,
        speaking_rate: float = 0.88,
        pitch: float = 1.0
    ) -> bytes:
        """Synthesizes text and returns raw audio bytes (MP3) as plain text."""
        print(f"DEBUG: [TTS] Synthesizing plain text: {text[:50]}...")
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-E"
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            volume_gain_db=volume_gain_db,
            speaking_rate=speaking_rate,
            pitch=pitch,
            sample_rate_hertz=22050,
            effects_profile_id=["telephony-class-application"]
        )
        
        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        return response.audio_content
