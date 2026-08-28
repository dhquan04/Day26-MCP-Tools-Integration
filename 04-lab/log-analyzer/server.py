"""MCP server phân tích file log của ứng dụng qua stdio."""

from __future__ import annotations

from pathlib import Path

from mcp.server.mcpserver import MCPServer


mcp = MCPServer("log-analyzer")

DATA_DIR = Path(__file__).resolve().parent / "data"
LOG_FILE = DATA_DIR / "app.log"
MAX_LIMIT = 200


def _validated_limit(limit: int) -> int:
    """Kiểm tra limit để tránh trả về lượng dữ liệu quá lớn."""
    if not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit phải nằm trong khoảng 1-{MAX_LIMIT}")
    return limit


def _read_log_lines() -> list[tuple[int, str]]:
    """Đọc file log được server quản lý, kèm số dòng bắt đầu từ 1."""
    if not LOG_FILE.is_file():
        raise FileNotFoundError(f"Không tìm thấy file log: {LOG_FILE}")

    with LOG_FILE.open("r", encoding="utf-8") as log_file:
        return [
            (line_number, line.rstrip("\r\n"))
            for line_number, line in enumerate(log_file, start=1)
        ]


def _format_result(line_number: int, content: str) -> dict[str, int | str]:
    """Chuẩn hóa một kết quả để client dễ xử lý."""
    parts = content.split(" ", maxsplit=3)
    timestamp = " ".join(parts[:2]) if len(parts) >= 2 else ""
    level = parts[2] if len(parts) >= 3 else "UNKNOWN"
    message = parts[3] if len(parts) >= 4 else content
    return {
        "line_number": line_number,
        "timestamp": timestamp,
        "level": level,
        "message": message,
        "raw": content,
    }


@mcp.tool()
def search_logs(keyword: str, limit: int = 50) -> list[dict[str, int | str]]:
    """Tìm các dòng log chứa keyword, không phân biệt chữ hoa/chữ thường.

    Args:
        keyword: Từ khóa cần tìm, ví dụ ERROR, WARNING hoặc timeout.
        limit: Số kết quả tối đa cần trả về, từ 1 đến 200.
    """
    keyword = keyword.strip()
    if not keyword:
        raise ValueError("keyword không được để trống")

    limit = _validated_limit(limit)
    matches = [
        _format_result(line_number, content)
        for line_number, content in _read_log_lines()
        if keyword.casefold() in content.casefold()
    ]
    return matches[:limit]


@mcp.tool()
def get_recent_errors(limit: int = 10) -> list[dict[str, int | str]]:
    """Lấy các log ERROR hoặc CRITICAL gần nhất, mới nhất đứng trước.

    Args:
        limit: Số lỗi gần nhất cần trả về, từ 1 đến 200.
    """
    limit = _validated_limit(limit)
    errors = [
        _format_result(line_number, content)
        for line_number, content in _read_log_lines()
        if " ERROR " in f" {content.upper()} "
        or " CRITICAL " in f" {content.upper()} "
    ]
    return list(reversed(errors[-limit:]))


if __name__ == "__main__":
    mcp.run()
