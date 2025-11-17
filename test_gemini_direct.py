import httpx
import asyncio
import json

API_KEY = "AIzaSyBPEFaTgNyyTjIFJKuHHpm547i4vEmqNs0"

async def test_gemini_api():
    # Try with gemini-pro model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Explain in one short sentence: mov eax, ebx"
                    }
                ]
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=30.0)
        
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    try:
        data = response.json()
        print(f"Response JSON: {json.dumps(data, indent=2)}")
    except:
        print(f"Response Text: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_gemini_api())