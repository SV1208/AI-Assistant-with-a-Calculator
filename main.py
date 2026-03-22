from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import stream_agent_response, get_agent_response
from fastapi.responses import StreamingResponse

app = FastAPI(title="Math AI Assistant API")

# Allow CORS so the frontend HTML file can communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str


@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_query = data.get("query")
    
    # Return a live stream instead of a static JSON response
    return StreamingResponse(
        stream_agent_response(user_query), 
        media_type="application/x-ndjson"
    )

# @app.post("/chat", response_model=ChatResponse)
# async def chat_endpoint(request: ChatRequest):
#     # Call the agent from agent.py
#     # Note: In a true production app, this would be an async call
#     response_text = get_agent_response(request.message)
#     return ChatResponse(reply=response_text)

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)