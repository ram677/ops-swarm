import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from config.settings import settings

# 1. Dynamic Path Resolution
# This ensures the client finds the server script regardless of where you run the command from.
# CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# SERVER_SCRIPT_PATH = os.path.join(CURRENT_DIR, "mcp_server.py")

SERVER_SCRIPT_PATH = str(settings.MCP_SERVER_SCRIPT)

async def execute_tool(tool_name: str, arguments: dict = None) -> str:
    """
    Connects to the local MCP Server, executes a specific tool, and returns the result.
    
    Args:
        tool_name (str): The name of the tool (e.g., 'fetch_service_logs')
        arguments (dict): The parameters for the tool (e.g., {'service_name': 'auth'})
    
    Returns:
        str: The text output from the tool.
    """
    if arguments is None:
        arguments = {}

    # 2. Server Configuration
    # We tell the client how to launch the server process (stdIO communication)
    server_params = StdioServerParameters(
        command=sys.executable,  # Uses the current active Python interpreter
        args=[SERVER_SCRIPT_PATH],
        env=None  # Inherit environment variables (like PATH)
    )

    try:
        # 3. Establish Connection (Async Context Manager)
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Handshake with the server
                await session.initialize()

                # Call the tool
                # Note: MCP allows listing tools too: await session.list_tools()
                result = await session.call_tool(tool_name, arguments)

                # 4. Parse Response
                # MCP returns a list of content blocks (Text or Image). We want the text.
                if result.content and len(result.content) > 0:
                    return result.content[0].text
                
                return "Success (No output returned)."

    except Exception as e:
        return f"❌ MCP Client Error: Failed to execute '{tool_name}'. Details: {str(e)}"

# Optional: Test block to run this file directly
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing MCP Client...")
        response = await execute_tool("fetch_service_logs", {"service_name": "payment_gateway"})
        print(f"Response:\n{response}")

    asyncio.run(test())