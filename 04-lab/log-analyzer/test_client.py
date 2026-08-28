"""Client kiểm thử Log Analyzer MCP Server qua stdio."""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def print_tool_result(result) -> None:
    """In toàn bộ content blocks mà MCP tool trả về."""
    for content in result.content:
        if hasattr(content, "text"):
            print(content.text)


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=["server.py"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools server cung cấp:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            search_result = await session.call_tool(
                "search_logs", {"keyword": "timeout", "limit": 5}
            )
            print("\nKết quả search_logs(keyword='timeout'):")
            print_tool_result(search_result)

            error_result = await session.call_tool(
                "get_recent_errors", {"limit": 3}
            )
            print("\nBa lỗi gần nhất:")
            print_tool_result(error_result)


if __name__ == "__main__":
    asyncio.run(main())
