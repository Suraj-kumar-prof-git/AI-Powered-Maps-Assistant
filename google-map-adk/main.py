import asyncio
import uuid
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from agent import root_agent, McpToolset
from dotenv import load_dotenv
import sys
import io

load_dotenv()
# Global variables for the session components
runner: Runner = None
session_service: InMemorySessionService = None
SESSION_ID: str = None
USER_ID: str = "suraj_kumar"
APP_NAME: str = "google_map_adk"
mcp_toolset: McpToolset = root_agent.tools

async def run_agent_session():
    """
    Sets up an in-memory session and runs the agent with a sample prompt.
    """
    await initialize_session()
    # format the query 
    content = types.Content(role = "user", parts= [types.Part(text=root_agent.instruction)])
    print(f"Created session with ID: {SESSION_ID}")
    print(f"\nSending prompt: \"{root_agent.instruction}\" to agent...\n")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    try:
        # 3. Run the agent asynchronously
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"🤖 Agent Response Event: {part.text}")
            elif event.type == 'agent_ended':
                print(f"--- Agent session ended ---")
    finally:
        print("Closing McpToolset connection...")
        await mcp_toolset.close()

async def initialize_session():
    """Sets up the initial session and runner."""
    global runner, session_service, SESSION_ID
    SESSION_ID = str(uuid.uuid4())
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    
    runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)
    
    print(f"--- Session Initialized (ID: {SESSION_ID}) ---")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def run_agent_turn(prompt: str):
    """Runs the agent for a single turn with the given prompt."""
    if not runner:
        print("Error: Session not initialized.")
        return

    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    
    print(f"\n>>>> Sending prompt: \"{prompt}\" to agent...")

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    # Print response parts as they arrive
                    print(f"🤖 Agent Response: {part.text}")
        elif event.type == 'agent_ended':
            # This marks the end of the *current turn*, not the whole session
            print(f"--- Turn ended ---")

async def interactive_loop():
    """The main interactive loop for conversation."""
    await initialize_session()
    
    try:
        while True:
            # Get user input from the console
            user_input = input("You: ")
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Ending session.")
                break
            
            if not user_input.strip():
                continue

            await run_agent_turn(user_input)
            
    finally:
        # Close the connection only when the user explicitly quits the loop
        print("Closing McpToolset connection...")
        await mcp_toolset.close()

def main():
    print("Executing agent using 'asyncio.run()'")
    try:
        asyncio.run(interactive_loop())
    except Exception as e:
        print(f"An error occurred during agent execution: {e}")

if __name__ == "__main__":
    main()