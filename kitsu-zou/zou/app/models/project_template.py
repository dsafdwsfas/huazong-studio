from sqlalchemy.dialects.postgresql import JSONB

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class ProjectTemplate(db.Model, BaseMixin, SerializerMixin):
    """
    A project template stores reusable project configuration
    (production type, style, task types, asset types, task statuses)
    for quick project creation.
    """

    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text(), default="")

    # Source project settings
    production_type = db.Column(db.String(20), default="short")
    production_style = db.Column(db.String(20), default="2d3d")
    fps = db.Column(db.String(10), default="25")
    ratio = db.Column(db.String(10), default="16:9")
    resolution = db.Column(db.String(12), default="1920x1080")

    # Stored as JSON arrays of IDs
    task_type_ids = db.Column(JSONB, default=[])
    asset_type_ids = db.Column(JSONB, default=[])
    task_status_ids = db.Column(JSONB, default=[])

    # Full config snapshot for future extensibility
    data = db.Column(JSONB, default={})

    def present(self):
        return self.serialize()
