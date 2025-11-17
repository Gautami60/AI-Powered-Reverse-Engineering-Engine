import httpx
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from the backend directory
load_dotenv("backend/.env")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
print(f"API Key loaded: {bool(GOOGLE_API_KEY)}")
if GOOGLE_API_KEY:
    print(f"API Key (first 10 chars): {GOOGLE_API_KEY[:10]}...")

async def test_gemini_api():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateText?key={GOOGLE_API_KEY}"
    
    payload = {
        "prompt": {"text": "Explain in one short sentence: mov eax, ebx"},
        "maxOutputTokens": 200
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=30.0)
        
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_gemini_api())