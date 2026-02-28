from langchain_google_genai import ChatGoogleGenerativeAI
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

llm = ChatGoogleGenerativeAI(
    google_api_key=api_key,
    model="gemini-1.5-flash"
)

try:
    response = llm.invoke("Hello, say 'Test Passed'")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"Flash verification failed: {e}")
