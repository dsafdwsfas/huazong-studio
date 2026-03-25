"""
API Key 认证装饰器

从 Authorization: Bearer hz_live_xxx 或 X-API-Key: hz_live_xxx 获取 key，
验证后将 api_key 对象存入 g.api_key。
"""

from functools import wraps

from flask import request, g

from zou.app.services import api_key_service


def _extract_api_key(req):
    """
    从请求中提取 API Key。

    支持两种方式:
    1. Authorization: Bearer hz_live_xxx
    2. X-API-Key: hz_live_xxx
    """
    # Try Authorization header first
    auth_header = req.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token.startswith("hz_live_"):
            return token

    # Try X-API-Key header
    api_key_header = req.headers.get("X-API-Key", "")
    if api_key_header.startswith("hz_live_"):
        return api_key_header

    return None


def api_key_required(scope=None):
    """
    API Key 认证装饰器。

    验证 API Key 并检查权限和速率限制。
    成功后将 api_key 对象存入 g.api_key。

    Args:
        scope: 所需权限范围（如 "assets:read"）

    Usage:
        @api_key_required("assets:read")
        def get(self):
            ...
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            raw_key = _extract_api_key(request)
            if not raw_key:
                return {"error": "API key required"}, 401

            api_key = api_key_service.validate_api_key(raw_key)
            if not api_key:
                return {"error": "Invalid or expired API key"}, 401

            # Check rate limit
            rate_result = api_key_service.check_rate_limit(api_key)
            if not rate_result["allowed"]:
                return {
                    "error": "Rate limit exceeded",
                    "retry_after": rate_result["reset_at"],
                }, 429

            # Check scope
            if scope and not api_key_service.check_scope(api_key, scope):
                return {
                    "error": f"Insufficient scope. Required: {scope}"
                }, 403

            g.api_key = api_key
            g.rate_limit_info = rate_result

            return f(*args, **kwargs)

        return decorated

    return decorator


def add_rate_limit_headers(response_data, status_code):
    """
    为响应添加速率限制 headers 信息。

    由于 Flask-RESTful Resource 返回 tuple，
    我们将限流信息嵌入 meta 中。

    Args:
        response_data: 响应数据 dict
        status_code: HTTP 状态码

    Returns:
        tuple: (response_data, status_code, headers)
    """
    headers = {}
    rate_info = getattr(g, "rate_limit_info", None)
    api_key = getattr(g, "api_key", None)

    if rate_info and api_key:
        headers["X-RateLimit-Limit"] = str(api_key.rate_limit or 100)
        headers["X-RateLimit-Remaining"] = str(rate_info.get("remaining", 0))
        headers["X-RateLimit-Reset"] = str(rate_info.get("reset_at", 0))

    return response_data, status_code, headers
