import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_SERVER_URL = "http://nexus-mcp.soc.svc.cluster.local:3001/sse"

async def run():
    print(f"Connecting to MCP server at {MCP_SERVER_URL}...")
    try:
        async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                print("Available MCP Tools:")
                for tool in tools.tools:
                    print(f"- {tool.name}: {tool.description}")
    except Exception as e:
        print(f"Failed to connect to MCP server: {e}")

if __name__ == "__main__":
    asyncio.run(run())
