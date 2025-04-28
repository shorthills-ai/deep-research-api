import os
import asyncio
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

SEARCH_PROVIDER = os.getenv('SEARCH_PROVIDER', 'searxng')
SEARXNG_URL = os.getenv('SEARXNG_API_BASE_URL', 'https://searx.be/search')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')
TAVILY_URL = os.getenv('TAVILY_API_BASE_URL', 'https://api.tavily.com/v1/search')

async def test_searxng():
    """Test if SearXNG is working"""
    print(f"Testing SearXNG with URL: {SEARXNG_URL}")
    
    params = {"q": "test query", "format": "json", "engines": "google"}
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"Making request to SearXNG: {SEARXNG_URL}?q=test query")
            response = await client.get(SEARXNG_URL, params=params, timeout=30.0)
            
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            try:
                results = response.json()
                print(f"Response received with {len(results.get('results', []))} results")
                
                if "results" not in results:
                    print("Error: No results in response")
                    print(f"Response: {json.dumps(results, indent=2)}")
                    return False
                
                if not results.get("results"):
                    print("Warning: Empty results list")
                    return True  # Still consider this a pass as the API is working
                
                print(f"Sample result: {json.dumps(results['results'][0], indent=2)}")
                return True
            except Exception as e:
                print(f"Error parsing response: {str(e)}")
                return False
    except Exception as e:
        print(f"Request error: {str(e)}")
        return False

async def test_tavily():
    """Test if Tavily is working"""
    if not TAVILY_API_KEY:
        print("No Tavily API key found. Please set TAVILY_API_KEY in your .env file")
        return False
    
    print(f"Testing Tavily with URL: {TAVILY_URL}")
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": TAVILY_API_KEY
    }
    payload = {
        "query": "test query",
        "search_depth": "advanced",
        "include_answer": False,
        "include_domains": [],
        "exclude_domains": []
    }
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"Making request to Tavily")
            response = await client.post(TAVILY_URL, headers=headers, json=payload, timeout=30.0)
            
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            try:
                results = response.json()
                print(f"Response received with {len(results.get('results', []))} results")
                
                if "results" not in results:
                    print("Error: No results in response")
                    print(f"Response: {json.dumps(results, indent=2)}")
                    return False
                
                if not results.get("results"):
                    print("Warning: Empty results list")
                    return True  # Still consider this a pass as the API is working
                
                print(f"Sample result: {json.dumps(results['results'][0], indent=2)}")
                return True
            except Exception as e:
                print(f"Error parsing response: {str(e)}")
                return False
    except Exception as e:
        print(f"Request error: {str(e)}")
        return False

async def main():
    provider = SEARCH_PROVIDER.lower()
    print(f"Using search provider: {provider}")
    
    if provider == "searxng":
        success = await test_searxng()
    elif provider == "tavily":
        success = await test_tavily()
    else:
        print(f"Unknown search provider: {provider}")
        return
    
    if success:
        print(f"✅ API test passed! The {provider} API is working correctly.")
    else:
        print(f"❌ API test failed! The {provider} API is not working.")

if __name__ == "__main__":
    asyncio.run(main()) 