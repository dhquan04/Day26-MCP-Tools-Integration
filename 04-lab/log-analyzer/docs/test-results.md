# Kết quả kiểm thử

Ngày kiểm thử: 2026-08-28.

## MCP local

```text
Tools server cung cấp:
- search_logs
- get_recent_errors

search_logs(keyword="timeout")
→ line 4, ERROR, Database connection timeout after 30 seconds

get_recent_errors(limit=3)
→ trả đủ 3 lỗi gần nhất, mới nhất trước
```

## Authentication

Production server chạy bằng Streamable HTTP tại `http://127.0.0.1:8086/mcp`.

```text
Token đúng  → MCP initialize và call_tool thành công
Token sai   → HTTP 401
Thiếu token → HTTP 401
```

## Versioning

```text
Client cũ gọi search_logs v1 thành công.

Client mới:
Server: log-analyzer-production v2.0.0
Deprecated: ["search_logs"]
Tool được chọn: search_logs_v2
Kết quả: 3 log ERROR cùng metadata api_version=2.0
```

Client mới đã đọc `server://info` trước, kiểm tra danh sách tools, ưu tiên v2 và
có logic fallback về v1.
