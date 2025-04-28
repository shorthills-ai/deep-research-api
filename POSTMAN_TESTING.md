# Testing the Deep Research API with Postman

This guide will help you test the Deep Research API using the provided Postman collection.

## Prerequisites

1. [Postman](https://www.postman.com/downloads/) installed on your computer
2. Deep Research Django API running locally
3. API keys set up in your `.env` file

## Importing the Collection

1. Open Postman
2. Click on "Import" button in the top left corner
3. Choose "File" > "Upload Files"
4. Navigate to the `Deep_Research_API.postman_collection.json` file and select it
5. Click "Import"

The collection should now appear in your workspace with all the pre-configured requests.

## Testing the API

### 1. Health Check

First, verify the API is up and running:

1. Select the "Health Check" request
2. Click the "Send" button
3. You should receive a `200 OK` response with `{"status": "ok", "version": "1.0.0"}`

### 2. Start a Research Process

To initiate a research process:

1. Select the "Start Research - Simple Test" request first to test basic functionality
2. Make sure the Content-Type header is set to "application/json"
3. Click the "Send" button
4. You should receive a `200 OK` response with a JSON object containing:
   - `id`: A unique identifier for this research (e.g., `research_12345`)
   - `status`: Initially set to `"processing"`
   - Other fields like `query`, `learnings` (empty array), etc.

**Important**: Note down the `id` value from the response as you'll need it for the next step.

### 3. Get Research Results

To check the status of your research and retrieve results:

1. Select the "Get Research Results" request
2. In the URL, replace `research_12345` with the actual ID you received in the previous step
3. Click the "Send" button
4. You will see the current status of the research

The research process happens asynchronously in the background. Keep polling this endpoint (every few seconds) until you see the `status` change from `"processing"` to either `"completed"`, `"no_results"`, or `"error"`.

When the status is `"completed"`, the response will contain:
- The final `report` with the research findings
- An array of `learnings` discovered during the research

### 4. Explore Available Models

To see which LLM models are available:

1. Select the "Get Available Models" request
2. Click the "Send" button
3. You will receive a list of available models grouped by provider

### 5. Check Search Providers

To see which search providers are supported:

1. Select the "Get Search Providers" request
2. Click the "Send" button
3. You will receive information about available search providers

## Troubleshooting

If you encounter errors:

### 400 Bad Request Errors

If you see a 400 error when starting research:

1. **Check JSON format**: Ensure your request body is valid JSON
2. **Required fields**: Make sure the "query" field is included
3. **Content-Type header**: Verify that the Content-Type header is set to "application/json"
4. **API Keys**: Check that your API keys are properly set in your .env file

### Connection Issues

1. **Server running**: Ensure the Django API is running at `http://localhost:8000`
2. **Port change**: If running on a different port, update the request URLs accordingly

### Environment Setup

1. **Environment variables**: Check that your `.env` file exists and has valid API keys
2. **Database migrations**: Run `python manage.py migrate` if you haven't already
3. **Python version**: Make sure you're using Python 3.9+ and have all dependencies installed

### Research Progress Issues

1. **Stuck in processing**: Check Django server logs for errors
2. **Invalid ID**: For "research not found" errors, verify that you're using the correct ID
3. **API Limits**: Some AI providers have rate limits that might cause timeouts

## Creating Your Own Requests

Feel free to duplicate and modify the existing requests to create your own research queries. The key endpoints are:

- `GET /api/` - Health check
- `POST /api/research` - Start research with custom parameters
- `GET /api/research/{research_id}` - Get research results
- `GET /api/research/{research_id}/stream` - Stream real-time research updates
- `GET /api/models` - Get available models
- `GET /api/search-providers` - Get search providers

## New Feature: Streaming API

The API now supports real-time streaming of research progress using Server-Sent Events (SSE).

### Testing the Streaming API

To test the streaming API, you have a few options:

#### Option 1: Using the HTML Demo Page

1. Open the `streaming_demo.html` file in your browser
2. Enter the correct API Base URL (default: `http://localhost:8000/api`)
3. Type your research query and click "Start Research"
4. Watch as the research results stream in real-time

#### Option 2: Using Curl

In a terminal, you can use curl to test the streaming endpoint:

```bash
curl -N http://localhost:8000/api/research/{research_id}/stream
```

Replace `{research_id}` with an actual research ID. The `-N` flag prevents buffering.

#### Option 3: Using JavaScript in a Browser Console

1. Start a research process using the Postman "Start Research" request
2. Note the `id` from the response
3. Open any webpage in your browser and open the developer console (F12)
4. Paste the following code, replacing `{research_id}` with your actual ID:

```javascript
const eventSource = new EventSource('http://localhost:8000/api/research/{research_id}/stream');
eventSource.onmessage = (event) => {
  console.log('Update:', JSON.parse(event.data));
};
eventSource.onerror = (err) => {
  console.error('SSE Error:', err);
  eventSource.close();
};
```

This will log all streaming updates to the console in real-time.

### Understanding the Streaming Response Format

The streaming API returns updates as Server-Sent Events (SSE) with the following format:

```
data: {"status": "generating_queries"}

data: {"learnings": ["Learning 1", "Learning 2"]}

data: {"report": "Markdown formatted report content..."}

data: {"status": "complete", "final": true}
```

Each event contains a different piece of information:

1. Status updates - indicate the current stage of the research process
2. Learning updates - new pieces of information discovered during research
3. Report update - the final report when it's ready
4. Final update - indicates the stream is complete and will be closed

This allows you to build interfaces that update in real-time as the research progresses. 