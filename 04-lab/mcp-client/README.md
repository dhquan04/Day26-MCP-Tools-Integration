# Weather Agent - Google ADK with Local MCP Server

AI agent built with **Google Agent Development Kit (ADK)** that uses tools from a local **MCP server** via Streamable HTTP transport.

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│   User Browser  │ ───> │  ADK Web UI      │ ───> │  Weather Agent      │
│   localhost:8000│      │  (Google ADK)    │      │  (Agent with MCP)   │
└─────────────────┘      └──────────────────┘      └─────────────────────┘
                                                             │
                                                             │ Streamable HTTP
                                                             ▼
                                                   ┌─────────────────────┐
                                                   │  MCP Server         │
                                                   │  localhost:8085/mcp │
                                                   │  FastMCP + Tools    │
                                                   └─────────────────────┘
                                                             │
                                                             ▼
                                                   ┌─────────────────────┐
                                                   │  WeatherAPI.com     │
                                                   └─────────────────────┘
```

## Features

- **Remote MCP Tools**: Connects to MCP server via Streamable HTTP
- **4 Weather and Air-Quality Tools**:
  - `get_current_weather(city)` - Real-time weather conditions
  - `get_forecast(city, days)` - Weather forecast up to 3 days
  - `get_air_quality(city)` - Current EPA category and pollutant concentrations
  - `health_check()` - Server health verification
- **Web Interface**: UI via ADK web
- **Streaming Responses**: Real-time AI responses

## Quick Start

### 1. Start the MCP Server (PowerShell)

```powershell
cd ../mcp-server
$env:WEATHERAPI_KEY = "your_weatherapi_key"
python -m uv run python weather.py
```

### 2. Setup Environment

```powershell
cd mcp-client

# Set your Google API key in this terminal
# Get free key from: https://aistudio.google.com/apikey
$env:GOOGLE_API_KEY = "your_google_api_key_here"
```

### 3. Install Dependencies

```powershell
python -m uv sync
```

### 4. Run the Agent

```powershell
python -m uv run adk web
```

### 5. Use the Agent

1. Open browser: http://localhost:8000
2. Select `weather_agent` from dropdown
3. Ask questions like:
   - "What's the weather in Brisbane?"
   - "Give me a 3-day forecast for Tokyo"
   - "How's the weather in New York?"

## Project Structure

```
mcp-client/
├── weather_agent/
│   ├── agent.py           # Main agent with MCP connection
│   └── __init__.py
├── pyproject.toml
├── .env                   # Environment variables (create this)
└── README.md
```

## Configuration

### Agent Configuration

In `weather_agent/agent.py`:

```python
MCP_SERVER_URL = "http://localhost:8085/mcp"

connection_params = StreamableHTTPConnectionParams(
    url=MCP_SERVER_URL,
    timeout=30.0,
)

root_agent = Agent(
    name="weather_agent",
    model="gemini-3.6-flash",
    tools=[weather_tools],
)
```

## Troubleshooting

### Agent won't connect to MCP server

1. **404 errors**: MCP server is not running or wrong port
   - Ensure the MCP server is running on port 8085
   - Check `MCP_SERVER_URL` in `agent.py`

2. **405 errors**: Port conflict with another application
   - Check what's running on the port: `lsof -i :8085`
   - Change port in both server and client if needed

3. **Timeout errors**: Server not started
   - Start the MCP server first, then the ADK client

### Fallback Mode

If MCP connection fails, the agent runs in fallback mode without tools.
Fix the connection and restart ADK web.

## Environment Variables

Đặt `GOOGLE_API_KEY` trong terminal chạy ADK. Có thể dùng `.env` local nếu muốn,
nhưng file này đã được `.gitignore` loại khỏi repository.

## Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [WeatherAPI](https://www.weatherapi.com/)
