"""
MCP 调试日志：httpx 拦截、请求/响应打印、API Key 脱敏
"""
import re
import json
import httpx
import logging


def _mask_key(url: str) -> str:
    """将 URL 中的 key 参数匿名化：key=abc123 → key=****"""
    return re.sub(r'(key=)[^&\s]+', r'\1****', url)


def _simplify_mcp_body(body_str: str) -> str:
    """简化 MCP 响应体打印：tools/list 只打印工具名和描述"""
    try:
        data = json.loads(body_str)
        if "result" in data and "tools" in data["result"]:
            tools = data["result"]["tools"]
            simplified = [
                {"name": t.get("name", ""), "description": t.get("description", "")[:80]}
                for t in tools
            ]
            return json.dumps({"tools_count": len(tools), "tools": simplified}, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass
    return body_str


class _HttpxKeyMaskFilter(logging.Filter):
    """过滤 httpx 内置日志，匿名化 URL 中的 key 参数。"""
    def filter(self, record):
        if record.args:
            record.args = tuple(
                _mask_key(str(a)) if isinstance(a, str) and "key=" in a else a
                for a in record.args
            )
        record.msg = _mask_key(str(record.msg))
        return True


_original_send = httpx.AsyncClient.send


async def _patched_send(self, request, *args, **kwargs):
    """拦截 httpx 请求，打印 MCP 请求/响应详情。"""
    url_str = str(request.url)
    body_str = ""

    if "mcp.amap.com" in url_str:
        body = request.content
        body_str = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)

        print(f"\n{'='*60}")
        print(f">>> MCP HTTP REQUEST")
        print(f"    Method: {request.method}")
        print(f"    URL:    {_mask_key(url_str)}")
        print(f"    Headers: {dict(request.headers)}")
        print(f"    Body: {body_str}")
        print(f"{'='*60}")

    response = await _original_send(self, request, *args, **kwargs)

    if "mcp.amap.com" in url_str:
        await response.aread()
        resp_body = response.content
        resp_str = resp_body.decode("utf-8", errors="replace") if isinstance(resp_body, bytes) else str(resp_body)
        resp_str = _simplify_mcp_body(resp_str)

        print(f"\n{'='*60}")
        print(f"<<< MCP HTTP RESPONSE")
        print(f"    Status:  {response.status_code}")
        print(f"    Headers: {dict(response.headers)}")
        print(f"    Body: {resp_str}")
        print(f"{'='*60}")

    return response


def setup_mcp_logging():
    """启用 MCP 调试日志：monkey-patch httpx + 过滤内置日志。"""
    httpx.AsyncClient.send = _patched_send
    logging.getLogger("httpx").addFilter(_HttpxKeyMaskFilter())
    logging.getLogger("httpcore").addFilter(_HttpxKeyMaskFilter())
    print("[MCP Debug] 已启用 MCP 请求/响应日志，API Key 自动脱敏")
