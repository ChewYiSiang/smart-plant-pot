from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    from config import get_settings
    api_key = get_settings().GOOGLE_API_KEY

print(f"Testing gemini-2.5-pro with API Key: {api_key[:10]}...")

llm = ChatGoogleGenerativeAI(
    google_api_key=api_key,
    model="gemini-2.5-pro"
)

try:
    print("Testing invoke()...")
    res = llm.invoke("Hello")
    print(f"Invoke Success: {res.content}")
except Exception as e:
    print(f"Invoke Failed: {e}")

try:
    print("\nTesting astream()...")
    for chunk in llm.stream("Hello"):
        print(f"Stream Chunk: {chunk.content}")
except Exception as e:
    print(f"Stream Failed: {e}")
