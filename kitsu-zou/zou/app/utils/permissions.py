from functools import wraps
from flask_principal import RoleNeed, Permission
from werkzeug.exceptions import Forbidden

admin_permission = Permission(RoleNeed("admin"))
manager_permission = Permission(RoleNeed("manager"))
supervisor_permission = Permission(RoleNeed("supervisor"))
client_permission = Permission(RoleNeed("client"))
vendor_permission = Permission(RoleNeed("vendor"))
artist_permission = Permission(RoleNeed("user"))

bot_permission = Permission(RoleNeed("bot"))
person_permission = Permission(RoleNeed("person"), RoleNeed("person_api"))
person_api_permission = Permission(RoleNeed("person_api"))


class PermissionDenied(Forbidden):
    pass


def has_manager_permissions():
    """
    Return True if user is an admin or a manager.
    """
    return admin_permission.can() or manager_permission.can()


def has_artist_permissions():
    """
    Return True if user is an artist.
    """
    return artist_permission.can()


def has_admin_permissions():
    """
    Return True if user is an admin.
    """
    return admin_permission.can()


def has_client_permissions():
    """
    Return True if user is a client.
    """
    return client_permission.can()


def has_vendor_permissions():
    """
    Return True if user is a vendor.
    """
    return vendor_permission.can()


def has_supervisor_permissions():
    """
    Return True if user is a supervisor.
    """
    return supervisor_permission.can()


def has_person_permissions():
    """
    Return True if user is a person.
    """
    return person_permission.can()


def has_at_least_supervisor_permissions():
    """
    Return True if user is an admin or a manager.
    """
    return (
        supervisor_permission.can()
        or admin_permission.can()
        or manager_permission.can()
    )


def check_at_least_supervisor_permissions():
    """
    Return True if user is admin, manager or supervisor. It raises a
    PermissionDenied exception in case of failure.
    """
    if has_at_least_supervisor_permissions():
        return True
    else:
        raise PermissionDenied


def check_manager_permissions():
    """
    Return True if user is admin or manager. It raises a PermissionDenied
    exception in case of failure.
    """
    if has_manager_permissions():
        return True
    else:
        raise PermissionDenied


def check_admin_permissions():
    """
    Return True if user is admin. It raises a PermissionDenied exception in case
    of failure.
    """
    if admin_permission.can():
        return True
    else:
        raise PermissionDenied


def check_person_permissions():
    """
    Return True if user is a person. It raises a PermissionDenied exception in
    case of failure.
    """
    if person_permission.can():
        return True
    else:
        raise PermissionDenied


def require_admin(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        check_admin_permissions()
        return function(*args, **kwargs)

    return decorated_function


def require_manager(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        check_manager_permissions()
        return function(*args, **kwargs)

    return decorated_function


def require_person(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        check_person_permissions()
        return function(*args, **kwargs)

    return decorated_function


# ------------------------------------------------------------------
# 项目角色权限（三级权限体系）
# ------------------------------------------------------------------


def get_project_role(project_id, person_id):
    """
    获取用户在指定项目中的角色。

    Returns:
        str | None: 项目角色（director/producer/artist/observer），
                    None 表示不是项目成员。
    """
    from zou.app.models.project import ProjectPersonLink
    link = ProjectPersonLink.query.filter_by(
        project_id=project_id,
        person_id=person_id,
    ).first()
    if not link:
        return None
    # 兼容旧数据：project_role 为空时默认 artist
    role = link.project_role
    if hasattr(role, 'value'):
        return role.value
    return role or "artist"


def has_project_role(project_id, person_id, required_roles):
    """
    检查用户在项目中的角色是否满足要求。
    全局 admin 始终通过。

    Args:
        project_id: 项目 ID
        person_id: 用户 ID
        required_roles: 允许的角色列表，如 ["director", "producer"]

    Returns:
        bool
    """
    if has_admin_permissions():
        return True
    role = get_project_role(project_id, person_id)
    return role is not None and role in required_roles


def check_project_role(project_id, person_id, required_roles):
    """
    断言型项目角色检查，不满足时抛出 PermissionDenied。
    """
    if not has_project_role(project_id, person_id, required_roles):
        raise PermissionDenied


def can_view_entity(entity_id, project_id, person_id):
    """
    检查用户是否可以查看指定实体。

    逻辑：
    1. 全局 admin → True
    2. 非项目成员 → False
    3. 查询 EntityAccessControl 表
    4. 无特殊配置 → 默认可查看
    5. 有配置 → 按 can_view 字段
    """
    if has_admin_permissions():
        return True

    role = get_project_role(project_id, person_id)
    if role is None:
        return False

    from zou.app.models.project import EntityAccessControl
    acl = EntityAccessControl.query.filter_by(
        entity_id=entity_id,
        project_id=project_id,
        project_role=role,
    ).first()

    if not acl:
        return True  # 无特殊配置，默认可查看

    return acl.can_view


def can_edit_entity(entity_id, project_id, person_id):
    """
    检查用户是否可以编辑指定实体。

    逻辑：
    1. 全局 admin → True
    2. 非项目成员 → False
    3. observer 角色 → False（默认不可编辑）
    4. 查询 EntityAccessControl 表
    5. 无特殊配置 → director/producer 可编辑，artist 可编辑
    6. 有配置 → 按 can_edit 字段
    """
    if has_admin_permissions():
        return True

    role = get_project_role(project_id, person_id)
    if role is None:
        return False

    from zou.app.models.project import EntityAccessControl
    acl = EntityAccessControl.query.filter_by(
        entity_id=entity_id,
        project_id=project_id,
        project_role=role,
    ).first()

    if not acl:
        # 默认规则：observer 不可编辑，其他角色可编辑
        return role != "observer"

    return acl.can_edit


def require_project_role(*required_roles):
    """
    API 路由装饰器：要求当前用户在项目中拥有指定角色。

    project_id 从 kwargs 中获取（Flask-RESTX resource 的 URL 参数）。

    用法::

        @require_project_role("director", "producer")
        def put(self, project_id):
            ...
    """
    def decorator(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            project_id = kwargs.get("project_id")
            if not project_id:
                raise PermissionDenied
            from zou.app.services import persons_service
            current_user = persons_service.get_current_user()
            check_project_role(
                project_id, current_user["id"], list(required_roles)
            )
            return function(*args, **kwargs)
        return decorated_function
    return decorator
