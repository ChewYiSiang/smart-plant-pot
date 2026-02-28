from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    try:
        from config import get_settings
        api_key = get_settings().GOOGLE_API_KEY
    except:
        pass

if not api_key:
    print("Error: GOOGLE_API_KEY not found.")
    exit(1)

client = genai.Client(api_key=api_key)

print(f"Listing models for API Key: {api_key[:10]}...")
try:
    for model in client.models.list():
        print(model.name)
except Exception as e:
    print(f"Failed to list models via google-genai: {e}")
