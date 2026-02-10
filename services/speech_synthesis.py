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

    async def synthesize(self, text: str, output_path: str):
        """Synthesizes text to a 16kHz Mono WAV file using Google Cloud TTS."""
        
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-F", # Premium-like voice
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )

        # Select the type of audio file you want returned
        # LINEAR16 = Uncompressed 16-bit PCM (WAV)
        # sample_rate_hertz = 16000 (Optimized for MAX98357)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.settings.AUDIO_SAMPLE_RATE,
            effects_profile_id=["small-bluetooth-speaker-class-device"] # Optimization profile
        )

        # Perform the text-to-speech request
        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write the response to the output file.
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
