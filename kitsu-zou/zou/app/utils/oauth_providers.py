"""
OAuth 2.0 Provider 接口 — 企业微信 & 钉钉

参照 zou/app/utils/saml.py 的设计模式，提供 OAuth 2.0 认证的 Provider 抽象层。
每个 Provider 实现授权URL生成、令牌交换、用户信息获取三个核心步骤。

返回标准化用户信息格式:
{
    "external_id": "...",    # 外部平台唯一标识
    "name": "...",           # 显示名称
    "email": "...",          # 邮箱（可能为空）
    "phone": "...",          # 手机号（可能为空）
    "avatar_url": "...",     # 头像URL
    "departments": [...]     # 部门列表
}
"""
import logging
import urllib.parse

import requests

from zou.app import config_oauth

logger = logging.getLogger(__name__)


class OAuthError(Exception):
    """OAuth 认证过程中的错误"""

    def __init__(self, message, provider=None, detail=None):
        self.message = message
        self.provider = provider
        self.detail = detail
        super().__init__(self.message)


class OAuthProvider:
    """OAuth 2.0 Provider 基类 — 定义标准接口"""

    # 子类必须设置
    PROVIDER_NAME = "base"

    def get_authorize_url(self, redirect_uri, state):
        """
        生成第三方平台的授权URL，用户将被重定向到此URL进行授权。

        参数:
            redirect_uri: 授权完成后的回调地址
            state: CSRF 防护随机字符串

        返回:
            授权URL字符串
        """
        raise NotImplementedError

    def get_access_token(self, code, redirect_uri):
        """
        使用授权码(code)换取访问令牌(access_token)。

        参数:
            code: 用户授权后回调携带的授权码
            redirect_uri: 原始回调地址（部分平台校验需要）

        返回:
            access_token 字符串或令牌字典
        """
        raise NotImplementedError

    def get_user_info(self, access_token):
        """
        使用访问令牌获取用户信息。

        参数:
            access_token: 访问令牌

        返回:
            标准化用户信息字典
        """
        raise NotImplementedError

    def _request(self, method, url, **kwargs):
        """
        统一 HTTP 请求封装 — 包含超时、错误处理、日志

        参数:
            method: HTTP 方法（"GET" / "POST"）
            url: 请求URL
            **kwargs: 传递给 requests 的其他参数

        返回:
            响应JSON字典

        异常:
            OAuthError: 请求失败或响应异常
        """
        kwargs.setdefault("timeout", 10)
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            data = response.json()
            logger.debug(
                "[%s] 请求 %s 响应: %s", self.PROVIDER_NAME, url, data
            )
            return data
        except requests.exceptions.Timeout:
            raise OAuthError(
                f"{self.PROVIDER_NAME} 请求超时",
                provider=self.PROVIDER_NAME,
                detail=f"URL: {url}",
            )
        except requests.exceptions.RequestException as e:
            raise OAuthError(
                f"{self.PROVIDER_NAME} 请求失败: {e}",
                provider=self.PROVIDER_NAME,
                detail=str(e),
            )
        except ValueError:
            raise OAuthError(
                f"{self.PROVIDER_NAME} 响应解析失败",
                provider=self.PROVIDER_NAME,
                detail=f"URL: {url}",
            )


class WeComProvider(OAuthProvider):
    """
    企业微信 OAuth 2.0 Provider

    认证流程（三步）:
    1. 引导用户访问企业微信授权页面，用户扫码/确认授权
    2. 回调获取 code → 用 corp_id + secret 获取 corp access_token
    3. 用 code + access_token 获取 userid → 再获取用户详细信息

    API 文档:
    - 授权URL: https://developer.work.weixin.qq.com/document/path/91022
    - 获取 access_token: https://developer.work.weixin.qq.com/document/path/91039
    - 获取用户信息(code): https://developer.work.weixin.qq.com/document/path/91023
    - 获取用户详情(userid): https://developer.work.weixin.qq.com/document/path/90196
    """

    PROVIDER_NAME = "wecom"

    # 企业微信 API 端点
    AUTHORIZE_URL = "https://open.weixin.qq.com/connect/oauth2/authorize"
    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    USER_INFO_URL = "https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo"
    USER_DETAIL_URL = "https://qyapi.weixin.qq.com/cgi-bin/user/get"

    def __init__(self):
        self.corp_id = config_oauth.WECOM_CORP_ID
        self.agent_id = config_oauth.WECOM_AGENT_ID
        self.secret = config_oauth.WECOM_SECRET

    def get_authorize_url(self, redirect_uri, state):
        """
        生成企业微信 OAuth 授权URL

        使用企业微信网页授权方式，scope=snsapi_privateinfo 获取用户详细信息。
        """
        params = {
            "appid": self.corp_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "snsapi_privateinfo",
            "state": state,
            "agentid": self.agent_id,
        }
        return (
            f"{self.AUTHORIZE_URL}?"
            f"{urllib.parse.urlencode(params)}"
            f"#wechat_redirect"
        )

    def _get_corp_access_token(self):
        """
        获取企业微信的 corp access_token

        此 token 用于后续调用企业微信 API（非用户级别）。
        生产环境应缓存此 token（有效期 7200 秒），此处简化为每次请求。
        """
        data = self._request(
            "GET",
            self.TOKEN_URL,
            params={
                "corpid": self.corp_id,
                "corpsecret": self.secret,
            },
        )

        if data.get("errcode", 0) != 0:
            raise OAuthError(
                f"获取企业微信 access_token 失败: {data.get('errmsg', '未知错误')}",
                provider=self.PROVIDER_NAME,
                detail=data,
            )

        return data["access_token"]

    def get_access_token(self, code, redirect_uri=None):
        """
        使用授权码获取用户身份信息

        企业微信的流程是: code → userid（通过 corp access_token）。
        返回包含 corp_access_token 和 userid 的字典。
        """
        corp_token = self._get_corp_access_token()

        # 用 code 获取用户身份（userid）
        data = self._request(
            "GET",
            self.USER_INFO_URL,
            params={
                "access_token": corp_token,
                "code": code,
            },
        )

        if data.get("errcode", 0) != 0:
            raise OAuthError(
                f"企业微信获取用户身份失败: {data.get('errmsg', '未知错误')}",
                provider=self.PROVIDER_NAME,
                detail=data,
            )

        userid = data.get("userid") or data.get("UserId")
        if not userid:
            raise OAuthError(
                "企业微信返回的用户身份中无 userid",
                provider=self.PROVIDER_NAME,
                detail=data,
            )

        return {"corp_access_token": corp_token, "userid": userid}

    def get_user_info(self, access_token):
        """
        获取企业微信用户详细信息

        参数:
            access_token: get_access_token 返回的字典
                         {"corp_access_token": "...", "userid": "..."}

        返回:
            标准化用户信息字典
        """
        if isinstance(access_token, dict):
            corp_token = access_token["corp_access_token"]
            userid = access_token["userid"]
        else:
            raise OAuthError(
                "access_token 参数格式错误，应为字典",
                provider=self.PROVIDER_NAME,
            )

        # 获取用户详细信息
        data = self._request(
            "GET",
            self.USER_DETAIL_URL,
            params={
                "access_token": corp_token,
                "userid": userid,
            },
        )

        if data.get("errcode", 0) != 0:
            raise OAuthError(
                f"获取企业微信用户详情失败: {data.get('errmsg', '未知错误')}",
                provider=self.PROVIDER_NAME,
                detail=data,
            )

        # 标准化用户信息
        return {
            "external_id": userid,
            "name": data.get("name", ""),
            "email": data.get("biz_mail", "") or data.get("email", ""),
            "phone": data.get("mobile", ""),
            "avatar_url": data.get("thumb_avatar", "")
            or data.get("avatar", ""),
            "departments": data.get("department", []),
        }


class DingtalkProvider(OAuthProvider):
    """
    钉钉 OAuth 2.0 Provider

    认证流程（两步）:
    1. 引导用户访问钉钉授权页面，用户扫码/确认授权
    2. 回调获取 code → 直接用 code 换取 user access_token → 获取用户信息

    API 文档:
    - 授权URL: https://open.dingtalk.com/document/orgapp/obtain-identity-credentials
    - 获取 user access_token: https://open.dingtalk.com/document/orgapp/obtain-user-token
    - 获取用户信息: https://open.dingtalk.com/document/orgapp/dingtalk-retrieve-user-information
    """

    PROVIDER_NAME = "dingtalk"

    # 钉钉 API 端点
    AUTHORIZE_URL = "https://login.dingtalk.com/oauth2/auth"
    TOKEN_URL = "https://api.dingtalk.com/v1.0/oauth2/userAccessToken"
    USER_INFO_URL = "https://api.dingtalk.com/v1.0/contact/users/me"

    def __init__(self):
        self.app_key = config_oauth.DINGTALK_APP_KEY
        self.app_secret = config_oauth.DINGTALK_APP_SECRET

    def get_authorize_url(self, redirect_uri, state):
        """
        生成钉钉 OAuth 2.0 授权URL

        使用钉钉统一登录协议，scope=openid 获取用户基本信息。
        """
        params = {
            "client_id": self.app_key,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid corpid",
            "state": state,
            "prompt": "consent",
        }
        return f"{self.AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    def get_access_token(self, code, redirect_uri=None):
        """
        使用授权码换取钉钉 user access_token

        钉钉直接用 code + app_key + app_secret 换取用户级别的 access_token。
        """
        data = self._request(
            "POST",
            self.TOKEN_URL,
            json={
                "clientId": self.app_key,
                "clientSecret": self.app_secret,
                "code": code,
                "grantType": "authorization_code",
            },
        )

        token = data.get("accessToken")
        if not token:
            raise OAuthError(
                f"钉钉获取 access_token 失败: {data.get('message', '未知错误')}",
                provider=self.PROVIDER_NAME,
                detail=data,
            )

        return token

    def get_user_info(self, access_token):
        """
        使用 user access_token 获取钉钉用户信息

        参数:
            access_token: 用户级别的 access_token 字符串

        返回:
            标准化用户信息字典
        """
        data = self._request(
            "GET",
            self.USER_INFO_URL,
            headers={"x-acs-dingtalk-access-token": access_token},
        )

        # 钉钉 unionId 作为 external_id（跨应用唯一）
        external_id = data.get("unionId") or data.get("openId", "")

        if not external_id:
            raise OAuthError(
                "钉钉返回的用户信息中无 unionId/openId",
                provider=self.PROVIDER_NAME,
                detail=data,
            )

        # 标准化用户信息
        return {
            "external_id": external_id,
            "name": data.get("nick", ""),
            "email": data.get("email", ""),
            "phone": data.get("mobile", ""),
            "avatar_url": data.get("avatarUrl", ""),
            "departments": [],  # 钉钉用户基本信息接口不返回部门
        }


def get_provider(provider_name):
    """
    工厂方法 — 根据名称获取 OAuth Provider 实例

    参数:
        provider_name: "wecom" 或 "dingtalk"

    返回:
        对应的 OAuthProvider 实例

    异常:
        OAuthError: 未知的 provider 名称
    """
    providers = {
        "wecom": WeComProvider,
        "dingtalk": DingtalkProvider,
    }

    provider_class = providers.get(provider_name)
    if not provider_class:
        raise OAuthError(
            f"未知的 OAuth Provider: {provider_name}",
            provider=provider_name,
        )

    return provider_class()
