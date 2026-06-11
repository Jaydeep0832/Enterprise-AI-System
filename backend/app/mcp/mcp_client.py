import asyncio
import json
import sys
import os
from typing import Dict, Any, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class EnterpriseMCPClient:
    def __init__(self, script_path: str = None):
        if not script_path:
            # Default to the mcp_server.py in the app directory
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script_path = os.path.join(app_dir, "mcp_server.py")
            
        self.server_parameters = StdioServerParameters(
            command=sys.executable,
            args=[script_path],
        )

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools from the MCP server."""
        async with stdio_client(self.server_parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                
                tools = []
                for tool in response.tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                    })
                return tools

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call a specific tool on the MCP server."""
        async with stdio_client(self.server_parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.call_tool(tool_name, arguments=arguments)
                
                if response.isError:
                    return f"Error from tool '{tool_name}': {response.content}"
                    
                # The response content is typically a list of content items (TextContent, etc.)
                result_text = "\n".join([item.text for item in response.content if hasattr(item, "text")])
                return result_text


# Helper for synchronous contexts (like agents)
def get_mcp_tools_sync():
    """Returns a list of tools available via MCP."""
    client = EnterpriseMCPClient()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an event loop but need to block (not ideal, but works for sync wrappers)
            # Actually, standard asyncio.run is better if not in a running loop
            pass
    except RuntimeError:
        pass
        
    return asyncio.run(client.list_tools())


def call_mcp_tool_sync(tool_name: str, **kwargs):
    """Call an MCP tool synchronously."""
    client = EnterpriseMCPClient()
    return asyncio.run(client.call_tool(tool_name, arguments=kwargs))
