import google.generativeai as genai
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
    with open("model_list_output.txt", "w") as f:
        f.write("Error: GOOGLE_API_KEY not found.")
    exit(1)

genai.configure(api_key=api_key)

try:
    models = list(genai.list_models())
    with open("model_list_output.txt", "w") as f:
        f.write("Available models:\n")
        for m in models:
            f.write(f"{m.name}\n")
except Exception as e:
    with open("model_list_output.txt", "w") as f:
        f.write(f"Failed to list models: {str(e)}")
