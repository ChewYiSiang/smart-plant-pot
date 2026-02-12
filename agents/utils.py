from langchain_google_genai import ChatGoogleGenerativeAI
from config import get_settings

def get_llm():
    """
    Returns a Gemini 2.5 Pro LLM with a fallback to Gemini 2.5 Flash.
    This ensures robustness if the Pro model fails or hits limits.
    """
    settings = get_settings()
    
    # Primary Model: Gemini 2.5 Pro (Restored as requested)
    llm_pro = ChatGoogleGenerativeAI(
        google_api_key=settings.GOOGLE_API_KEY, 
        model="gemini-2.5-pro",
        temperature=0.7,
        streaming=True
    )
    
    # Fallback Model: Gemini 2.5 Flash
    llm_flash = ChatGoogleGenerativeAI(
        google_api_key=settings.GOOGLE_API_KEY, 
        model="gemini-2.5-flash",
        temperature=0.7,
        streaming=True
    )
    
    # Create a runnable with fallback
    llm_with_fallback = llm_pro.with_fallbacks([llm_flash])
    
    return llm_with_fallback
