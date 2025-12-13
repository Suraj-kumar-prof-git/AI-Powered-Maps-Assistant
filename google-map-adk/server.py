from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from agent import root_agent
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Globals for session management
session_service = InMemorySessionService()
active_sessions: Dict[str, Runner] = {}
mcp_toolset = root_agent.tools

APP_NAME_DEFAULT = "google_map_adk"

# Pydantic models matching your new route.ts request format

class MessagePart(BaseModel):
    text: str

class NewMessage(BaseModel):
    parts: List[MessagePart]

class RunRequest(BaseModel):
    app_name: str
    user_id: str
    session_id: Optional[str] = None
    new_message: NewMessage

class SessionCreateRequest(BaseModel):
    state: Optional[Dict[str, Any]] = {}

@app.on_event("shutdown")
async def shutdown_event():
    await mcp_toolset.close()

async def create_runner_for_session(app_name: str, user_id: str, session_id: str) -> Runner:
    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    runner = Runner(app_name=app_name, agent=root_agent, session_service=session_service)
    active_sessions[session_id] = runner
    return runner

@app.post("/apps/{app_name}/users/{user_id}/sessions/{session_id}")
async def create_session(
    app_name: str = Path(...),
    user_id: str = Path(...),
    session_id: str = Path(...),
    request: SessionCreateRequest = None
):
    """
    Endpoint to create or validate a session.
    Your route.ts calls this before /run to ensure session exists.
    """
    # Check if session already exists
    if session_id in active_sessions:
        return {"message": "Session already exists"}

    # Otherwise create session and runner
    await create_runner_for_session(app_name, user_id, session_id)
    return {"message": "Session created"}

@app.post("/run")
async def run_agent_turn(request: RunRequest):
    try:
        session_id = request.session_id
        if not session_id:
            # Generate a new session ID if not provided
            session_id = str(uuid.uuid4())

        # Get or create runner for session
        runner = active_sessions.get(session_id)
        if not runner:
            runner = await create_runner_for_session(request.app_name, request.user_id, session_id)

        # Extract prompt text from new_message parts (assuming at least one part)
        if not request.new_message.parts or len(request.new_message.parts) == 0:
            raise HTTPException(status_code=400, detail="new_message.parts must have at least one element")

        prompt_text = request.new_message.parts[0].text
        content = types.Content(role="user", parts=[types.Part(text=prompt_text)])

        response_events = []
        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=session_id,
            new_message=content
        ):
            response_events.append(event.model_dump(by_alias=True))

        return {
            "session_id": session_id,
            "user_id": request.user_id,
            "response_events": response_events
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/list-apps")
def list_apps():
    return {
        "status": "active",
        "app_name": APP_NAME_DEFAULT,
        "available_tools": [tool.__class__.__name__ for tool in mcp_toolset],
        "message": "ADK server is operational"
    }
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))  # default to 8000 if not set
    uvicorn.run("server:app", host="127.0.0.1", port=port, reload=True)