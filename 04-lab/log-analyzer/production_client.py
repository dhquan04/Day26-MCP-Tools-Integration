"""Client mới: đọc server://info rồi chọn tool version phù hợp."""

import asyncio
import json
import os
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SERVER_URL = os.getenv("LOG_MCP_URL", "http://127.0.0.1:8086/mcp")
TOKEN = os.getenv("LOG_MCP_TOKEN")


async def main() -> None:
    if not TOKEN:
        raise RuntimeError("Thiếu LOG_MCP_TOKEN")

    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {TOKEN}"}
    ) as http_client:
        async with streamable_http_client(
            SERVER_URL, http_client=http_client
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                resource = await session.read_resource("server://info")
                metadata = json.loads(resource.contents[0].text)
                tools = await session.list_tools()
                tool_names = {tool.name for tool in tools.tools}

                selected_tool = (
                    "search_logs_v2"
                    if "search_logs_v2" in tool_names
                    else "search_logs"
                )
                arguments = {"keyword": "ERROR", "limit": 10}
                if selected_tool == "search_logs_v2":
                    arguments["level"] = "ERROR"

                print(f"Server: {metadata['name']} v{metadata['version']}")
                print(f"Deprecated: {metadata['deprecated_tools']}")
                print(f"Tool được chọn: {selected_tool}")

                result = await session.call_tool(selected_tool, arguments)
                print("Kết quả:")
                for content in result.content:
                    if hasattr(content, "text"):
                        print(content.text)


if __name__ == "__main__":
    asyncio.run(main())
