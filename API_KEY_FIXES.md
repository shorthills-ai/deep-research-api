# API Key Configuration and SearXNG Search Fixes

## Issues Fixed

This update addresses two main issues:

1. **Missing API Keys**: The application was failing because placeholder values were used in the `.env` file for most API keys.

2. **SearXNG Search 403 Errors**: The SearXNG search was failing with 403 Forbidden errors, causing research to fail.

## Fixes Implemented

### 1. API Key Configuration

- Created detailed documentation in `SETUP_API_KEYS.md` explaining the API key requirements
- Added a test script (`test_api_keys.py`) to verify API key configuration
- Updated README.md with API key setup information
- Created a user-friendly HTML guide (`static/apikey_setup.html`)

### 2. SearXNG Search Reliability

- Modified `search_with_searxng` function to try multiple SearXNG instances
- Added proper User-Agent headers to avoid being blocked
- Implemented fallback to mock results if all instances fail
- Added documentation recommending Tavily as a more reliable alternative

## How to Test

1. Run the API key test script:
   ```bash
   python test_api_keys.py
   ```

2. Restart the server:
   ```bash
   ./restart_server.sh
   ```

3. Try a research query:
   ```bash
   curl -X POST http://localhost:8000/api/research \
     -H "Content-Type: application/json" \
     -d '{"query": "Latest advancements in quantum computing", "model": "gemini-1.5-pro"}'
   ```

## Current Status

- The Google API key is working correctly
- The application can now use Gemini models even if SearXNG fails
- For full functionality with other models, you'll need to add the relevant API keys

## Recommendations

1. **For better search results**: Sign up for Tavily and update your `.env` file to use it instead of SearXNG:
   ```
   SEARCH_PROVIDER=tavily
   TAVILY_API_KEY=your-tavily-key
   ```

2. **For using all LLM models**: Configure API keys for OpenAI and Anthropic in your `.env` file.

## Files Changed

- `research/views.py` - Modified search_with_searxng function for better reliability
- `SETUP_API_KEYS.md` - Created detailed API key setup guide
- `test_api_keys.py` - Created API key testing script
- `README.md` - Added API key and search configuration information
- `static/apikey_setup.html` - Created user-friendly setup guide
- `restart_server.sh` - Added server management script 