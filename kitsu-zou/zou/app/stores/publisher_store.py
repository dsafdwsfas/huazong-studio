import redis

from flask_socketio import SocketIO

from zou.app import config
from zou.app.utils.redis import get_redis_url

socketio = None


def publish(event, data):
    if socketio is not None:
        socketio.emit(event, data, namespace="/events")


def publish_to_room(event, data, room):
    """发布事件到指定房间（项目级隔离）"""
    if socketio is not None:
        socketio.emit(event, data, namespace="/events", room=room)


def publish_notification(user_id, notification_data):
    """
    向指定用户推送实时通知。
    用户房间名: user:{user_id}
    """
    if socketio is not None:
        socketio.emit(
            "notification:new",
            notification_data,
            namespace="/events",
            room=f"user:{user_id}",
        )


def init():
    """
    Initialize key value store that will be used for the event publishing.
    That way the main API takes advantage of Redis pub/sub capabilities to push
    events to the event stream API.
    """
    global socketio

    try:
        publisher_store = redis.StrictRedis(
            host=config.KEY_VALUE_STORE["host"],
            port=config.KEY_VALUE_STORE["port"],
            db=config.KV_EVENTS_DB_INDEX,
            password=config.KEY_VALUE_STORE["password"],
            decode_responses=True,
        )
        publisher_store.get("test")
        socketio = SocketIO(
            message_queue=get_redis_url(config.KV_EVENTS_DB_INDEX),
            cors_allowed_origins=[],
            cors_credentials=False,
        )
    except redis.ConnectionError:
        pass

    return socketio
