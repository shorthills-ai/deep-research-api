# Deep Research Django API

A Django-based API for generating comprehensive research reports using Large Language Models. This project is a Python/Django implementation of the [Deep Research](https://github.com/u14app/deep-research) functionality.

## Features

- Generate in-depth research reports on any topic
- Utilize various AI models (Gemini, OpenAI, Anthropic)
- Web search integration for up-to-date information
- Customizable report generation
- Asynchronous processing for long-running research
- Simple RESTful API
- Django admin interface to view and manage research

## Setup

### Prerequisites

- Python 3.9+
- pip (Python package manager)

### Installation

1. Clone this repository or copy files to your project:

```bash
git clone <your-repository-url>
cd django-api
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the template:

```bash
python create_env_example.py
cp .env.example .env
```

5. Edit the `.env` file and add your API keys:

   The application requires API keys to function properly:
   - **Google API Key**: Required for using Gemini models
   - **OpenAI API Key**: Required for using GPT models
   - **Anthropic API Key**: Required for using Claude models
   - **Tavily API Key**: Optional, for using Tavily search instead of SearXNG

   You can use the included testing script to verify your API key configuration:
   ```bash
   python test_api_keys.py
   ```
   
   For detailed instructions on setting up API keys, see `SETUP_API_KEYS.md`.

### Search Provider Configuration

By default, the application uses SearXNG for web searches, which doesn't require an API key. However, public SearXNG instances may have reliability issues (403 errors, rate limiting).

For more reliable results, we recommend using Tavily:

1. Get a Tavily API key from https://tavily.com/
2. Update your `.env` file:
   ```
   SEARCH_PROVIDER=tavily
   TAVILY_API_KEY=tvly-your-actual-tavily-key
   ```

The application will automatically try multiple SearXNG instances if one fails, but Tavily offers better reliability for production use.

6. Run database migrations:

```bash
python manage.py migrate
```

7. Create a superuser for the admin interface (optional):

```bash
python manage.py createsuperuser
```

### Running the API

Start the Django development server:

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/` and the admin interface at `http://localhost:8000/admin/`.

## API Documentation

### Endpoints

- `GET /api/` - API health check
- `POST /api/research` - Start a new research process
- `GET /api/research/{research_id}` - Get research status and results
- `GET /api/models` - Get available LLM models
- `GET /api/search-providers` - Get available search providers

### Example API Usage

#### Start Research

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Latest advancements in quantum computing", "model": "gemini-1.5-pro"}'
```

Response:
```json
{
  "id": "research_12345",
  "status": "processing",
  "query": "Latest advancements in quantum computing",
  "learnings": [],
  "report": null,
  "error": null
}
```

#### Get Research Results

```bash
curl http://localhost:8000/api/research/research_12345
```

Response:
```json
{
  "id": "research_12345",
  "status": "completed",
  "query": "Latest advancements in quantum computing",
  "learnings": ["IBM unveiled 100-qubit processor", "..."],
  "report": "# Latest Advancements in Quantum Computing\n\n...",
  "error": null
}
```

## Python Integration Example

```python
import requests
import time

def get_research_report(query):
    # Start research
    response = requests.post(
        "http://localhost:8000/api/research",
        json={"query": query}
    )
    data = response.json()
    research_id = data["id"]
    
    # Poll for results
    while True:
        response = requests.get(f"http://localhost:8000/api/research/{research_id}")
        data = response.json()
        if data["status"] == "completed":
            return data["report"]
        elif data["status"] == "error":
            raise Exception(f"Research error: {data.get('error')}")
        time.sleep(5)  # Wait 5 seconds before polling again

# Usage
report = get_research_report("Latest advancements in renewable energy")
print(report)
```

## Project Structure

- `manage.py` - Django management script
- `deep_research/` - Main Django project directory
  - `settings.py` - Project settings
  - `urls.py` - Main URL configuration
- `research/` - Research app
  - `models.py` - Research data models
  - `views.py` - API views and core functionality
  - `utils.py` - Utility functions for prompts
  - `urls.py` - App URL configuration

## Production Deployment

For production deployment, consider:

1. Using a production-ready web server (Nginx + Gunicorn)
2. Setting DEBUG=False and generating a secure SECRET_KEY
3. Implementing proper user authentication
4. Using a more robust database (PostgreSQL)
5. Setting up SSL/TLS
6. Configuring proper ALLOWED_HOSTS

## License

MIT License

## New Feature: Streaming Research API

The API now supports real-time streaming of research progress using Server-Sent Events (SSE).

### Endpoint

```
GET /api/research/{research_id}/stream
```

This endpoint provides real-time updates about the research process as an event stream.

### Client-side Implementation

Here's an example of how to consume the streaming API using JavaScript:

```javascript
// Start a new research
async function startResearch(query) {
    const response = await fetch('/api/research', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
    });
    
    const data = await response.json();
    return data.id;
}

// Connect to the streaming API to get real-time updates
function connectToStream(researchId, callbacks) {
    const eventSource = new EventSource(`/api/research/${researchId}/stream`);
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Handle different types of updates
        if (data.status) {
            callbacks.onStatusUpdate?.(data.status);
        }
        
        if (data.learnings) {
            callbacks.onNewLearnings?.(data.learnings);
        }
        
        if (data.report) {
            callbacks.onReportGenerated?.(data.report);
        }
        
        // Close connection when research is complete
        if (data.final) {
            eventSource.close();
            callbacks.onComplete?.();
        }
    };
    
    eventSource.onerror = (error) => {
        console.error('Stream error:', error);
        eventSource.close();
        callbacks.onError?.(error);
    };
    
    return eventSource;
}

// Example usage
async function runResearchWithUpdates() {
    const researchId = await startResearch('Impact of climate change on coral reefs');
    
    const updates = {
        statusEl: document.getElementById('status'),
        learningsEl: document.getElementById('learnings'),
        reportEl: document.getElementById('report')
    };
    
    connectToStream(researchId, {
        onStatusUpdate: (status) => {
            updates.statusEl.textContent = `Status: ${status}`;
        },
        onNewLearnings: (learnings) => {
            const list = updates.learningsEl;
            
            for (const learning of learnings) {
                const item = document.createElement('li');
                item.textContent = learning;
                list.appendChild(item);
            }
        },
        onReportGenerated: (report) => {
            updates.reportEl.innerHTML = report;
        },
        onComplete: () => {
            updates.statusEl.textContent = 'Research completed!';
        },
        onError: (error) => {
            updates.statusEl.textContent = `Error: ${error}`;
        }
    });
}
```

### Complete Usage Example HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deep Research - Streaming Example</title>
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .status {
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .section {
            margin-bottom: 30px;
        }
        h2 {
            border-bottom: 1px solid #ccc;
            padding-bottom: 10px;
        }
        button {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        #learnings {
            padding-left: 20px;
        }
        #report {
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <h1>Deep Research - Streaming Example</h1>
    
    <div class="section">
        <input type="text" id="query" placeholder="Enter your research query" style="width: 70%; padding: 10px;">
        <button onclick="runResearch()">Start Research</button>
    </div>
    
    <div class="status" id="status">Status: Ready</div>
    
    <div class="section">
        <h2>Learnings</h2>
        <ul id="learnings"></ul>
    </div>
    
    <div class="section">
        <h2>Final Report</h2>
        <div id="report"></div>
    </div>
    
    <script>
        async function startResearch(query) {
            const response = await fetch('/api/research', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            
            const data = await response.json();
            return data.id;
        }
        
        function connectToStream(researchId, callbacks) {
            const eventSource = new EventSource(`/api/research/${researchId}/stream`);
            
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.status) {
                    callbacks.onStatusUpdate?.(data.status);
                }
                
                if (data.learnings) {
                    callbacks.onNewLearnings?.(data.learnings);
                }
                
                if (data.report) {
                    callbacks.onReportGenerated?.(data.report);
                }
                
                if (data.final) {
                    eventSource.close();
                    callbacks.onComplete?.();
                }
            };
            
            eventSource.onerror = (error) => {
                console.error('Stream error:', error);
                eventSource.close();
                callbacks.onError?.(error);
            };
            
            return eventSource;
        }
        
        async function runResearch() {
            // Reset UI
            document.getElementById('learnings').innerHTML = '';
            document.getElementById('report').innerHTML = '';
            document.getElementById('status').textContent = 'Status: Starting research...';
            
            const query = document.getElementById('query').value;
            if (!query) {
                document.getElementById('status').textContent = 'Status: Please enter a query';
                return;
            }
            
            try {
                const researchId = await startResearch(query);
                
                const updates = {
                    statusEl: document.getElementById('status'),
                    learningsEl: document.getElementById('learnings'),
                    reportEl: document.getElementById('report')
                };
                
                connectToStream(researchId, {
                    onStatusUpdate: (status) => {
                        updates.statusEl.textContent = `Status: ${status}`;
                    },
                    onNewLearnings: (learnings) => {
                        const list = updates.learningsEl;
                        
                        for (const learning of learnings) {
                            const item = document.createElement('li');
                            item.textContent = learning;
                            list.appendChild(item);
                        }
                    },
                    onReportGenerated: (report) => {
                        updates.reportEl.innerHTML = report;
                    },
                    onComplete: () => {
                        updates.statusEl.textContent = 'Status: Research completed!';
                    },
                    onError: (error) => {
                        updates.statusEl.textContent = `Status: Error during research`;
                    }
                });
            } catch (error) {
                document.getElementById('status').textContent = `Status: Error - ${error.message}`;
            }
        }
    </script>
</body>
</html>
```

You can save this HTML file and use it as a standalone demo of the streaming API functionality. 