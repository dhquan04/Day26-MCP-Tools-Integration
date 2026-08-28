"""Client cũ: vẫn gọi search_logs v1 trên production server."""

import asyncio
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
                result = await session.call_tool(
                    "search_logs", {"keyword": "timeout", "limit": 5}
                )
                print("Client cũ gọi search_logs v1 thành công:")
                for content in result.content:
                    if hasattr(content, "text"):
                        print(content.text)


if __name__ == "__main__":
    asyncio.run(main())
