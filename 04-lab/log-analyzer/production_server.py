"""Log Analyzer production: HTTP auth, tool v1/v2 và metadata resource."""

from __future__ import annotations

import json
import os
import secrets

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer

from server import get_recent_errors as get_recent_errors_impl
from server import search_logs as search_logs_impl


SERVER_VERSION = "2.0.0"
HOST = os.getenv("LOG_MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("LOG_MCP_PORT", "8086"))
AUTH_TOKEN = os.getenv("LOG_MCP_TOKEN")

if not AUTH_TOKEN:
    raise RuntimeError("Thiếu LOG_MCP_TOKEN. Hãy đặt token trước khi chạy server.")


class EnvironmentTokenVerifier(TokenVerifier):
    """Xác minh Bearer token lấy từ biến môi trường LOG_MCP_TOKEN."""

    async def verify_token(self, token: str) -> AccessToken | None:
        if not secrets.compare_digest(token, AUTH_TOKEN):
            return None
        return AccessToken(
            token=token,
            client_id="log-analyzer-client",
            scopes=["logs:read"],
        )


mcp = MCPServer(
    "log-analyzer-production",
    instructions=f"Log Analyzer MCP Server v{SERVER_VERSION}",
    auth=AuthSettings(
        issuer_url=f"http://{HOST}:{PORT}",
        resource_server_url=f"http://{HOST}:{PORT}",
    ),
    token_verifier=EnvironmentTokenVerifier(),
)


@mcp.tool()
def search_logs(keyword: str, limit: int = 50) -> list[dict[str, int | str]]:
    """[v1] Tìm log theo từ khóa. Giữ lại để tương thích client cũ."""
    return search_logs_impl(keyword, limit)


@mcp.tool()
def get_recent_errors(limit: int = 10) -> list[dict[str, int | str]]:
    """Lấy các log ERROR hoặc CRITICAL gần nhất."""
    return get_recent_errors_impl(limit)


@mcp.tool()
def search_logs_v2(
    keyword: str,
    limit: int = 50,
    level: str = "",
) -> dict:
    """[v2] Tìm log và trả metadata; có thể lọc theo level.

    Args:
        keyword: Từ khóa cần tìm.
        limit: Số kết quả tối đa, từ 1 đến 200.
        level: Level tùy chọn: INFO, WARNING, ERROR hoặc CRITICAL.
    """
    if not 1 <= limit <= 200:
        raise ValueError("limit phải nằm trong khoảng 1-200")

    normalized_level = level.strip().upper()
    allowed_levels = {"", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if normalized_level not in allowed_levels:
        raise ValueError("level phải là INFO, WARNING, ERROR hoặc CRITICAL")

    matches = search_logs_impl(keyword, limit=200)
    if normalized_level:
        matches = [item for item in matches if item["level"] == normalized_level]
    matches = matches[:limit]

    return {
        "api_version": "2.0",
        "query": {
            "keyword": keyword,
            "level": normalized_level or None,
            "limit": limit,
        },
        "total_matches": len(matches),
        "results": matches,
    }


@mcp.resource("server://info")
def server_info() -> str:
    """Metadata version, capabilities và hướng dẫn migration."""
    return json.dumps(
        {
            "name": "log-analyzer-production",
            "version": SERVER_VERSION,
            "transport": "streamable-http",
            "authentication": "bearer",
            "capabilities": [
                "log-search",
                "recent-errors",
                "level-filtering",
            ],
            "tool_versions": {
                "search_logs": "1.0.0",
                "search_logs_v2": "2.0.0",
                "get_recent_errors": "1.0.0",
            },
            "deprecated_tools": ["search_logs"],
            "replacements": {"search_logs": "search_logs_v2"},
            "migration_guide": (
                "Client cũ tiếp tục gọi search_logs. Client mới nên gọi "
                "search_logs_v2 để nhận metadata và lọc theo level."
            ),
        },
        ensure_ascii=False,
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
