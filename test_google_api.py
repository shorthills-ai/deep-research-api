import os
import asyncio
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GOOGLE_GENERATIVE_AI_API_KEY')
BASE_URL = os.getenv('GOOGLE_GENERATIVE_AI_API_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/models')
MODEL = 'gemini-1.5-pro'

async def test_gemini_api():
    """Test if the Gemini API key is working"""
    
    if not API_KEY:
        print("No API key found. Please set GOOGLE_GENERATIVE_AI_API_KEY in your .env file")
        return False
    
    print(f"Testing Gemini API with key: {API_KEY[:5]}...{API_KEY[-4:]}")
    
    url = f"{BASE_URL}/{MODEL}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}
    
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Say hello world"}]}],
        "generationConfig": {"temperature": 0.7}
    }
    
    try:
        print(f"Making request to Gemini API: {url}")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, params=params, json=payload, timeout=30.0)
            
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            try:
                result = response.json()
                print(f"Response received: {json.dumps(result, indent=2)}")
                
                if "candidates" not in result or not result["candidates"]:
                    print("Error: No candidates in response")
                    return False
                
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                print(f"Success! Response text: {text}")
                return True
            except Exception as e:
                print(f"Error parsing response: {str(e)}")
                return False
    except Exception as e:
        print(f"Request error: {str(e)}")
        return False

async def main():
    success = await test_gemini_api()
    if success:
        print("✅ API test passed! The Gemini API key is working correctly.")
    else:
        print("❌ API test failed! The Gemini API key is not working.")

if __name__ == "__main__":
    asyncio.run(main()) 