# AI Assistant with a Calculator

An AI-powered math assistant that combines:
- A FastAPI backend
- A LangGraph agent with tool-calling
- A Python REPL tool for accurate calculations
- A simple web chat UI with Markdown and MathJax rendering

The assistant is designed to always use Python execution for calculations instead of mental math.

## Demo

YouTube demo: https://www.youtube.com/watch?v=pQZF0oIOzWc

## Features

- AI chat interface for math questions
- Streaming responses from backend to frontend (NDJSON)
- Automatic Python tool invocation for calculations
- Math rendering with LaTeX support (MathJax)
- Conversation memory support using LangGraph checkpointing

## Tech Stack

### Languages
- Python
- JavaScript
- HTML/CSS

### Backend
- FastAPI
- Uvicorn
- Pydantic
- LangChain Core
- LangGraph
- LangChain Ollama

### Math and Scientific Libraries
- NumPy
- SciPy
- SymPy

### Frontend
- Vanilla JavaScript
- Tailwind CSS (CDN)
- Marked.js (Markdown parser)
- MathJax (LaTeX rendering)

### Runtime / Tools
- Ollama (local LLM runtime)
- Model used in code: qwen2.5

## Project Structure

```text
AI Assistant with a Calculator/
|-- agent.py          # LangGraph agent, tool, and streaming logic
|-- main.py           # FastAPI application and /chat endpoint
|-- index.html        # Chat UI
|-- script.js         # Frontend chat + streaming client logic
|-- requirements.txt  # Python dependencies
|-- README.md
```

## How It Works

1. User asks a math question in the browser.
2. Frontend sends request to backend at /chat.
3. FastAPI streams events from the agent as NDJSON.
4. Agent decides whether to call python_repl_tool.
5. Tool executes Python code and returns real output.
6. Final answer is streamed back to UI and rendered.

## Prerequisites

Before running, ensure you have:
- Python 3.10+
- pip
- Ollama installed and running
- qwen2.5 model available in Ollama

## Installation

1. Clone or open this folder in your editor.

2. Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install missing LangGraph/LangChain packages if needed:

```bash
pip install langgraph langchain-core langchain-ollama
```

## Ollama Setup

1. Start Ollama (if not already running).
2. Pull the model used by this project:

```bash
ollama pull qwen2.5
```

3. Keep Ollama service running while using the app.

## Run the Project

1. Start the backend server:

```bash
python main.py
```

The API will run on:
- http://0.0.0.0:8000

2. Open the frontend:
- Open index.html in your browser

The frontend sends requests to:
- http://localhost:8000/chat

## API Reference

### POST /chat

Request body:

```json
{
	"query": "What is the derivative of x^2 + 3x?"
}
```

Response type:
- application/x-ndjson (streamed)

Stream event examples:

```json
{"type":"tool_start","message":"Calling Python tool..."}
{"type":"final_answer","content":"The derivative is 2x + 3."}
```

## Development Notes

- The main tool is python_repl_tool in agent.py.
- The system prompt enforces tool usage for all calculations.
- The frontend parses NDJSON chunks and reacts to tool_start/final_answer events.
- Conversation state is maintained via LangGraph MemorySaver and thread_id.

## Common Issues

1. Connection error from frontend:
- Ensure backend is running on port 8000.
- Check firewall or port conflicts.

2. Model not found:
- Run ollama pull qwen2.5.

3. No response or tool errors:
- Confirm Ollama service is active.
- Check terminal logs from FastAPI.

4. Math not rendering:
- Ensure internet is available (CDN scripts for Tailwind/Marked/MathJax).
