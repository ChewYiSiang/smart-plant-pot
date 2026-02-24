from langchain_google_genai import ChatGoogleGenerativeAI
from config import get_settings

def get_llm():
    """
    Returns a Gemini 2.5 Pro LLM as requested by the USER.
    """
    settings = get_settings()
    
    # Model: Gemini 2.5 Pro
    llm = ChatGoogleGenerativeAI(
        google_api_key=settings.GOOGLE_API_KEY, 
        model="gemini-2.5-pro",
        temperature=0.7,
        streaming=True
    )
    
    return llm
