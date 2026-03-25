"""
在线状态管理服务

使用 Redis 存储用户在线状态和当前浏览位置。
支持 50+ 人同时在线的场景。

数据结构：
- huazong:presence:{user_id} — Hash: {socket_id, page, project_id, last_seen}
- huazong:online_users — Set: 所有在线用户 ID
- huazong:project_users:{project_id} — Set: 项目内在线用户
"""

import json
import logging
import time

import redis

from zou.app import config
from zou.app.utils.redis import get_redis_url

logger = logging.getLogger(__name__)

PRESENCE_TTL = 120  # 在线状态过期时间（秒），心跳间隔应为 TTL/3
PREFIX = "huazong:presence"

_redis_client = None


def _get_redis():
    """获取 Redis 客户端（延迟初始化）"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.StrictRedis(
                host=config.KEY_VALUE_STORE["host"],
                port=config.KEY_VALUE_STORE["port"],
                db=config.KV_EVENTS_DB_INDEX,
                password=config.KEY_VALUE_STORE["password"],
                decode_responses=True,
            )
            _redis_client.ping()
        except Exception as e:
            logger.warning("Redis 连接失败，在线状态不可用: %s", e)
            _redis_client = None
    return _redis_client


def user_connected(user_id, socket_id, user_name=""):
    """用户连接时注册在线状态"""
    r = _get_redis()
    if not r:
        return

    key = f"{PREFIX}:{user_id}"
    pipe = r.pipeline()
    pipe.hset(key, mapping={
        "socket_id": socket_id,
        "user_name": user_name,
        "page": "",
        "project_id": "",
        "connected_at": str(int(time.time())),
        "last_seen": str(int(time.time())),
    })
    pipe.expire(key, PRESENCE_TTL)
    pipe.sadd(f"{PREFIX}:online", user_id)
    pipe.execute()

    logger.info("用户上线: %s (socket=%s)", user_id, socket_id)


def user_disconnected(user_id):
    """用户断开时清除在线状态"""
    r = _get_redis()
    if not r:
        return

    key = f"{PREFIX}:{user_id}"
    # 获取当前项目以清除项目在线列表
    project_id = r.hget(key, "project_id")

    pipe = r.pipeline()
    pipe.delete(key)
    pipe.srem(f"{PREFIX}:online", user_id)
    if project_id:
        pipe.srem(f"{PREFIX}:project:{project_id}", user_id)
    pipe.execute()

    logger.info("用户离线: %s", user_id)


def heartbeat(user_id, page="", project_id=""):
    """心跳更新：刷新 TTL 和当前页面"""
    r = _get_redis()
    if not r:
        return

    key = f"{PREFIX}:{user_id}"
    old_project = r.hget(key, "project_id") or ""

    pipe = r.pipeline()
    pipe.hset(key, mapping={
        "page": page,
        "project_id": project_id,
        "last_seen": str(int(time.time())),
    })
    pipe.expire(key, PRESENCE_TTL)
    pipe.sadd(f"{PREFIX}:online", user_id)

    # 更新项目在线列表
    if project_id and project_id != old_project:
        if old_project:
            pipe.srem(f"{PREFIX}:project:{old_project}", user_id)
        pipe.sadd(f"{PREFIX}:project:{project_id}", user_id)
    elif not project_id and old_project:
        pipe.srem(f"{PREFIX}:project:{old_project}", user_id)

    pipe.execute()


def get_online_users():
    """获取所有在线用户 ID 列表"""
    r = _get_redis()
    if not r:
        return []

    user_ids = r.smembers(f"{PREFIX}:online")
    # 验证每个用户的 presence key 是否仍然存在（TTL 过期清理）
    result = []
    for uid in user_ids:
        if r.exists(f"{PREFIX}:{uid}"):
            result.append(uid)
        else:
            r.srem(f"{PREFIX}:online", uid)
    return result


def get_online_users_detail():
    """获取所有在线用户的详细信息"""
    r = _get_redis()
    if not r:
        return []

    user_ids = get_online_users()
    result = []
    for uid in user_ids:
        info = r.hgetall(f"{PREFIX}:{uid}")
        if info:
            result.append({
                "user_id": uid,
                "page": info.get("page", ""),
                "project_id": info.get("project_id", ""),
                "user_name": info.get("user_name", ""),
                "last_seen": int(info.get("last_seen", 0)),
            })
    return result


def get_project_online_users(project_id):
    """获取项目内在线用户"""
    r = _get_redis()
    if not r:
        return []

    user_ids = r.smembers(f"{PREFIX}:project:{project_id}")
    result = []
    for uid in user_ids:
        info = r.hgetall(f"{PREFIX}:{uid}")
        if info:
            result.append({
                "user_id": uid,
                "page": info.get("page", ""),
                "user_name": info.get("user_name", ""),
            })
    return result


def get_user_count():
    """获取在线用户总数"""
    r = _get_redis()
    if not r:
        return 0
    return r.scard(f"{PREFIX}:online")
