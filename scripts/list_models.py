import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    # Try reading from config.py if .env is missing
    try:
        from config import get_settings
        api_key = get_settings().GOOGLE_API_KEY
    except:
        pass

if not api_key:
    print("Error: GOOGLE_API_KEY not found.")
    exit(1)

genai.configure(api_key=api_key)

print(f"Checking models for API Key: {api_key[:10]}...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Failed to list models: {e}")
