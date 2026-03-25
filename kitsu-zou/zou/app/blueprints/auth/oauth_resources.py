"""
OAuth 2.0 & 手机验证码 API 端点

提供企业微信 OAuth、钉钉 OAuth、手机验证码登录的 Flask-RESTful Resource 类。
参照现有 zou/app/blueprints/auth/resources.py 中 SAMLSSOResource 的设计模式。

API 端点:
- GET  /auth/oauth/wecom/login       — 重定向到企业微信授权页
- GET  /auth/oauth/wecom/callback    — 企业微信回调处理
- GET  /auth/oauth/dingtalk/login    — 重定向到钉钉授权页
- GET  /auth/oauth/dingtalk/callback — 钉钉回调处理
- POST /auth/sms/send                — 发送手机验证码
- POST /auth/sms/login               — 手机验证码登录
"""
import logging
import secrets

from flask import request, jsonify, current_app, redirect, make_response
from flask_restful import Resource
from flask_principal import Identity, identity_changed
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    set_access_cookies,
    set_refresh_cookies,
)

from zou.app import config
from zou.app import config_oauth
from zou.app.mixin import ArgsMixin
from zou.app.models.person import Person
from zou.app.utils import auth
from zou.app.utils.flask import is_from_browser
from zou.app.utils.oauth_providers import (
    WeComProvider,
    DingtalkProvider,
    OAuthError,
)
from zou.app.utils.sms import send_sms_code, verify_sms_code
from zou.app.services import (
    persons_service,
    events_service,
)
from zou.app.services.exception import PersonNotFoundException
from zou.app.stores import auth_tokens_store

logger = logging.getLogger(__name__)


# =============================================================================
# 内部辅助函数
# =============================================================================

def _generate_jwt_tokens(user_id):
    """
    为指定用户生成 JWT access_token 和 refresh_token

    参数:
        user_id: 用户 UUID 字符串

    返回:
        (access_token, refresh_token) 元组
    """
    additional_claims = {"identity_type": "person"}
    access_token = create_access_token(
        identity=user_id,
        additional_claims=additional_claims,
    )
    refresh_token = create_refresh_token(
        identity=user_id,
        additional_claims=additional_claims,
    )
    return access_token, refresh_token


def _build_login_response(user, access_token, refresh_token):
    """
    构建登录成功的 JSON 响应（API 模式）

    参照 LoginResource.post() 的响应格式，包含 user、organisation、tokens。

    参数:
        user: 用户字典
        access_token: JWT access token
        refresh_token: JWT refresh token

    返回:
        Flask Response 对象
    """
    organisation = persons_service.get_organisation(
        sensitive=user.get("role") == "admin"
    )

    response_data = {
        "user": user,
        "organisation": organisation,
        "login": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

    response = jsonify(response_data)

    if is_from_browser(request.user_agent):
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)

    return response


def _build_oauth_redirect_response(user, access_token, refresh_token):
    """
    构建 OAuth 登录成功的重定向响应（浏览器模式）

    参照 SAMLSSOResource.post() 的响应格式，设置 cookies 并重定向。

    参数:
        user: 用户字典
        access_token: JWT access token
        refresh_token: JWT refresh token

    返回:
        Flask Response 对象（302 重定向）
    """
    redirect_url = (
        f"{config.DOMAIN_PROTOCOL}://{config.DOMAIN_NAME}"
        f"{config_oauth.OAUTH_SUCCESS_REDIRECT}"
    )
    response = make_response(redirect(redirect_url))

    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)

    return response


def _emit_login_event(user_id, login_source="web"):
    """
    发送登录相关的事件（身份变更 + 登录日志）

    参数:
        user_id: 用户 UUID
        login_source: 登录来源标识（"web" / "oauth" 等）
    """
    identity_changed.send(
        current_app._get_current_object(),
        identity=Identity(user_id, "person"),
    )

    ip_address = request.environ.get(
        "HTTP_X_REAL_IP", request.remote_addr
    )
    events_service.create_login_log(user_id, ip_address, login_source)


def _find_or_create_oauth_user(provider_name, user_info):
    """
    根据 OAuth 用户信息查找或创建本地用户

    查找策略（按优先级）:
    1. 通过 person.data JSON 字段中的 {provider}_id 匹配
    2. 通过邮箱匹配
    3. 通过手机号匹配
    4. 如果都未找到且允许自动注册，创建新用户

    参数:
        provider_name: "wecom" 或 "dingtalk"
        user_info: 标准化用户信息字典

    返回:
        用户字典（persons_service 格式）

    异常:
        OAuthError: 用户不存在且不允许自动注册
    """
    external_id = user_info.get("external_id", "")
    email = user_info.get("email", "")
    phone = user_info.get("phone", "")
    name = user_info.get("name", "")
    oauth_id_field = f"{provider_name}_id"

    # 策略 1: 通过 data JSON 字段中的 OAuth ID 查找
    user = _find_person_by_oauth_id(oauth_id_field, external_id)
    if user:
        logger.info(
            "[%s] 通过 %s 找到用户: %s",
            provider_name,
            oauth_id_field,
            user["id"],
        )
        # 更新用户 data 字段（头像等信息可能变化）
        _update_person_oauth_data(user, provider_name, user_info)
        return user

    # 策略 2: 通过邮箱查找
    if email:
        try:
            user = persons_service.get_person_by_email(email)
            logger.info(
                "[%s] 通过邮箱 %s 找到用户: %s",
                provider_name,
                email,
                user["id"],
            )
            # 关联 OAuth ID 到已有用户
            _update_person_oauth_data(user, provider_name, user_info)
            return user
        except PersonNotFoundException:
            pass

    # 策略 3: 通过手机号查找
    if phone:
        user = _find_person_by_phone(phone)
        if user:
            logger.info(
                "[%s] 通过手机号 %s 找到用户: %s",
                provider_name,
                phone,
                user["id"],
            )
            _update_person_oauth_data(user, provider_name, user_info)
            return user

    # 策略 4: 自动创建新用户
    if not config_oauth.AUTO_REGISTER_ENABLED:
        raise OAuthError(
            f"用户不存在且自动注册已禁用 (provider={provider_name}, "
            f"external_id={external_id})",
            provider=provider_name,
        )

    user = _create_person_from_oauth(provider_name, user_info)
    logger.info(
        "[%s] 自动创建新用户: %s (external_id=%s)",
        provider_name,
        user["id"],
        external_id,
    )
    return user


def _find_person_by_oauth_id(oauth_id_field, external_id):
    """
    通过 person.data JSON 字段中的 OAuth ID 查找用户

    使用 SQLAlchemy JSONB 查询: data->>{field} = {value}

    参数:
        oauth_id_field: data 字段中的 key 名（如 "wecom_id"）
        external_id: OAuth 平台的用户唯一标识

    返回:
        用户字典，未找到返回 None
    """
    if not external_id:
        return None

    try:
        person = Person.query.filter(
            Person.data[oauth_id_field].astext == external_id
        ).first()

        if person:
            return person.serialize_safe()
    except Exception as e:
        logger.warning("JSONB 查询 %s 失败: %s", oauth_id_field, e)

    return None


def _find_person_by_phone(phone):
    """
    通过手机号查找用户

    参数:
        phone: 手机号字符串

    返回:
        用户字典，未找到返回 None
    """
    if not phone:
        return None

    person = Person.get_by(phone=phone)
    if person:
        return person.serialize_safe()
    return None


def _update_person_oauth_data(user, provider_name, user_info):
    """
    更新用户的 data JSON 字段，存储 OAuth 关联信息

    将 OAuth 平台的 external_id 和头像 URL 存入 person.data，
    用于后续快速匹配。

    参数:
        user: 用户字典
        provider_name: "wecom" 或 "dingtalk"
        user_info: 标准化用户信息字典
    """
    try:
        person = Person.get(user["id"])
        if person is None:
            return

        data = person.data or {}
        data[f"{provider_name}_id"] = user_info.get("external_id", "")
        data[f"{provider_name}_avatar"] = user_info.get("avatar_url", "")

        person.update({"data": data})
        logger.debug(
            "已更新用户 %s 的 OAuth 数据: %s_id=%s",
            user["id"],
            provider_name,
            user_info.get("external_id"),
        )
    except Exception as e:
        # 更新失败不影响登录流程
        logger.warning("更新用户 OAuth 数据失败: %s", e)


def _create_person_from_oauth(provider_name, user_info):
    """
    从 OAuth 用户信息创建新的本地用户

    参数:
        provider_name: "wecom" 或 "dingtalk"
        user_info: 标准化用户信息字典

    返回:
        新创建的用户字典
    """
    name = user_info.get("name", "")
    email = user_info.get("email", "")
    phone = user_info.get("phone", "")

    # 拆分姓名（中文名: 第一个字为姓，后面为名）
    if name:
        first_name = name[1:] if len(name) > 1 else name
        last_name = name[0] if len(name) > 0 else ""
    else:
        first_name = provider_name
        last_name = "User"

    # 如果没有邮箱，生成占位邮箱（Kitsu 需要唯一邮箱）
    if not email:
        external_id = user_info.get("external_id", "unknown")
        email = f"{provider_name}_{external_id}@oauth.local"

    # 生成随机密码（OAuth 用户不使用密码登录）
    random_password = auth.encrypt_password(secrets.token_urlsafe(64))

    user = persons_service.create_person(
        email=email,
        password=random_password,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )

    # 将 OAuth ID 写入 data 字段
    _update_person_oauth_data(user, provider_name, user_info)

    return user


def _generate_oauth_state():
    """
    生成 OAuth state 参数（CSRF 防护）

    生成随机字符串并存入 Redis（5 分钟过期），
    回调时验证 state 有效性。

    返回:
        state 字符串
    """
    state = secrets.token_urlsafe(32)
    auth_tokens_store.add(
        f"oauth_state:{state}",
        "valid",
        ttl=300,
    )
    return state


def _verify_oauth_state(state):
    """
    验证 OAuth state 参数（CSRF 防护）

    参数:
        state: 回调携带的 state 字符串

    返回:
        True: 有效
        False: 无效或已过期
    """
    if not state:
        return False

    key = f"oauth_state:{state}"
    result = auth_tokens_store.get(key)
    if result:
        auth_tokens_store.delete(key)
        return True
    return False


# =============================================================================
# 企业微信 OAuth 资源
# =============================================================================

class WeComLoginResource(Resource):
    """企业微信 OAuth 登录 — 生成授权URL并重定向"""

    def get(self):
        """
        企业微信 OAuth 登录入口
        ---
        description: 生成企业微信 OAuth 授权URL，重定向用户到企业微信授权页面。
        tags:
            - Authentication
            - OAuth
        responses:
          302:
            description: 重定向到企业微信授权页面
          400:
            description: 企业微信 OAuth 未启用
        """
        if not config_oauth.WECOM_ENABLED:
            return {"error": True, "message": "企业微信 OAuth 未启用"}, 400

        provider = WeComProvider()
        redirect_uri = (
            config_oauth.WECOM_REDIRECT_URI
            or f"{config.DOMAIN_PROTOCOL}://{config.DOMAIN_NAME}"
            f"/api/auth/oauth/wecom/callback"
        )
        state = _generate_oauth_state()

        authorize_url = provider.get_authorize_url(redirect_uri, state)
        return redirect(authorize_url, code=302)


class WeComCallbackResource(Resource):
    """企业微信 OAuth 回调 — 处理授权码，创建/更新用户，返回 JWT"""

    def get(self):
        """
        企业微信 OAuth 回调处理
        ---
        description: 接收企业微信授权回调，用授权码获取用户信息，
          创建或更新用户账号，生成 JWT token 并设置 cookies。
        tags:
            - Authentication
            - OAuth
        parameters:
          - name: code
            in: query
            type: string
            required: true
            description: 企业微信授权码
          - name: state
            in: query
            type: string
            required: true
            description: CSRF 防护参数
        responses:
          302:
            description: 登录成功，重定向到前端主页
          400:
            description: 参数错误或认证失败
        """
        code = request.args.get("code")
        state = request.args.get("state")

        # 参数校验
        if not code:
            return {"error": True, "message": "缺少授权码 (code)"}, 400

        if not _verify_oauth_state(state):
            return {"error": True, "message": "无效的 state 参数"}, 400

        try:
            provider = WeComProvider()
            redirect_uri = (
                config_oauth.WECOM_REDIRECT_URI
                or f"{config.DOMAIN_PROTOCOL}://{config.DOMAIN_NAME}"
                f"/api/auth/oauth/wecom/callback"
            )

            # 用 code 换取用户身份
            token_data = provider.get_access_token(code, redirect_uri)

            # 获取用户详细信息
            user_info = provider.get_user_info(token_data)

            # 查找或创建用户
            user = _find_or_create_oauth_user("wecom", user_info)

            if not user.get("active", True):
                return {
                    "error": True,
                    "login": False,
                    "message": "用户已被禁用，无法登录。",
                }, 401

            # 生成 JWT
            access_token, refresh_token = _generate_jwt_tokens(user["id"])
            _emit_login_event(user["id"], "wecom_oauth")

            current_app.logger.info(
                "用户 %s 通过企业微信 OAuth 登录成功。", user.get("email")
            )

            return _build_oauth_redirect_response(
                user, access_token, refresh_token
            )

        except OAuthError as e:
            current_app.logger.error("企业微信 OAuth 失败: %s", e.message)
            return {"error": True, "message": e.message}, 400
        except Exception as e:
            current_app.logger.error("企业微信 OAuth 异常: %s", e, exc_info=1)
            return {
                "error": True,
                "message": "OAuth 认证过程发生服务器错误",
            }, 500


# =============================================================================
# 钉钉 OAuth 资源
# =============================================================================

class DingtalkLoginResource(Resource):
    """钉钉 OAuth 登录 — 生成授权URL并重定向"""

    def get(self):
        """
        钉钉 OAuth 登录入口
        ---
        description: 生成钉钉 OAuth 授权URL，重定向用户到钉钉授权页面。
        tags:
            - Authentication
            - OAuth
        responses:
          302:
            description: 重定向到钉钉授权页面
          400:
            description: 钉钉 OAuth 未启用
        """
        if not config_oauth.DINGTALK_ENABLED:
            return {"error": True, "message": "钉钉 OAuth 未启用"}, 400

        provider = DingtalkProvider()
        redirect_uri = (
            config_oauth.DINGTALK_REDIRECT_URI
            or f"{config.DOMAIN_PROTOCOL}://{config.DOMAIN_NAME}"
            f"/api/auth/oauth/dingtalk/callback"
        )
        state = _generate_oauth_state()

        authorize_url = provider.get_authorize_url(redirect_uri, state)
        return redirect(authorize_url, code=302)


class DingtalkCallbackResource(Resource):
    """钉钉 OAuth 回调 — 处理授权码，创建/更新用户，返回 JWT"""

    def get(self):
        """
        钉钉 OAuth 回调处理
        ---
        description: 接收钉钉授权回调，用授权码获取用户信息，
          创建或更新用户账号，生成 JWT token 并设置 cookies。
        tags:
            - Authentication
            - OAuth
        parameters:
          - name: authCode
            in: query
            type: string
            required: true
            description: 钉钉授权码
          - name: state
            in: query
            type: string
            required: true
            description: CSRF 防护参数
        responses:
          302:
            description: 登录成功，重定向到前端主页
          400:
            description: 参数错误或认证失败
        """
        # 钉钉回调参数名为 authCode
        code = request.args.get("authCode") or request.args.get("code")
        state = request.args.get("state")

        if not code:
            return {"error": True, "message": "缺少授权码 (authCode)"}, 400

        if not _verify_oauth_state(state):
            return {"error": True, "message": "无效的 state 参数"}, 400

        try:
            provider = DingtalkProvider()
            redirect_uri = (
                config_oauth.DINGTALK_REDIRECT_URI
                or f"{config.DOMAIN_PROTOCOL}://{config.DOMAIN_NAME}"
                f"/api/auth/oauth/dingtalk/callback"
            )

            # 用 code 换取 user access_token
            access_token = provider.get_access_token(code, redirect_uri)

            # 获取用户信息
            user_info = provider.get_user_info(access_token)

            # 查找或创建用户
            user = _find_or_create_oauth_user("dingtalk", user_info)

            if not user.get("active", True):
                return {
                    "error": True,
                    "login": False,
                    "message": "用户已被禁用，无法登录。",
                }, 401

            # 生成 JWT
            access_token, refresh_token = _generate_jwt_tokens(user["id"])
            _emit_login_event(user["id"], "dingtalk_oauth")

            current_app.logger.info(
                "用户 %s 通过钉钉 OAuth 登录成功。", user.get("email")
            )

            return _build_oauth_redirect_response(
                user, access_token, refresh_token
            )

        except OAuthError as e:
            current_app.logger.error("钉钉 OAuth 失败: %s", e.message)
            return {"error": True, "message": e.message}, 400
        except Exception as e:
            current_app.logger.error("钉钉 OAuth 异常: %s", e, exc_info=1)
            return {
                "error": True,
                "message": "OAuth 认证过程发生服务器错误",
            }, 500


# =============================================================================
# 手机验证码资源
# =============================================================================

class SMSSendResource(Resource, ArgsMixin):
    """发送手机验证码"""

    def post(self):
        """
        发送手机验证码
        ---
        description: 向指定手机号发送 6 位数字验证码，60 秒内不可重复发送。
        tags:
            - Authentication
            - SMS
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  phone:
                    type: string
                    example: "13800138000"
                    description: 手机号码
                required:
                  - phone
        responses:
          200:
            description: 验证码发送成功
          400:
            description: 参数错误或冷却期内
          500:
            description: 短信发送失败
        """
        if not config_oauth.SMS_ENABLED and config_oauth.SMS_SECRET_ID:
            return {"error": True, "message": "短信服务未启用"}, 400

        args = self.get_args(
            [
                {
                    "name": "phone",
                    "required": True,
                    "help": "手机号不能为空",
                },
            ]
        )
        phone = args["phone"]

        if not phone or len(phone.strip()) < 5:
            return {"error": True, "message": "无效的手机号"}, 400

        success = send_sms_code(phone.strip())

        if success:
            return {"success": True, "message": "验证码已发送"}
        else:
            return {
                "error": True,
                "message": "验证码发送失败，请稍后重试（60 秒内不可重复发送）",
            }, 400


class SMSLoginResource(Resource, ArgsMixin):
    """手机验证码登录"""

    def post(self):
        """
        手机验证码登录
        ---
        description: 使用手机号和验证码登录。验证码通过后，查找或创建用户，
          生成 JWT token。
        tags:
            - Authentication
            - SMS
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                properties:
                  phone:
                    type: string
                    example: "13800138000"
                    description: 手机号码
                  code:
                    type: string
                    example: "123456"
                    description: 6 位验证码
                required:
                  - phone
                  - code
        responses:
          200:
            description: 登录成功
          400:
            description: 验证码错误或已过期
          401:
            description: 用户被禁用
        """
        args = self.get_args(
            [
                {
                    "name": "phone",
                    "required": True,
                    "help": "手机号不能为空",
                },
                {
                    "name": "code",
                    "required": True,
                    "help": "验证码不能为空",
                },
            ]
        )
        phone = args["phone"]
        code = args["code"]

        # 验证验证码
        if not verify_sms_code(phone, code):
            return {
                "error": True,
                "login": False,
                "message": "验证码错误或已过期",
            }, 400

        try:
            # 通过手机号查找用户
            user = _find_person_by_phone(phone)

            if user is None:
                # 自动注册
                if not config_oauth.AUTO_REGISTER_ENABLED:
                    return {
                        "error": True,
                        "login": False,
                        "message": "用户不存在且自动注册已禁用",
                    }, 400

                # 创建新用户
                random_password = auth.encrypt_password(
                    secrets.token_urlsafe(64)
                )
                user = persons_service.create_person(
                    email=f"phone_{phone}@sms.local",
                    password=random_password,
                    first_name=phone[-4:],  # 用手机号后4位作为名字占位
                    last_name="用户",
                    phone=phone,
                )
                current_app.logger.info(
                    "通过手机验证码自动创建新用户: phone=%s, id=%s",
                    phone,
                    user["id"],
                )

            if not user.get("active", True):
                return {
                    "error": True,
                    "login": False,
                    "message": "用户已被禁用，无法登录。",
                }, 401

            # 生成 JWT
            access_token, refresh_token = _generate_jwt_tokens(user["id"])
            _emit_login_event(user["id"], "sms")

            current_app.logger.info(
                "用户 %s 通过手机验证码登录成功。", phone
            )

            return _build_login_response(user, access_token, refresh_token)

        except Exception as e:
            current_app.logger.error("手机验证码登录异常: %s", e, exc_info=1)
            return {
                "error": True,
                "login": False,
                "message": "登录过程发生服务器错误",
            }, 500
