import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.utils.llm_client import call_llm

async def test_gemini():
    messages = [
        {"role": "system", "content": "You are a helpful assistant that explains assembly code."},
        {"role": "user", "content": "Explain in one short sentence: mov eax, ebx"}
    ]
    
    try:
        result = await call_llm(messages)
        print("Success! Response from Gemini:")
        print(result)
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini())