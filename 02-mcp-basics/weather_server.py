"""MCP SERVER minh hoạ — công bố tool `get_weather` qua giao thức MCP.

Khác với function calling: tool nằm ở một server ĐỘC LẬP. Server tự "khai
báo" tool của mình; bất kỳ MCP client nào (Claude Code, Claude Desktop,
Cursor, hoặc weather_client.py) cũng cắm vào dùng được mà không cần biết
code bên trong.

Schema của tool được TỰ ĐỘNG sinh ra từ type hints + docstring.

Chạy trực tiếp:
    pip install -r ../requirements.txt
    python weather_server.py

Đăng ký với Claude Code (làm 1 lần, dùng mãi):
    claude mcp add weather -- python /đường/dẫn/tới/weather_server.py
"""

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("weather")

_MOCK_DB = {
    "Hanoi": "29°C, trời mưa",
    "Haiphong": "33°C, mưa rào",
    "Danang": "30°C, nhiều mây",
}

_MOCK_AIR_QUALITY = {
    "Hanoi": {"aqi": 87, "level": "Trung bình", "pm2_5": 28.4},
    "Haiphong": {"aqi": 72, "level": "Trung bình", "pm2_5": 22.1},
    "Danang": {"aqi": 41, "level": "Tốt", "pm2_5": 9.8},
}


@mcp.tool()
def get_weather(city: str) -> str:
    """Lấy thời tiết hiện tại của một thành phố."""
    return f"{city}: {_MOCK_DB.get(city, '28°C, không có dữ liệu chi tiết')}"


@mcp.tool()
def get_air_quality(city: str) -> str:
    """Lấy chỉ số chất lượng không khí AQI và nồng độ PM2.5 của một thành phố."""
    data = _MOCK_AIR_QUALITY.get(city)
    if data is None:
        return f"{city}: không có dữ liệu chất lượng không khí"
    return (
        f"{city}: AQI {data['aqi']} ({data['level']}), "
        f"PM2.5 {data['pm2_5']} µg/m³"
    )


if __name__ == "__main__":
    mcp.run()  # mặc định chạy qua stdio
