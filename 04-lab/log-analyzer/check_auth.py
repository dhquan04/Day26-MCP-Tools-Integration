"""Kiểm tra HTTP status khi token sai hoặc bị thiếu."""

import asyncio
import os
import sys

import httpx


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SERVER_URL = os.getenv("LOG_MCP_URL", "http://127.0.0.1:8086/mcp")


async def check(name: str, token: str | None) -> None:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.post(SERVER_URL, json={})
    print(f"{name}: HTTP {response.status_code}")


async def main() -> None:
    await check("Token sai", "wrong-token")
    await check("Không có token", None)


if __name__ == "__main__":
    asyncio.run(main())
