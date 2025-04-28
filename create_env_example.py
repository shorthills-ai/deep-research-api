#!/usr/bin/env python

"""
Simple script to create the .env.example file
"""

env_content = """# Django settings
SECRET_KEY=your_secret_key_here
DEBUG=True

# LLM API Keys
GOOGLE_GENERATIVE_AI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# LLM API Base URLs (Optional)
GOOGLE_GENERATIVE_AI_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta/models
OPENAI_API_BASE_URL=https://api.openai.com/v1
ANTHROPIC_API_BASE_URL=https://api.anthropic.com/v1

# Search Provider Configuration
SEARCH_PROVIDER=searxng  # Options: searxng, tavily
SEARXNG_API_BASE_URL=https://searx.be/search
TAVILY_API_KEY=your_tavily_api_key
TAVILY_API_BASE_URL=https://api.tavily.com/v1/search
"""

with open('.env.example', 'w') as f:
    f.write(env_content)

print("Created .env.example file") 