# Setting Up API Keys for Django Research API

The application requires several API keys to function properly. Currently, your `.env` file has placeholder values for most API keys, which is causing the application to fail.

## Current `.env` Status

```
GOOGLE_GENERATIVE_AI_API_KEY=AIzaSyDS7BH8fYq0x8Simsr9y5AP8kLb9pJZCw4  # This one is set
OPENAI_API_KEY=your_openai_api_key                 # Placeholder - needs updating
ANTHROPIC_API_KEY=your_anthropic_api_key           # Placeholder - needs updating
TAVILY_API_KEY=your_tavily_api_key                 # Placeholder - needs updating
```

## Default Configuration

The application is currently configured to:
- Use `gemini-1.5-pro` as the default LLM model
- Use `searxng` as the default search provider (doesn't require an API key)

## Search Provider Considerations

### SearXNG Issues

The default SearXNG search provider may sometimes return 403 Forbidden errors or be unreliable because:
- Many public instances have rate limiting
- They may block automated requests
- Availability can be inconsistent

The application will now try multiple SearXNG instances and use mock results as a last resort, but for more reliable results, consider using Tavily.

### Tavily Recommended

For more reliable search results, we recommend configuring Tavily as your search provider:

1. Get a Tavily API key at https://tavily.com/
2. Update your `.env` file:
   ```
   SEARCH_PROVIDER=tavily
   TAVILY_API_KEY=tvly-your-actual-tavily-key
   ```

## Required API Keys Based on Usage

1. **For minimal setup (uses only Gemini and SearXNG)**:
   - Your Google API key is already configured correctly, no changes needed.

2. **If you want to use OpenAI models** (gpt-4o, gpt-4-turbo, gpt-3.5-turbo):
   - You must add your OpenAI API key

3. **If you want to use Anthropic models** (claude-3-opus, claude-3-sonnet, claude-3-haiku):
   - You must add your Anthropic API key
   
4. **If you want to use Tavily search instead of SearXNG**:
   - You must add your Tavily API key
   - Change the `SEARCH_PROVIDER` to `tavily` in your `.env` file

## How to Update Your API Keys

1. Open the `.env` file in your project root with a text editor:
   ```
   nano .env
   ```
   or
   ```
   code .env
   ```

2. Replace the placeholder values with your actual API keys:
   ```
   OPENAI_API_KEY=sk-your-actual-openai-key
   ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key
   TAVILY_API_KEY=tvly-your-actual-tavily-key
   ```

3. Save the file

## Test Your API Key Configuration

A test script has been provided to verify if your API keys are properly configured.

To run the test script:

```
python test_api_keys.py
```

The script will:
1. Check if the required API keys are present based on your configuration
2. Verify the format of your API keys
3. Test if the keys are valid by making API calls
4. Provide recommendations on what keys you need to configure

This is the recommended way to test your configuration before using the application.

## Where to Get API Keys

- **OpenAI API Key**: Sign up at https://platform.openai.com/
- **Anthropic API Key**: Sign up at https://www.anthropic.com/product
- **Tavily API Key**: Sign up at https://tavily.com/
- **Google Generative AI API Key**: Sign up at https://aistudio.google.com/

## Troubleshooting

If you're seeing errors like "No API key found for OpenAI model" or similar, it means:
1. You're trying to use a model that requires an API key you haven't provided, or
2. The API key is invalid or formatted incorrectly

If you're seeing SearXNG errors like "403 Forbidden":
1. This is a known issue with public SearXNG instances
2. The app will try multiple SearXNG instances automatically
3. Consider switching to Tavily for more reliable results

You can check the application logs for more detailed error messages. If you only want to use Gemini models, you don't need to set up any additional API keys as your Google API key is already configured.

## Minimum Required Keys

If you don't need all services, at minimum you should set up:
- `GOOGLE_GENERATIVE_AI_API_KEY` (already set)
- Either `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` 
- If using Tavily search, `TAVILY_API_KEY` (otherwise the default SearXNG will be used) 