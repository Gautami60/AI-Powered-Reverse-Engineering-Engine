import httpx
import asyncio

API_KEY = "AIzaSyD_vMxS_Af-bkJNX8HhBUU7nR9pzAPATmU"

async def list_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print(f"Available Models: {data}")
    except:
        print(f"Response Text: {response.text}")

if __name__ == "__main__":
    asyncio.run(list_models())