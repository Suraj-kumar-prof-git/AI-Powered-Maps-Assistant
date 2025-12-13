from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters
from prompt import instruction
import os
from dotenv import load_dotenv
load_dotenv()
env = os.environ.copy()

root_agent = LlmAgent(
    model='gemini-2.5-flash-lite',
    name='google_map_adk',
    description = "This is my first Gemini agent",
    instruction=instruction,
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command='npx',
                    args=[
                        "-y",
                        "@modelcontextprotocol/server-google-maps",
                    ],
                    env=env
                )
            ),
        ),
    ],
)