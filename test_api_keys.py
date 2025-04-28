#!/usr/bin/env python

"""
Script to test API key configuration.
This script checks if the API keys in your environment are properly set up.
"""

import os
import sys
from dotenv import load_dotenv
import httpx
import asyncio

# Load environment variables
load_dotenv()

def colorize(text, color_code):
    """Add color to terminal output"""
    return f"\033[{color_code}m{text}\033[0m"

def success(text):
    """Format success message in green"""
    return colorize(text, "32")

def error(text):
    """Format error message in red"""
    return colorize(text, "31")

def warning(text):
    """Format warning message in yellow"""
    return colorize(text, "33")

def info(text):
    """Format info message in blue"""
    return colorize(text, "34")

# Get API keys from environment
GOOGLE_API_KEY = os.getenv('GOOGLE_GENERATIVE_AI_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')
SEARCH_PROVIDER = os.getenv('SEARCH_PROVIDER', 'searxng')

# Simple validators to check if keys look valid
def validate_google_key(key):
    return key.startswith('AIza')

def validate_openai_key(key):
    return key.startswith('sk-')

def validate_anthropic_key(key):
    return key.startswith('sk-ant-')

def validate_tavily_key(key):
    return key.startswith('tvly-')

async def test_google_api():
    """Test Google Generative AI API key"""
    if not GOOGLE_API_KEY:
        print(error("❌ Google API key not configured"))
        return False
    
    if not validate_google_key(GOOGLE_API_KEY):
        print(warning("⚠️ Google API key doesn't match expected format (should start with 'AIza')"))
    
    base_url = os.getenv('GOOGLE_GENERATIVE_AI_API_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/models')
    url = f"{base_url}/gemini-1.5-pro"
    headers = {"Content-Type": "application/json"}
    params = {"key": GOOGLE_API_KEY}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=10.0)
            if response.status_code == 200:
                print(success("✅ Google API key is valid"))
                return True
            else:
                print(error(f"❌ Google API key error: {response.status_code} - {response.text[:100]}"))
                return False
    except Exception as e:
        print(error(f"❌ Google API request error: {str(e)}"))
        return False

async def test_openai_api():
    """Test OpenAI API key"""
    if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_openai_api_key':
        print(warning("⚠️ OpenAI API key not configured"))
        return False
    
    if not validate_openai_key(OPENAI_API_KEY):
        print(warning("⚠️ OpenAI API key doesn't match expected format (should start with 'sk-')"))
    
    base_url = os.getenv('OPENAI_API_BASE_URL', 'https://api.openai.com/v1')
    url = f"{base_url}/models"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                print(success("✅ OpenAI API key is valid"))
                return True
            else:
                print(error(f"❌ OpenAI API key error: {response.status_code} - {response.text[:100]}"))
                return False
    except Exception as e:
        print(error(f"❌ OpenAI API request error: {str(e)}"))
        return False

async def test_anthropic_api():
    """Test Anthropic API key"""
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == 'your_anthropic_api_key':
        print(warning("⚠️ Anthropic API key not configured"))
        return False
    
    if not validate_anthropic_key(ANTHROPIC_API_KEY):
        print(warning("⚠️ Anthropic API key doesn't match expected format (should start with 'sk-ant-')"))
    
    # Anthropic doesn't have a simple endpoint to verify the API key without making a completion
    # So we'll just check the format and mention that it's configured
    print(info("ℹ️ Anthropic API key is configured but not verified (requires making a completion)"))
    return True

async def test_tavily_api():
    """Test Tavily API key"""
    if SEARCH_PROVIDER != 'tavily':
        print(info(f"ℹ️ Search provider is set to '{SEARCH_PROVIDER}', not 'tavily'"))
        if not TAVILY_API_KEY or TAVILY_API_KEY == 'your_tavily_api_key':
            print(info("ℹ️ Tavily API key not configured (not needed with current search provider)"))
        return True
    
    if not TAVILY_API_KEY or TAVILY_API_KEY == 'your_tavily_api_key':
        print(error("❌ Tavily API key not configured but SEARCH_PROVIDER is set to 'tavily'"))
        return False
    
    if not validate_tavily_key(TAVILY_API_KEY):
        print(warning("⚠️ Tavily API key doesn't match expected format (should start with 'tvly-')"))
    
    tavily_url = os.getenv('TAVILY_API_BASE_URL', 'https://api.tavily.com/v1/search')
    headers = {
        "Content-Type": "application/json",
        "x-api-key": TAVILY_API_KEY
    }
    payload = {
        "query": "test",
        "search_depth": "basic",
        "include_answer": False
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(tavily_url, headers=headers, json=payload, timeout=10.0)
            if response.status_code == 200:
                print(success("✅ Tavily API key is valid"))
                return True
            else:
                print(error(f"❌ Tavily API key error: {response.status_code} - {response.text[:100]}"))
                return False
    except Exception as e:
        print(error(f"❌ Tavily API request error: {str(e)}"))
        return False

async def main():
    """Run all tests and provide a summary"""
    print(info("\n=== Testing API Key Configuration ===\n"))
    
    # Test each API key
    google_ok = await test_google_api()
    openai_ok = await test_openai_api()
    anthropic_ok = await test_anthropic_api()
    tavily_ok = await test_tavily_api()
    
    print(info("\n=== Configuration Summary ===\n"))
    
    # Summary based on the current configuration
    if SEARCH_PROVIDER == 'searxng':
        if google_ok:
            print(success("✅ Minimal configuration is complete. You can use Gemini models with SearXNG search."))
        else:
            print(error("❌ Google API key is required for the minimal configuration."))
    else:  # tavily
        if google_ok and tavily_ok:
            print(success("✅ Configuration for Gemini with Tavily search is complete."))
        else:
            print(error("❌ Both Google and Tavily API keys are required for your current configuration."))
    
    # Additional capabilities
    if openai_ok:
        print(success("✅ OpenAI models are available to use."))
    
    if anthropic_ok:
        print(success("✅ Anthropic models are available to use."))
    
    print(info("\n=== Recommended Actions ===\n"))
    
    if not google_ok:
        print(error("❌ Configure your Google API key - required for basic functionality"))
    
    if SEARCH_PROVIDER == 'tavily' and not tavily_ok:
        print(error("❌ Configure your Tavily API key or change SEARCH_PROVIDER to 'searxng'"))
    
    if not openai_ok and not anthropic_ok:
        print(warning("⚠️ Consider configuring at least one of OpenAI or Anthropic API keys for more model options"))
    
    print("\nTo make these changes, edit your .env file in the project root directory.")

if __name__ == "__main__":
    asyncio.run(main()) 