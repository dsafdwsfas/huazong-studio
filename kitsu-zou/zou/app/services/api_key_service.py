"""
API Key 管理服务

提供 API Key 的生成、验证、CRUD 和速率限制功能。
密钥格式: hz_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (40 字符)
明文 key 只在创建时返回一次，存储只保存 SHA256 哈希。
"""

import hashlib
import logging
import secrets
import time

from zou.app import db
from zou.app.models.api_key import ApiKey
from zou.app.utils import date_helpers

logger = logging.getLogger(__name__)

# --- Key Generation ---

KEY_PREFIX = "hz_live_"
KEY_RANDOM_LENGTH = 32  # 32 hex chars after prefix → 40 total


def generate_api_key():
    """
    生成 API Key。

    格式: hz_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (40 字符)

    Returns:
        dict: {
            key: "hz_live_xxx...",      # 明文（只返回一次）
            prefix: "hz_live_xxxx",     # 前缀（显示用）
            key_hash: "sha256..."       # 哈希（存储用）
        }
    """
    random_part = secrets.token_hex(KEY_RANDOM_LENGTH // 2)
    raw_key = f"{KEY_PREFIX}{random_part}"
    prefix = raw_key[:16]
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    return {
        "key": raw_key,
        "prefix": prefix,
        "key_hash": key_hash,
    }


# --- CRUD ---


def create_api_key(
    owner_id, name, scopes=None, rate_limit=100, expires_at=None
):
    """
    创建 API Key。

    Args:
        owner_id: 所有者 ID (person.id)
        name: 密钥名称（如 "Blender插件"）
        scopes: 权限范围列表
        rate_limit: 每分钟请求限制
        expires_at: 过期时间（可选）

    Returns:
        dict: 包含 key（明文，仅此一次）和 api_key 序列化数据
    """
    if scopes is None:
        scopes = ["assets:read"]

    key_data = generate_api_key()

    api_key = ApiKey.create(
        name=name,
        key_prefix=key_data["prefix"],
        key_hash=key_data["key_hash"],
        owner_id=owner_id,
        scopes=scopes,
        rate_limit=rate_limit,
        is_active=True,
        expires_at=expires_at,
        total_requests=0,
    )

    result = api_key.serialize()
    result["key"] = key_data["key"]  # 明文只在创建时返回
    return result


def validate_api_key(raw_key):
    """
    验证 API Key。

    1. 计算 hash
    2. 查询匹配的记录
    3. 检查 is_active
    4. 检查 expires_at
    5. 更新 last_used_at 和 total_requests

    Args:
        raw_key: 原始密钥字符串

    Returns:
        ApiKey 对象或 None
    """
    if not raw_key or not raw_key.startswith(KEY_PREFIX):
        return None

    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    api_key = ApiKey.get_by(key_hash=key_hash)

    if api_key is None:
        return None

    if not api_key.is_active:
        return None

    if api_key.expires_at:
        now = date_helpers.get_utc_now_datetime()
        if api_key.expires_at < now:
            return None

    # Update usage stats
    api_key.last_used_at = date_helpers.get_utc_now_datetime()
    api_key.total_requests = (api_key.total_requests or 0) + 1
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.warning("Failed to update API key usage stats", exc_info=True)

    return api_key


def list_api_keys(owner_id):
    """
    列出用户的所有 Key（不返回 hash）。

    Args:
        owner_id: 所有者 ID

    Returns:
        list[dict]: API Key 列表
    """
    keys = ApiKey.get_all_by(owner_id=owner_id)
    return [k.serialize() for k in keys]


def get_api_key(key_id, owner_id):
    """
    获取单个 API Key 详情。

    Args:
        key_id: API Key ID
        owner_id: 所有者 ID（验证所有权）

    Returns:
        dict 或 None
    """
    api_key = ApiKey.get(key_id)
    if api_key is None or str(api_key.owner_id) != str(owner_id):
        return None
    return api_key.serialize()


def revoke_api_key(key_id, owner_id):
    """
    撤销 Key（设 is_active=False）。

    Args:
        key_id: API Key ID
        owner_id: 所有者 ID

    Returns:
        dict 或 None
    """
    api_key = ApiKey.get(key_id)
    if api_key is None or str(api_key.owner_id) != str(owner_id):
        return None

    api_key.update({"is_active": False})
    return api_key.serialize()


def delete_api_key(key_id, owner_id):
    """
    删除 Key。

    Args:
        key_id: API Key ID
        owner_id: 所有者 ID

    Returns:
        bool
    """
    api_key = ApiKey.get(key_id)
    if api_key is None or str(api_key.owner_id) != str(owner_id):
        return False

    api_key.delete()
    return True


def update_api_key(key_id, owner_id, data):
    """
    更新 Key（名称、权限、限流）。

    Args:
        key_id: API Key ID
        owner_id: 所有者 ID
        data: dict — 允许字段: name, scopes, rate_limit, expires_at

    Returns:
        dict 或 None
    """
    api_key = ApiKey.get(key_id)
    if api_key is None or str(api_key.owner_id) != str(owner_id):
        return None

    updatable = {}
    for field in ("name", "scopes", "rate_limit", "expires_at"):
        if field in data:
            updatable[field] = data[field]

    if updatable:
        api_key.update(updatable)

    return api_key.serialize()


# --- Rate Limiting ---

# Redis-based sliding window rate limiter
_redis_client = None


def _get_redis():
    """Lazy-init Redis client for rate limiting."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            from zou.app import config

            _redis_client = redis.StrictRedis(
                host=config.KEY_VALUE_STORE["host"],
                port=int(config.KEY_VALUE_STORE["port"]),
                password=config.KEY_VALUE_STORE.get("password"),
                db=config.KV_RATE_LIMIT_DB_INDEX,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            _redis_client.ping()
        except Exception:
            logger.warning(
                "Redis unavailable for rate limiting; "
                "falling back to permissive mode."
            )
            _redis_client = None
    return _redis_client


def check_rate_limit(api_key):
    """
    检查速率限制（基于 Redis 滑动窗口）。

    Key: api_rate:{key_prefix}
    使用 Redis INCR + EXPIRE 实现简单计数器窗口。

    Args:
        api_key: ApiKey 模型实例

    Returns:
        dict: {allowed: bool, remaining: int, reset_at: int}
    """
    limit = api_key.rate_limit or 100
    window = 60  # 60 seconds

    redis_client = _get_redis()
    if redis_client is None:
        # Redis 不可用时放行
        return {
            "allowed": True,
            "remaining": limit,
            "reset_at": int(time.time()) + window,
        }

    redis_key = f"api_rate:{api_key.key_prefix}"

    try:
        pipe = redis_client.pipeline()
        pipe.incr(redis_key)
        pipe.ttl(redis_key)
        results = pipe.execute()

        current_count = results[0]
        ttl = results[1]

        # Set expiry on first request in window
        if ttl == -1:
            redis_client.expire(redis_key, window)
            ttl = window

        remaining = max(0, limit - current_count)
        reset_at = int(time.time()) + max(ttl, 0)

        return {
            "allowed": current_count <= limit,
            "remaining": remaining,
            "reset_at": reset_at,
        }
    except Exception:
        logger.warning(
            "Rate limit check failed; falling back to permissive mode.",
            exc_info=True,
        )
        return {
            "allowed": True,
            "remaining": limit,
            "reset_at": int(time.time()) + window,
        }


# --- Scope Checking ---

VALID_SCOPES = {
    "assets:read",
    "assets:write",
    "assets:delete",
    "categories:read",
    "search",
    "graph:read",
}


def check_scope(api_key, required_scope):
    """
    检查权限范围。

    Args:
        api_key: ApiKey 模型实例
        required_scope: 所需权限字符串

    Returns:
        bool
    """
    scopes = api_key.scopes or []
    if "*" in scopes:
        return True
    return required_scope in scopes
