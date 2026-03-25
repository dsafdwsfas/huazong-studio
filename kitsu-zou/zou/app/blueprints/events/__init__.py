from flask import Blueprint
from zou.app.utils.api import configure_api_from_blueprint

from zou.app.blueprints.events.resources import (
    EventsResource,
    LoginLogsResource,
)
from zou.app.blueprints.events.realtime_resources import (
    OnlineUsersResource,
    ProjectOnlineUsersResource,
    HeartbeatResource,
    EntityLockResource,
)

routes = [
    ("/data/events/last", EventsResource),
    ("/data/events/login-logs/last", LoginLogsResource),
    ("/data/online-users", OnlineUsersResource),
    ("/data/projects/<project_id>/online-users", ProjectOnlineUsersResource),
    ("/data/heartbeat", HeartbeatResource),
    ("/data/entities/<entity_id>/check-lock", EntityLockResource),
]

blueprint = Blueprint("events", "events")
api = configure_api_from_blueprint(blueprint, routes)
