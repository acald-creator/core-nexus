import asyncio
import json
from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_SERVER_URL = "http://nexus-mcp.soc.svc.cluster.local:3001/sse"

async def run():
    print(f"Connecting to MCP server at {MCP_SERVER_URL}...")
    try:
        async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("Calling tool 'get_inference_hardware'...")
                result = await session.call_tool("get_inference_hardware", arguments={})
                print(result)
    except Exception as e:
        print(f"Failed to connect or call tool: {e}")

if __name__ == "__main__":
    asyncio.run(run())
