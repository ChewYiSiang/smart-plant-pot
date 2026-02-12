from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    from config import get_settings
    api_key = get_settings().GOOGLE_API_KEY

print(f"Testing gemini-2.5-pro (Final Verification) with API Key: {api_key[:10]}...")

# Test with default (v1beta for streaming)
llm = ChatGoogleGenerativeAI(
    google_api_key=api_key,
    model="gemini-2.5-pro"
)

try:
    print("Testing astream()...")
    import asyncio
    async def test_stream():
        async for chunk in llm.astream("Hello"):
            print(f"Chunk: {chunk.content}")
            
    asyncio.run(test_stream())
    print("\nASTREAM SUCCESS")
except Exception as e:
    print(f"\nASTREAM FAILED: {e}")
    
    # Try with version='v1' if supported/available
    try:
        print("\nRetrying with version='v1'...")
        llm_v1 = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model="gemini-2.5-pro",
            version="v1"
        )
        async def test_stream_v1():
            async for chunk in llm_v1.astream("Hello"):
                print(f"Chunk (v1): {chunk.content}")
        asyncio.run(test_stream_v1())
        print("\nASTREAM V1 SUCCESS")
    except Exception as e2:
        print(f"\nASTREAM V1 FAILED: {e2}")
