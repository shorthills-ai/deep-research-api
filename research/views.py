from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import asyncio
import httpx
import threading
import time
from datetime import datetime
from asgiref.sync import sync_to_async
from .models import Research
from .utils import (
    generate_serp_queries_prompt, 
    process_search_result_prompt,
    write_final_report_prompt,
    get_system_prompt
)
import os

# --- API Endpoints ---

@csrf_exempt
@require_http_methods(["GET"])
def api_root(request):
    """API health check"""
    return JsonResponse({"status": "ok", "version": "1.0.0"})

@csrf_exempt
@require_http_methods(["POST"])
def start_research(request):
    """Start a new research process"""
    try:
        # Print the raw request body for debugging
        print(f"Request body: {request.body}")
        
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({"error": f"Invalid JSON: {str(e)}"}, status=400)
            
        # Check for required fields
        if 'query' not in data:
            return JsonResponse({"error": "Missing required field: query"}, status=400)
        
        # Create a new research object
        research = Research(
            query=data.get('query'),
            model=data.get('model', 'gemini-1.5-pro'),
            search_model=data.get('search_model'),
            max_searches=data.get('max_searches', 5),
            custom_requirement=data.get('custom_requirement', '')
        )
        research.save()
        
        # Start the research process in the background using a thread
        def run_async_research():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(conduct_research(research.id))
            finally:
                loop.close()
                
        # Start research in a separate thread
        thread = threading.Thread(target=run_async_research)
        thread.daemon = True
        thread.start()
        
        return JsonResponse(research.as_dict())
    
    except Exception as e:
        print(f"Error in start_research: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)

@require_http_methods(["GET"])
def get_research(request, research_id):
    """Get the status and results of a research process"""
    try:
        research = Research.objects.get(id=research_id)
        return JsonResponse(research.as_dict())
    except Research.DoesNotExist:
        return JsonResponse({"detail": f"Research {research_id} not found"}, status=404)

@require_http_methods(["GET"])
def stream_research(request, research_id):
    """Stream real-time updates of a research process"""
    try:
        research = Research.objects.get(id=research_id)
        
        def event_stream():
            """Generate SSE event stream"""
            # Send initial state
            yield f"data: {json.dumps(research.as_dict())}\n\n"
            
            # Track what's been sent to avoid sending duplicates
            sent_learning_count = len(research.learnings)
            sent_status = research.status
            sent_report = research.report
            
            # Keep streaming updates until the research is complete
            while research.status not in ["completed", "error", "no_results"]:
                # Refresh the research object from the database
                research.refresh_from_db()
                
                # Send status update if it changed
                if research.status != sent_status:
                    sent_status = research.status
                    yield f"data: {json.dumps({'status': research.status})}\n\n"
                
                # Send new learnings if any
                current_learning_count = len(research.learnings)
                if current_learning_count > sent_learning_count:
                    new_learnings = research.learnings[sent_learning_count:]
                    yield f"data: {json.dumps({'learnings': new_learnings})}\n\n"
                    sent_learning_count = current_learning_count
                
                # Send report if it's been generated and not sent yet
                if research.report and research.report != sent_report:
                    sent_report = research.report
                    yield f"data: {json.dumps({'report': research.report})}\n\n"
                
                # Add a small delay to prevent overwhelming the database
                time.sleep(1)
            
            # Send final state
            yield f"data: {json.dumps({'status': 'complete', 'final': True})}\n\n"
        
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # Prevent buffering in Nginx
        return response
        
    except Research.DoesNotExist:
        return JsonResponse({"detail": f"Research {research_id} not found"}, status=404)

@require_http_methods(["GET"])
def get_models(request):
    """Get the list of available models"""
    return JsonResponse({
        "models": {
            "gemini": [
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-1.0-pro"
            ],
            "openai": [
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ],
            "anthropic": [
                "claude-3-opus",
                "claude-3-sonnet",
                "claude-3-haiku"
            ]
        }
    })

@require_http_methods(["GET"])
def get_search_providers(request):
    """Get the list of available search providers"""
    return JsonResponse({
        "providers": [
            {
                "id": "searxng",
                "name": "SearXNG",
                "description": "Open-source metasearch engine",
                "requires_key": False
            },
            {
                "id": "tavily",
                "name": "Tavily",
                "description": "AI-powered search API",
                "requires_key": True
            }
        ]
    })

# --- Core Research Functions ---

async def conduct_research(research_id):
    """Conduct the research process in the background"""
    # Use sync_to_async to get the research object
    get_research = sync_to_async(Research.objects.get)
    research = await get_research(id=research_id)
    
    try:
        # 1. Generate SERP queries
        # Use sync_to_async for database operations
        @sync_to_async
        def update_research_status(status):
            research.status = status
            research.save()
        
        @sync_to_async
        def update_error(error_msg):
            research.status = "error"
            research.error = error_msg
            research.save()
            print(f"ERROR: {error_msg}")
        
        print(f"Starting research for '{research.query}'")
        await update_research_status("generating_queries")
        
        try:
            print("Generating SERP queries...")
            serp_prompt = generate_serp_queries_prompt(research.query)
            print(f"Calling LLM with prompt: {serp_prompt[:100]}...")
            serp_response = await call_llm(serp_prompt, research.model)
            print(f"LLM response received: {serp_response[:100]}...")
            
            # Parse JSON response to extract queries
            try:
                # Handle different possible JSON formats
                if '[' in serp_response:
                    json_start = serp_response.find('[')
                    json_end = serp_response.rfind(']') + 1
                    json_str = serp_response[json_start:json_end]
                    serp_queries = json.loads(json_str)
                else:
                    serp_queries = json.loads(serp_response)
                print(f"Parsed {len(serp_queries)} SERP queries")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}, Response: {serp_response[:200]}")
                # Fall back to a single query if JSON parsing fails
                serp_queries = [{"query": research.query, "researchGoal": "Research the main query"}]
                print("Using fallback single query")
        except Exception as e:
            print(f"Error in SERP query generation: {str(e)}")
            await update_error(f"Error generating SERP queries: {str(e)}")
            return
        
        # Limit to max_searches
        @sync_to_async
        def get_max_searches():
            return research.max_searches
        
        max_searches = await get_max_searches()
        serp_queries = serp_queries[:max_searches]
        
        # 2. For each query, search the web and process results
        all_learnings = []
        
        @sync_to_async
        def get_models():
            return (research.search_model or research.model)
        
        search_model = await get_models()
        
        for idx, query_obj in enumerate(serp_queries):
            try:
                query = query_obj.get("query")
                research_goal = query_obj.get("researchGoal", "Research this topic thoroughly")
                
                # Update status with query number
                query_num = idx + 1
                total_queries = len(serp_queries)
                await update_research_status(f"searching: {query_num}/{total_queries}: {query}")
                print(f"Searching for: {query}")
                
                # Search the web
                try:
                    search_results = await search_web(query)
                    print(f"Found {len(search_results)} search results")
                except Exception as e:
                    print(f"Error in web search: {str(e)}")
                    await update_error(f"Error searching the web: {str(e)}")
                    return
                
                # Process search results
                if search_results:
                    await update_research_status(f"processing_results: {query_num}/{total_queries}: {query}")
                    
                    process_prompt = process_search_result_prompt(
                        query, 
                        research_goal, 
                        search_results
                    )
                    print(f"Processing search results with prompt: {process_prompt[:100]}...")
                    
                    try:
                        learnings_text = await call_llm(process_prompt, search_model)
                        print(f"LLM learning response received: {learnings_text[:100]}...")
                        
                        # Extract learnings (simple approach - split by lines or extract bullet points)
                        learnings = [line.strip() for line in learnings_text.split('\n') 
                                    if line.strip() and not line.strip().startswith('#')]
                        print(f"Extracted {len(learnings)} learnings")
                        all_learnings.extend(learnings)
                        
                        # Update learnings in real-time
                        @sync_to_async
                        def update_learnings():
                            research.learnings = all_learnings
                            research.save()
                        
                        await update_learnings()
                    except Exception as e:
                        print(f"Error processing search results: {str(e)}")
                        await update_error(f"Error processing search results: {str(e)}")
                        return
            except Exception as e:
                print(f"Error in query processing loop: {str(e)}")
                await update_error(f"Error processing query {idx+1}: {str(e)}")
                return
        
        # 3. Generate the final report
        if all_learnings:
            await update_research_status("generating_report")
            print("Generating final report...")
            
            @sync_to_async
            def get_query_and_requirement():
                return research.query, research.custom_requirement
            
            query, custom_requirement = await get_query_and_requirement()
            
            report_prompt = write_final_report_prompt(
                query,
                all_learnings, 
                custom_requirement
            )
            
            @sync_to_async
            def get_model():
                return research.model
            
            try:
                model = await get_model()
                print(f"Calling LLM for final report using model {model}...")
                final_report = await call_llm(report_prompt, model, 0.8)
                print(f"Final report received: {final_report[:100]}...")
                
                # Update the research results
                @sync_to_async
                def update_report():
                    research.report = final_report
                    research.status = "completed"
                    research.save()
                
                await update_report()
                print("Research completed successfully")
            except Exception as e:
                print(f"Error generating final report: {str(e)}")
                await update_error(f"Error generating final report: {str(e)}")
                return
        else:
            print("No learnings found, marking as no_results")
            await update_research_status("no_results")
    
    except Exception as e:
        error_msg = f"Unhandled exception: {str(e)}"
        print(error_msg)
        
        @sync_to_async
        def update_error_final():
            research.status = "error"
            research.error = error_msg
            research.save()
        
        await update_error_final()

# --- LLM Integration ---

async def call_llm(prompt, model, temperature=0.7):
    """Call the LLM based on model type"""
    try:
        if model.startswith("gemini"):
            api_key = settings.GOOGLE_GENERATIVE_AI_API_KEY
            if not api_key:
                raise Exception("No API key found for Gemini model")
            print(f"Calling Gemini API with key: {api_key[:5]}...{api_key[-4:]}")
            return await call_gemini(prompt, model, api_key, temperature)
        
        elif model.startswith("gpt"):
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                raise Exception("No API key found for OpenAI model")
            print(f"Calling OpenAI API with key: {api_key[:5]}...")
            return await call_openai(prompt, model, api_key, temperature)
        
        elif model.startswith("claude"):
            api_key = settings.ANTHROPIC_API_KEY
            if not api_key:
                raise Exception("No API key found for Anthropic model")
            print(f"Calling Anthropic API with key: {api_key[:5]}...")
            return await call_anthropic(prompt, model, api_key, temperature)
        
        else:
            raise Exception(f"Unsupported model: {model}")
    except Exception as e:
        print(f"Error in call_llm: {str(e)}")
        raise

async def call_gemini(prompt, model, api_key, temperature):
    """Call Gemini API with retry logic for rate limiting"""
    base_url = settings.GOOGLE_GENERATIVE_AI_API_BASE_URL
    url = f"{base_url}/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature}
    }
    
    # Retry configuration
    max_retries = 5
    retry_delay = 2  # Start with 2 seconds delay
    attempt = 0
    
    while attempt < max_retries:
        try:
            print(f"Making request to Gemini API: {url} (attempt {attempt+1}/{max_retries})")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, params=params, json=payload, timeout=30.0)
                
                if response.status_code == 429:
                    # Rate limit error - parse the response to get retry info
                    error_data = response.json()
                    print(f"Rate limit error: {error_data}")
                    
                    # Calculate delay - default to exponential backoff if no specific delay given
                    retry_delay_secs = retry_delay
                    if "error" in error_data and "details" in error_data["error"]:
                        for detail in error_data["error"]["details"]:
                            if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                                if "retryDelay" in detail:
                                    retry_delay_secs = float(detail["retryDelay"].replace("s", ""))
                    
                    print(f"Rate limited. Retrying in {retry_delay_secs} seconds...")
                    await asyncio.sleep(retry_delay_secs)
                    
                    # Exponential backoff for next attempt
                    retry_delay *= 2
                    attempt += 1
                    continue
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"Gemini API error response: {error_text}")
                    raise Exception(f"Gemini API error ({response.status_code}): {error_text}")
                
                result = response.json()
                if "candidates" not in result or not result["candidates"]:
                    print(f"Unexpected Gemini API response format: {result}")
                    raise Exception("Unexpected Gemini API response format: missing candidates")
                    
                if "content" not in result["candidates"][0] or "parts" not in result["candidates"][0]["content"]:
                    print(f"Unexpected Gemini API response structure: {result['candidates'][0]}")
                    raise Exception("Unexpected Gemini API response structure")
                    
                if not result["candidates"][0]["content"]["parts"]:
                    print("Empty parts in Gemini API response")
                    raise Exception("Empty response from Gemini API")
                    
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except httpx.RequestError as e:
            print(f"Gemini API request error: {str(e)}")
            raise Exception(f"Gemini API request error: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"Gemini API JSON decode error: {str(e)}")
            raise Exception(f"Invalid JSON response from Gemini API: {str(e)}")
        except Exception as e:
            if isinstance(e, asyncio.CancelledError):
                raise
            print(f"Unexpected error in call_gemini: {str(e)}")
            
            # Only retry on specific errors, raise others immediately
            if "rate limit" in str(e).lower() or "quota exceeded" in str(e).lower():
                print(f"Rate limit or quota error. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
                attempt += 1
                continue
            raise
            
    # If we've exhausted all retries
    raise Exception(f"Failed after {max_retries} attempts to call Gemini API due to rate limiting")

async def call_openai(prompt, model, api_key, temperature):
    """Call OpenAI API"""
    base_url = settings.OPENAI_API_BASE_URL
    url = f"{base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]

async def call_anthropic(prompt, model, api_key, temperature):
    """Call Anthropic API"""
    base_url = settings.ANTHROPIC_API_BASE_URL
    url = f"{base_url}/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Anthropic API error: {response.text}")
        
        result = response.json()
        return result["content"][0]["text"]

# --- Web Search Integration ---

async def search_web(query):
    """Search the web using available search API"""
    search_provider = settings.SEARCH_PROVIDER
    print(f"Using search provider: {search_provider}")
    
    try:
        if search_provider == "searxng":
            return await search_with_searxng(query)
        elif search_provider == "tavily":
            return await search_with_tavily(query)
        else:
            raise Exception(f"Unsupported search provider: {search_provider}")
    except Exception as e:
        print(f"Error in search_web: {str(e)}")
        raise

async def search_with_searxng(query):
    """Search the web using SearXNG with fallback instances"""
    # List of SearXNG instances to try in order
    instances = [
        os.getenv('SEARXNG_API_BASE_URL', 'https://searx.be/search'),
        "https://searx.tiekoetter.com/search",
        "https://search.mdosch.de/search",
        "https://search.privacyguides.net/search"
    ]
    
    # Custom user agent to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Parameters for the search
    params = {"q": query, "format": "json", "engines": "google"}
    
    # Try each instance until one works
    for instance_url in instances:
        print(f"Trying SearXNG instance: {instance_url}")
        
        try:
            async with httpx.AsyncClient() as client:
                print(f"Making request to SearXNG: {instance_url}?q={query}")
                response = await client.get(instance_url, params=params, headers=headers, timeout=30.0)
                
                if response.status_code == 403:
                    print(f"403 Forbidden from {instance_url}, trying next instance...")
                    continue
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"SearXNG API error response from {instance_url}: {error_text}")
                    continue
                
                try:
                    results = response.json()
                except json.JSONDecodeError as e:
                    print(f"SearXNG API JSON decode error from {instance_url}: {str(e)}, Response: {response.text[:200]}")
                    continue
                
                # Format the results into a list of dictionaries
                sources = []
                if "results" not in results or not results.get("results"):
                    print(f"No results from {instance_url}")
                    continue
                    
                for result in results.get("results", [])[:5]:  # Limit to first 5 results
                    if "content" in result and "url" in result:
                        sources.append({"url": result["url"], "content": result["content"]})
                
                if sources:
                    print(f"SearXNG instance {instance_url} returned {len(sources)} results")
                    return sources
                else:
                    print(f"No valid results from {instance_url}")
        except httpx.RequestError as e:
            print(f"SearXNG API request error from {instance_url}: {str(e)}")
    
    # If all instances failed, fall back to mock results
    print("All SearXNG instances failed, using fallback mock results")
    return [
        {
            "url": "https://example.com/result1",
            "content": f"This is a mock search result for query: {query}. The search providers are currently unavailable."
        },
        {
            "url": "https://example.com/result2",
            "content": "Please consider using Tavily search provider instead by setting SEARCH_PROVIDER=tavily in your .env file and adding a valid Tavily API key."
        }
    ]

async def search_with_tavily(query):
    """Search the web using Tavily"""
    tavily_api_key = settings.TAVILY_API_KEY
    if not tavily_api_key:
        raise Exception("No Tavily API key configured")
    
    tavily_url = settings.TAVILY_API_BASE_URL
    headers = {
        "Content-Type": "application/json",
        "x-api-key": tavily_api_key
    }
    payload = {
        "query": query,
        "search_depth": "advanced",
        "include_answer": False,
        "include_domains": [],
        "exclude_domains": []
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(tavily_url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Tavily API error: {response.text}")
        
        results = response.json()
        sources = []
        for result in results.get("results", [])[:5]:
            if "content" in result and "url" in result:
                sources.append({"url": result["url"], "content": result["content"]})
        
        return sources 