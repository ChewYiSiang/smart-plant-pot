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
    model="gemini-2.0-flash"
)

try:
    response = llm.invoke("Say '2.0 Flash is working'")
    with open("verification_result.txt", "w") as f:
        f.write(f"SUCCESS: {response.content}")
except Exception as e:
    with open("verification_result.txt", "w") as f:
        f.write(f"FAILED: {str(e)}")
