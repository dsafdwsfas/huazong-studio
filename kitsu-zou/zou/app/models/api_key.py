"""
API Key 模型

外部开放 API 的密钥管理。密钥以 SHA256 哈希存储，明文只在创建时返回一次。
"""

from sqlalchemy_utils import UUIDType
from sqlalchemy.dialects.postgresql import JSONB

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class ApiKey(db.Model, BaseMixin, SerializerMixin):
    """
    外部 API 密钥。

    用于第三方应用（如 Blender 插件、DCC 工具）通过开放 API 访问资产库。
    密钥以 SHA256 哈希存储，不保存明文。
    """

    __tablename__ = "api_key"

    name = db.Column(db.String(100), nullable=False)
    key_prefix = db.Column(db.String(16), nullable=False)
    key_hash = db.Column(db.String(256), nullable=False, unique=True)

    owner_id = db.Column(
        UUIDType(binary=False),
        db.ForeignKey("person.id"),
        nullable=False,
        index=True,
    )

    # 权限范围
    scopes = db.Column(
        JSONB,
        default=["assets:read"],
        server_default='["assets:read"]',
    )

    # 限制
    rate_limit = db.Column(db.Integer, default=100, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)

    # 使用统计
    last_used_at = db.Column(db.DateTime, nullable=True)
    total_requests = db.Column(db.Integer, default=0, nullable=False)

    owner = db.relationship("Person")

    def serialize(self, **kwargs):
        """序列化时排除 key_hash，避免泄露。"""
        result = super().serialize(**kwargs)
        result.pop("key_hash", None)
        return result
