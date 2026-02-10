from google.cloud import speech
from google.api_core.client_options import ClientOptions
from config import get_settings

def list_models():
    settings = get_settings()
    options = ClientOptions(api_key=settings.GOOGLE_API_KEY)
    client = speech.SpeechClient(client_options=options)
    
    # In V1, there isn't a direct 'list_models' like in some other APIs, 
    # but we can try a tiny recognition with chirp_3 to see if it errors out immediately.
    print("Testing 'chirp_3' model availability...")
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        model="chirp_3"
    )
    audio = speech.RecognitionAudio(content=b"\0"*3200) # 0.1s of silence
    
    try:
        client.recognize(config=config, audio=audio)
        print("SUCCESS: 'chirp_3' is available.")
    except Exception as e:
        print(f"FAILURE: 'chirp_3' error: {e}")

if __name__ == "__main__":
    list_models()
