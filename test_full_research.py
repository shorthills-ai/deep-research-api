import os
import asyncio
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('GOOGLE_GENERATIVE_AI_API_KEY')
BASE_URL = os.getenv('GOOGLE_GENERATIVE_AI_API_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/models')
MODEL = 'gemini-1.5-pro'

# Mock search results to skip the failing SearXNG search
MOCK_SEARCH_RESULTS = [
    {
        "url": "https://en.wikipedia.org/wiki/Quantum_computing",
        "content": "Quantum computing is the exploitation of collective properties of quantum states, such as superposition and entanglement, to perform computation. Devices that perform quantum computations are known as quantum computers. Though current quantum computers are too small to outperform usual computers for practical applications, they are believed to be capable of solving certain computational problems, such as integer factorization, substantially faster than classical computers."
    },
    {
        "url": "https://www.ibm.com/quantum/what-is-quantum-computing",
        "content": "Quantum computing is a rapidly-emerging technology that harnesses the laws of quantum mechanics to solve problems too complex for classical computers. Today, IBM Quantum makes real quantum hardware available to developers, researchers, and businesses. IBM offers cloud access to the most advanced quantum computers for exploring practical applications."
    },
    {
        "url": "https://www.nature.com/articles/d41586-023-00103-3",
        "content": "Recent advancements in quantum computing include error correction breakthroughs, new quantum processors with over 1000 qubits, and hybrid classical-quantum algorithms showing promise for near-term applications in chemistry simulation and optimization problems. Major tech companies and startups have invested billions in quantum computing research."
    }
]

async def generate_serp_queries(query):
    """Generate search queries using the LLM"""
    print(f"Generating search queries for '{query}'")
    
    prompt = f"""Given the following query from the user:
<query>{query}</query>

Based on previous user query, generate a list of SERP queries to further research the topic. Make sure each query is unique and not similar to each other.

Expected output format: JSON list with 'query' and 'researchGoal' fields."""
    
    try:
        # Call Gemini API
        import httpx
        url = f"{BASE_URL}/{MODEL}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": API_KEY}
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7}
        }
        
        print("Calling Gemini API for SERP queries")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, params=params, json=payload, timeout=30.0)
            
            if response.status_code != 200:
                print(f"API error: {response.status_code} - {response.text}")
                return []
            
            result = response.json()
            response_text = result["candidates"][0]["content"]["parts"][0]["text"]
            print(f"API response: {response_text[:200]}...")
            
            # Parse JSON
            try:
                if '[' in response_text:
                    json_start = response_text.find('[')
                    json_end = response_text.rfind(']') + 1
                    json_str = response_text[json_start:json_end]
                    queries = json.loads(json_str)
                else:
                    queries = json.loads(response_text)
                
                print(f"Parsed {len(queries)} queries")
                return queries[:2]  # Limit to 2 for testing
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                return [{"query": query, "researchGoal": "Research the main query"}]
    except Exception as e:
        print(f"Error generating queries: {str(e)}")
        return [{"query": query, "researchGoal": "Research the main query"}]

async def process_search_results(query, research_goal, search_results):
    """Process search results to extract learnings"""
    print(f"Processing search results for '{query}'")
    
    contents = [f'<content url="{result["url"]}">\n{result["content"]}\n</content>' for result in search_results]
    prompt = f"""Given the following contents from a SERP search for the query:
<query>{query}</query>.

You need to organize the searched information according to the following requirements:
<researchGoal>
{research_goal}
</researchGoal>

<contents>{"".join(contents)}</contents>

You need to think like a human researcher. Generate a list of learnings from the contents. Make sure each learning is unique and not similar to each other. The learnings should be to the point, as detailed and information dense as possible. Make sure to include any entities like people, places, companies, products, things, etc in the learnings, as well as any specific entities, metrics, numbers, and dates when available. The learnings will be used to research the topic further."""
    
    try:
        # Call Gemini API
        import httpx
        url = f"{BASE_URL}/{MODEL}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": API_KEY}
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7}
        }
        
        print("Calling Gemini API to process search results")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, params=params, json=payload, timeout=30.0)
            
            if response.status_code != 200:
                print(f"API error: {response.status_code} - {response.text}")
                return []
            
            result = response.json()
            response_text = result["candidates"][0]["content"]["parts"][0]["text"]
            print(f"API response: {response_text[:200]}...")
            
            # Extract learnings
            learnings = [line.strip() for line in response_text.split('\n') 
                         if line.strip() and not line.strip().startswith('#')]
            print(f"Extracted {len(learnings)} learnings")
            return learnings
    except Exception as e:
        print(f"Error processing search results: {str(e)}")
        return []

async def generate_final_report(query, learnings, custom_requirement=""):
    """Generate the final report based on learnings"""
    print(f"Generating final report for '{query}' with {len(learnings)} learnings")
    
    learnings_str = "\n".join([f"<learning>\n{learning}\n</learning>" for learning in learnings])
    requirement_str = f"\nPlease write according to the user's writing requirements:\n<requirement>{custom_requirement}</requirement>" if custom_requirement else ""
    
    prompt = f"""Given the following query from the user, write a final report on the topic using the learnings from research. Make it as detailed as possible, aim for 3 or more pages, include ALL the learnings from research:
<query>{query}</query>

Here are all the learnings from previous research:
<learnings>
{learnings_str}
</learnings>
{requirement_str}

You need to write this report like a human researcher. Contains diverse data information such as table, formulas, diagrams, etc. in the form of markdown syntax. DO NOT output anything other than report."""
    
    try:
        # Call Gemini API
        import httpx
        url = f"{BASE_URL}/{MODEL}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": API_KEY}
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.8}
        }
        
        print("Calling Gemini API to generate final report")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, params=params, json=payload, timeout=60.0)
            
            if response.status_code != 200:
                print(f"API error: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            response_text = result["candidates"][0]["content"]["parts"][0]["text"]
            print(f"Report generated ({len(response_text)} chars)")
            return response_text
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return None

async def conduct_research(query, custom_requirement=""):
    """Conduct the research process"""
    print(f"Starting research for: {query}")
    start_time = time.time()
    
    # 1. Generate SERP queries
    print("Step 1: Generate SERP queries")
    serp_queries = await generate_serp_queries(query)
    
    # 2. For each query, use mock search and process results
    print("Step 2: Searching and processing results")
    all_learnings = []
    
    for idx, query_obj in enumerate(serp_queries):
        sub_query = query_obj.get("query")
        research_goal = query_obj.get("researchGoal", "Research this topic thoroughly")
        
        print(f"Query {idx+1}/{len(serp_queries)}: {sub_query}")
        
        # Use mock search results
        search_results = MOCK_SEARCH_RESULTS
        print(f"Using {len(search_results)} mock search results")
        
        # Process results
        learnings = await process_search_results(sub_query, research_goal, search_results)
        all_learnings.extend(learnings)
        print(f"Total learnings so far: {len(all_learnings)}")
    
    # 3. Generate final report
    if all_learnings:
        print("Step 3: Generating final report")
        report = await generate_final_report(query, all_learnings, custom_requirement)
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"Research completed in {duration:.1f} seconds")
        
        return {
            "query": query,
            "learnings": all_learnings,
            "report": report,
            "duration": duration
        }
    else:
        print("No learnings found, research failed")
        return None

async def main():
    query = "Latest advancements in quantum computing"
    custom_requirement = "Focus on practical business applications"
    
    print("=== Testing Full Research Process ===")
    print(f"Query: {query}")
    print(f"Custom requirement: {custom_requirement}")
    print()
    
    result = await conduct_research(query, custom_requirement)
    
    if result:
        print("\n=== Research Results ===")
        print(f"Query: {result['query']}")
        print(f"Number of learnings: {len(result['learnings'])}")
        print("Sample learnings:")
        for i, learning in enumerate(result['learnings'][:5]):
            print(f"  {i+1}. {learning}")
            
        print("\nReport excerpt:")
        print(result['report'][:500] + "...")
        print(f"\nTotal time: {result['duration']:.1f} seconds")
        
        # Save results to file
        with open("research_results.json", "w") as f:
            json.dump({
                "query": result['query'],
                "learnings": result['learnings'],
                "report": result['report']
            }, f, indent=2)
            
        print("\nFull results saved to research_results.json")
    else:
        print("\nResearch failed!")

if __name__ == "__main__":
    asyncio.run(main()) 