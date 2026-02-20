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
        speaking_rate: float = 1.05,
        pitch: float = 0.0
    ):
        """Synthesizes text to an MP3 file using Google Cloud TTS as plain text."""
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-F"
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            volume_gain_db=volume_gain_db,
            speaking_rate=speaking_rate,
            pitch=pitch
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
        speaking_rate: float = 1.05,
        pitch: float = 0.0
    ) -> bytes:
        """Synthesizes text and returns raw audio bytes (MP3) as plain text."""
        print(f"DEBUG: [TTS] Synthesizing plain text: {text[:50]}...")
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-F"
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            volume_gain_db=volume_gain_db,
            speaking_rate=speaking_rate,
            pitch=pitch
        )
        
        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        return response.audio_content
