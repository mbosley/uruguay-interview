# API Reference

## REST API

### Base URL
```
http://localhost:8000
```

### Endpoints

#### POST /research
Start a new research job.

**Request Body:**
```json
{
  "question": "string",
  "provider": "moonshot" | "groq",
  "max_iterations": 10,
  "use_mock": false
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "started",
  "message": "Research job {job_id} started"
}
```

#### GET /research/{job_id}
Get the status of a research job.

**Response:**
```json
{
  "status": "pending" | "running" | "completed" | "failed",
  "question": "string",
  "results": {},
  "created_at": "ISO 8601 timestamp"
}
```

#### GET /interviews
Get list of all interviews.

**Response:**
```json
[
  {
    "id": "001",
    "title": "Interview 001",
    "date": "2025-05-28",
    "location": "Montevideo",
    "themes": ["healthcare", "education"],
    "turns": 150
  }
]
```

#### GET /interviews/{interview_id}
Get specific interview content.

**Response:**
```json
{
  "id": "001",
  "metadata": {},
  "turns": [],
  "annotation": {}
}
```

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "corpus_loaded": true
}
```

## WebSocket API

### Connection
```
ws://localhost:8000/research/{job_id}/stream
```

### Event Types

#### iteration_start
Signals the beginning of a new research iteration.

```json
{
  "type": "iteration_start",
  "iteration": 1,
  "data": {
    "current": 1,
    "max": 10
  },
  "timestamp": "ISO 8601"
}
```

#### thinking
Agent's reasoning process.

```json
{
  "type": "thinking",
  "iteration": 1,
  "data": {
    "content": "I'll start by exploring healthcare themes..."
  },
  "timestamp": "ISO 8601"
}
```

#### tool_call
Tool being invoked.

```json
{
  "type": "tool_call",
  "iteration": 1,
  "data": {
    "tool": "search_interviews",
    "args": {
      "query": "healthcare access"
    }
  },
  "timestamp": "ISO 8601"
}
```

#### tool_result
Result from tool execution.

```json
{
  "type": "tool_result",
  "iteration": 1,
  "data": {
    "tool": "search_interviews",
    "metadata": {
      "preview": "Found 15 matches...",
      "matches": 15
    }
  },
  "timestamp": "ISO 8601"
}
```

#### response_start
Indicates the agent is starting to generate the final response.

```json
{
  "type": "response_start",
  "timestamp": "ISO 8601"
}
```

#### response_end
Final research summary.

```json
{
  "type": "response_end",
  "data": {
    "response": "Based on my analysis...",
    "sources": ["Interview 001", "Interview 023"]
  },
  "timestamp": "ISO 8601"
}
```

#### error
Error during research.

```json
{
  "type": "error",
  "data": {
    "error": "Error message"
  },
  "timestamp": "ISO 8601"
}
```

## Research Tools API

### get_corpus_stats
Get overview statistics of the interview corpus.

**Parameters:** None

**Returns:**
```json
{
  "total_interviews": 37,
  "total_turns": 5510,
  "average_turns_per_interview": 149
}
```

### search_interviews
Search interview content with text or semantic search.

**Parameters:**
- `query` (string): Search query
- `max_results` (int, optional): Maximum results to return

**Returns:**
```json
{
  "matches": [
    {
      "interview_id": "001",
      "turn_number": 42,
      "speaker": "Ciudadano",
      "text": "...",
      "relevance_score": 0.95
    }
  ]
}
```

### list_interview_themes
Get all themes and their occurrences.

**Parameters:** None

**Returns:**
```json
{
  "themes": {
    "healthcare_access": {
      "count": 23,
      "interviews": ["001", "005", "012"]
    }
  }
}
```

### get_interview_turn
Retrieve a specific turn from an interview.

**Parameters:**
- `interview_turn` (string): Format "interview_id:turn_number"

**Returns:**
```json
{
  "interview_id": "001",
  "turn_number": 42,
  "speaker": "Ciudadano",
  "text": "Full turn text..."
}
```

### search_themes
Search across theme annotations.

**Parameters:**
- `keyword` (string): Theme keyword to search

**Returns:**
```json
{
  "themes": [
    {
      "theme": "healthcare_crisis",
      "interviews": ["001", "023"],
      "count": 15
    }
  ]
}
```

### get_interview_summary
Get AI-generated summary of an interview.

**Parameters:**
- `interview_id` (string): Interview ID

**Returns:**
```json
{
  "interview_id": "001",
  "summary": {
    "key_themes": ["healthcare", "education"],
    "main_concerns": "...",
    "suggestions": "..."
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |
| 1008 | WebSocket - Job not found |