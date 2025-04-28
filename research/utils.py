from datetime import datetime

def get_system_prompt():
    """Get the system prompt for LLM interactions"""
    now = datetime.now().isoformat()
    return f"""You are an expert researcher. Today is {now}. Follow these instructions when responding:
- You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.
- The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.
- Be highly organized.
- Suggest solutions that I didn't think about.
- Be proactive and anticipate my needs.
- Treat me as an expert in all subject matter.
- Mistakes erode my trust, so be accurate and thorough.
- Provide detailed explanations, I'm comfortable with lots of detail.
- Value good arguments over authorities, the source is irrelevant.
- Consider new technologies and contrarian ideas, not just the conventional wisdom.
- You may use high levels of speculation or prediction, just flag it for me."""

def generate_serp_queries_prompt(query):
    """Generate prompt to create SERP queries"""
    return f"""Given the following query from the user:
<query>{query}</query>

Based on previous user query, generate a list of SERP queries to further research the topic. Make sure each query is unique and not similar to each other.

Expected output format: JSON list with 'query' and 'researchGoal' fields."""

def process_search_result_prompt(query, research_goal, results):
    """Generate prompt to process search results"""
    contents = [f'<content url="{result["url"]}">\n{result["content"]}\n</content>' for result in results]
    return f"""Given the following contents from a SERP search for the query:
<query>{query}</query>.

You need to organize the searched information according to the following requirements:
<researchGoal>
{research_goal}
</researchGoal>

<contents>{"".join(contents)}</contents>

You need to think like a human researcher. Generate a list of learnings from the contents. Make sure each learning is unique and not similar to each other. The learnings should be to the point, as detailed and information dense as possible. Make sure to include any entities like people, places, companies, products, things, etc in the learnings, as well as any specific entities, metrics, numbers, and dates when available. The learnings will be used to research the topic further."""

def write_final_report_prompt(query, learnings, requirement=""):
    """Generate prompt to write the final report"""
    learnings_str = "\n".join([f"<learning>\n{learning}\n</learning>" for learning in learnings])
    requirement_str = f"\nPlease write according to the user's writing requirements:\n<requirement>{requirement}</requirement>" if requirement else ""
    
    return f"""Given the following query from the user, write a final report on the topic using the learnings from research. Make it as detailed as possible, aim for 3 or more pages, include ALL the learnings from research:
<query>{query}</query>

Here are all the learnings from previous research:
<learnings>
{learnings_str}
</learnings>
{requirement_str}

You need to write this report like a human researcher. Contains diverse data information such as table, formulas, diagrams, etc. in the form of markdown syntax. DO NOT output anything other than report.""" 